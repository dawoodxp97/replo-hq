"""Repository endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.dependencies import get_current_user_async
from ..core.pagination import Page, PageParams, page_params
from ..db.session import get_async_db
from ..models.user import User
from ..schemas.repo import (
    RepoCreate,
    RepoDetailResponse,
    RepoFileContentResponse,
    RepoFileTreeResponse,
    RepoResponse,
)
from ..services import repo as repo_service

router = APIRouter()


@router.post("", response_model=RepoResponse, status_code=status.HTTP_201_CREATED)
async def add_repository(
    body: RepoCreate,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """Add a repository to the caller's account.

    Idempotent per user: submitting a URL already on the account returns the
    existing row rather than erroring.
    """
    return await repo_service.add_repository(db, current_user.user_id, body.github_url)


@router.get("", response_model=Page[RepoResponse])
async def list_repositories(
    params: PageParams = Depends(page_params),
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """List the caller's repositories.

    Now paginated. The old version returned every repository the user owned in a
    `{"repositories": [...]}` wrapper with no limit.
    """
    repos, total = await repo_service.list_repositories(db, current_user.user_id, params)
    return Page[RepoResponse].build([RepoResponse.model_validate(r) for r in repos], total, params)


@router.get("/{repo_id}", response_model=RepoDetailResponse)
async def get_repository(
    repo_id: UUID,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    repo, tutorials = await repo_service.get_repository_detail(db, repo_id, current_user.user_id)
    return RepoDetailResponse(repository=RepoResponse.model_validate(repo), tutorials=tutorials)


@router.delete("/{repo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repository(
    repo_id: UUID,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
) -> None:
    """Delete a repository, its tutorials (FK cascade), and its on-disk clone."""
    await repo_service.delete_repository(db, repo_id, current_user.user_id)


@router.get("/{repo_id}/tree", response_model=RepoFileTreeResponse)
async def get_file_tree(
    repo_id: UUID,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    tree = await repo_service.get_file_tree(db, repo_id, current_user.user_id)
    return RepoFileTreeResponse(tree=tree)


@router.get("/{repo_id}/file", response_model=RepoFileContentResponse)
async def get_file_content(
    repo_id: UUID,
    file_path: str = Query(..., description="Path relative to the repository root"),
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    content, size = await repo_service.get_file_content(
        db, repo_id, current_user.user_id, file_path
    )
    return RepoFileContentResponse(content=content, path=file_path, size=size)
