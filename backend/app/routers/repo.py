import os
import uuid
from typing import Any, Dict, List, Optional
import git
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from .. import models
from ..core.dependencies import get_current_user
from ..db.session import get_db
from ..models.repositories import Repository
from ..models.tutorials import Tutorial

router = APIRouter()

# --- Pydantic Models ---
class RepoCreate(BaseModel):
    github_url: HttpUrl

class RepoResponse(BaseModel):
    repo_id: uuid.UUID
    github_url: str
    name: Optional[str] = None
    description: Optional[str] = None
    status: str
    created_at: str
    updated_at: str

class RepoListResponse(BaseModel):
    repositories: List[RepoResponse]

class TutorialBrief(BaseModel):
    tutorial_id: uuid.UUID
    level: str
    title: str

class RepoDetailResponse(BaseModel):
    repository: RepoResponse
    tutorials: List[TutorialBrief]

class FileTreeNode(BaseModel):
    name: str
    path: str
    type: str  # 'file' or 'directory'
    children: Optional[List['FileTreeNode']] = None
    
    class Config:
        from_attributes = True

class RepoFileTreeResponse(BaseModel):
    tree: List[FileTreeNode]

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
    db: Session = Depends(get_db)
):
    existing_repo = db.query(Repository).filter(Repository.github_url == str(repo_data.github_url)).first()
    if existing_repo:
        return {
            "repo_id": existing_repo.repo_id,
            "github_url": existing_repo.github_url,
            "name": existing_repo.name,
            "description": existing_repo.description,
            "status": existing_repo.status,
            "created_at": existing_repo.created_at.isoformat(),
            "updated_at": existing_repo.updated_at.isoformat()
        }

    repo_name = str(repo_data.github_url).split('/')[-1].replace('.git', '')
    new_repo = Repository(
        github_url=str(repo_data.github_url),
        name=repo_name,
        status='PENDING',
        user_id=current_user.user_id,
    )
    db.add(new_repo)
    db.commit()
    db.refresh(new_repo)
    
    try:
        redis_pool = request.app.state.redis_pool
        await redis_pool.enqueue_job(
            'analyze_repository',
            {
                "repo_id": str(new_repo.repo_id),
                "github_url": new_repo.github_url
            }
        )
    except Exception as e:
        new_repo.status = 'FAILED'
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to enqueue analysis job")

    return {
        "repo_id": new_repo.repo_id,
        "github_url": new_repo.github_url,
        "name": new_repo.name,
        "description": new_repo.description,
        "status": new_repo.status,
        "created_at": new_repo.created_at.isoformat(),
        "updated_at": new_repo.updated_at.isoformat()
    }

@router.get("/", response_model=RepoListResponse)
async def get_user_repositories(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
                "updated_at": repo.updated_at.isoformat()
            }
            for repo in repos
        ]
    }

def get_repo_path(repo_id: uuid.UUID) -> str:
    """Get the local path where the repository is cloned."""
    return f"/tmp/reploai/{repo_id}"

def build_file_tree(repo_path: str, current_path: str = "", max_depth: int = 10, current_depth: int = 0) -> List[FileTreeNode]:
    if current_depth >= max_depth:
        return []
    
    if not os.path.exists(repo_path):
        return []
    
    tree = []
    ignored_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'dist', 'build', '.next', '.cache'}
    code_extensions = {'.js', '.jsx', '.ts', '.tsx', '.py', '.java', '.cpp', '.c', '.go', '.rs', '.rb', '.php', 
                      '.json', '.md', '.yml', '.yaml', '.html', '.css', '.scss', '.less', '.sh', '.bash', '.zsh',
                      '.sql', '.xml', '.txt', '.ini', '.conf', '.config', '.env', '.gitignore', '.dockerfile'}
    
    try:
        items = sorted(os.listdir(repo_path))
        for item in items:
            if item.startswith('.'):
                continue
            
            item_path = os.path.join(repo_path, item)
            rel_path = os.path.join(current_path, item) if current_path else item
            
            if os.path.isdir(item_path):
                if item in ignored_dirs:
                    continue
                
                children = build_file_tree(item_path, rel_path, max_depth, current_depth + 1)
                tree.append(FileTreeNode(
                    name=item,
                    path=rel_path,
                    type='directory',
                    children=children if children else None
                ))
            elif os.path.isfile(item_path):
                _, ext = os.path.splitext(item)
                if ext.lower() in code_extensions or not ext:
                    tree.append(FileTreeNode(
                        name=item,
                        path=rel_path,
                        type='file',
                        children=None
                    ))
    except PermissionError:
        pass
    except Exception:
        pass
    
    return tree

@router.get("/{repo_id}/tree", response_model=RepoFileTreeResponse)
async def get_repository_file_tree(
    repo_id: uuid.UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    repo = db.query(Repository).filter(Repository.repo_id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail=f"Repository with ID {repo_id} not found")
    
    if repo.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this repository")
    
    repo_path = get_repo_path(repo_id)
    
    if not os.path.exists(repo_path):
        if repo.status == 'COMPLETED':
            try:
                os.makedirs("/tmp/reploai", exist_ok=True)
                git.Repo.clone_from(repo.github_url, repo_path)
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to re-clone repository: {str(e)}"
                )
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Repository files not found. Repository status: {repo.status}. The repository may not have been cloned yet or analysis is still in progress."
            )
    
    tree = build_file_tree(repo_path)
    return RepoFileTreeResponse(tree=tree)

@router.get("/{repo_id}/file")
async def get_repository_file_content(
    repo_id: uuid.UUID,
    file_path: str = Query(..., description="Path to the file relative to repository root"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    repo = db.query(Repository).filter(Repository.repo_id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    if repo.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this repository")
    
    repo_path = get_repo_path(repo_id)
    
    if not os.path.exists(repo_path):
        if repo.status == 'COMPLETED':
            try:
                os.makedirs("/tmp/reploai", exist_ok=True)
                git.Repo.clone_from(repo.github_url, repo_path)
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to re-clone repository: {str(e)}"
                )
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Repository files not found. Repository status: {repo.status}. The repository may not have been cloned yet or analysis is still in progress."
            )
    
    full_path = os.path.join(repo_path, file_path)
    full_path = os.path.normpath(full_path)
    if not full_path.startswith(os.path.normpath(repo_path)):
        raise HTTPException(status_code=400, detail="Invalid file path")
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    if not os.path.isfile(full_path):
        raise HTTPException(status_code=400, detail="Path is not a file")
    
    file_size = os.path.getsize(full_path)
    if file_size > 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 1MB)")
    
    try:
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return RepoFileContentResponse(
            content=content,
            path=file_path,
            size=file_size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

@router.get("/{repo_id}", response_model=RepoDetailResponse)
async def get_repository_details(
    repo_id: uuid.UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
            "updated_at": repo.updated_at.isoformat()
        },
        "tutorials": [
            {
                "tutorial_id": tutorial.tutorial_id,
                "level": tutorial.level,
                "title": tutorial.title
            }
            for tutorial in tutorials
        ]
    }