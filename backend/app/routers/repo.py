# ./backend/app/routers/repo.py
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl

from ..db.session import get_db
from ..core.dependencies import get_current_user
from .. import models
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

# --- API Endpoints ---
@router.post("/", response_model=RepoResponse)
async def submit_repository(
    repo_data: RepoCreate,
    request: Request,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit a new GitHub URL for analysis.
    Returns 202 Accepted immediately.
    """
    # 1. Check if URL already exists
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

    # 2. Create 'PENDING' entry in DB
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
    
    # 3. Add job to Redis queue
    try:
        # Get the Redis pool from the app state
        redis_pool = request.app.state.redis_pool
        
        # Enqueue the job
        await redis_pool.enqueue_job(
            'analyze_repository',
            {
                "repo_id": str(new_repo.repo_id),
                "github_url": new_repo.github_url
            }
        )
        
        print(f"Job enqueued for repository: {new_repo.repo_id}")
    except Exception as e:
        print(f"Error enqueueing job: {str(e)}")
        # Update repo status to FAILED
        new_repo.status = 'FAILED'
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to enqueue analysis job")

    # 4. Return the new repo entry
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
    """
    Get all repositories submitted by the user and their status.
    """
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

@router.get("/{repo_id}", response_model=RepoDetailResponse)
async def get_repository_details(
    repo_id: uuid.UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get details for one repo, including its generated tutorials.
    """
    repo = db.query(Repository).filter(Repository.repo_id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Verify user owns this repository
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