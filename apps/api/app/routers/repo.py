import os
import uuid

import git
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from .. import models
from ..core.dependencies import get_current_user
from ..db.session import get_db
from ..models.repositories import Repository
from ..models.tutorials import Tutorial
from ..utils.repo_utils import build_file_tree, get_repo_path

router = APIRouter()


# --- Pydantic Models ---
class RepoCreate(BaseModel):
    github_url: HttpUrl


class RepoResponse(BaseModel):
    repo_id: uuid.UUID
    github_url: str
    name: str | None = None
    description: str | None = None
    status: str
    created_at: str
    updated_at: str


class RepoListResponse(BaseModel):
    repositories: list[RepoResponse]


class TutorialBrief(BaseModel):
    tutorial_id: uuid.UUID
    level: str
    title: str


class RepoDetailResponse(BaseModel):
    repository: RepoResponse
    tutorials: list[TutorialBrief]


class FileTreeNodeResponse(BaseModel):
    name: str
    path: str
    type: str
    children: list["FileTreeNodeResponse"] | None = None

    class Config:
        from_attributes = True


class RepoFileTreeResponse(BaseModel):
    tree: list[FileTreeNodeResponse]


class RepoFileContentResponse(BaseModel):
    content: str
    path: str
    size: int


# --- API Endpoints ---
@router.post("/", response_model=RepoResponse)
async def submit_repository(
    repo_data: RepoCreate,
    request: Request,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing_repo = (
        db.query(Repository).filter(Repository.github_url == str(repo_data.github_url)).first()
    )
    if existing_repo:
        return {
            "repo_id": existing_repo.repo_id,
            "github_url": existing_repo.github_url,
            "name": existing_repo.name,
            "description": existing_repo.description,
            "status": existing_repo.status,
            "created_at": existing_repo.created_at.isoformat(),
            "updated_at": existing_repo.updated_at.isoformat(),
        }

    repo_name = str(repo_data.github_url).split("/")[-1].replace(".git", "")
    new_repo = Repository(
        github_url=str(repo_data.github_url),
        name=repo_name,
        status="PENDING",
        user_id=current_user.user_id,
    )
    db.add(new_repo)
    db.commit()
    db.refresh(new_repo)

    # Analysis is now triggered by Tutorial Generation, so we don't auto-enqueue here.
    # We could enqueue a simple "clone" job if we wanted, but TutorialOrchestrator handles cloning.

    return {
        "repo_id": new_repo.repo_id,
        "github_url": new_repo.github_url,
        "name": new_repo.name,
        "description": new_repo.description,
        "status": new_repo.status,
        "created_at": new_repo.created_at.isoformat(),
        "updated_at": new_repo.updated_at.isoformat(),
    }


@router.get("/", response_model=RepoListResponse)
async def get_user_repositories(
    current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
):
    repos = db.query(Repository).filter(Repository.user_id == current_user.user_id).all()

    return {
        "repositories": [
            {
                "repo_id": repo.repo_id,
                "github_url": repo.github_url,
                "name": repo.name,
                "description": repo.description,
                "status": repo.status,
                "created_at": repo.created_at.isoformat(),
                "updated_at": repo.updated_at.isoformat(),
            }
            for repo in repos
        ]
    }


@router.get("/{repo_id}/tree", response_model=RepoFileTreeResponse)
async def get_repository_file_tree(
    repo_id: uuid.UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = db.query(Repository).filter(Repository.repo_id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail=f"Repository with ID {repo_id} not found")

    if repo.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this repository")

    # Use utils
    repo_path = get_repo_path(repo_id)

    # If not exists, try to clone? Or fail?
    if not os.path.exists(repo_path):
        try:
            os.makedirs("/tmp/reploai", exist_ok=True)
            git.Repo.clone_from(repo.github_url, repo_path)
        except Exception as e:
            # If cloning fails here, it might mean repo is private or invalid
            raise HTTPException(
                status_code=404, detail=f"Repository files not found and cloning failed: {str(e)}"
            )

    tree = build_file_tree(repo_path)
    return RepoFileTreeResponse(tree=tree)


@router.get("/{repo_id}/file")
async def get_repository_file_content(
    repo_id: uuid.UUID,
    file_path: str = Query(..., description="Path to the file relative to repository root"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = db.query(Repository).filter(Repository.repo_id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    if repo.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this repository")

    repo_path = get_repo_path(repo_id)
    full_path = os.path.join(repo_path, file_path)
    full_path = os.path.normpath(full_path)

    if not full_path.startswith(os.path.normpath(repo_path)):
        raise HTTPException(status_code=400, detail="Invalid file path")

    if not os.path.exists(full_path):
        if not os.path.exists(repo_path):
            try:
                os.makedirs("/tmp/reploai", exist_ok=True)
                git.Repo.clone_from(repo.github_url, repo_path)
                if not os.path.exists(full_path):
                    raise HTTPException(status_code=404, detail="File not found after cloning")
            except Exception:
                raise HTTPException(status_code=404, detail="Repository or file not found")
        else:
            raise HTTPException(status_code=404, detail="File not found")

    file_size = os.path.getsize(full_path)
    if file_size > 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 1MB)")

    try:
        with open(full_path, encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return RepoFileContentResponse(content=content, path=file_path, size=file_size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


@router.get("/{repo_id}", response_model=RepoDetailResponse)
async def get_repository_details(
    repo_id: uuid.UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = db.query(Repository).filter(Repository.repo_id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    if repo.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this repository")

    tutorials = db.query(Tutorial).filter(Tutorial.repo_id == repo_id).all()

    return {
        "repository": {
            "repo_id": repo.repo_id,
            "github_url": repo.github_url,
            "name": repo.name,
            "description": repo.description,
            "status": repo.status,
            "created_at": repo.created_at.isoformat(),
            "updated_at": repo.updated_at.isoformat(),
        },
        "tutorials": [
            {"tutorial_id": tutorial.tutorial_id, "level": tutorial.level, "title": tutorial.title}
            for tutorial in tutorials
        ],
    }
