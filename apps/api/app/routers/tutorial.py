"""Tutorial endpoints.

**Route order matters here.** `/generation/status` and `/generate` are declared
before `/{tutorial_id}`; FastAPI matches in declaration order, so a literal path
placed after a parameterised one is unreachable.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.dependencies import get_current_user_async, get_optional_user
from ..core.pagination import Page, PageParams, page_params
from ..db.session import get_async_db
from ..models.user import User
from ..schemas.tutorial import (
    GenerateRequest,
    GenerateResponse,
    GenerationStatusResponse,
    StatusResponse,
    TutorialListItem,
    TutorialResponse,
    VisibilityUpdate,
)
from ..services import tutorial as tutorial_service

router = APIRouter()


# --- Literal paths (must precede /{tutorial_id}) ----------------------------


@router.post("/generate", response_model=GenerateResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_tutorial(
    body: GenerateRequest,
    request: Request,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """Queue a tutorial generation.

    202, not 200: nothing is generated when this returns. Poll
    `/{instance_id}/status`.
    """
    instance = await tutorial_service.start_generation(
        db,
        current_user.user_id,
        body,
        getattr(request.app.state, "redis_pool", None),
    )
    return GenerateResponse(instance_id=instance.id, status=instance.status)


@router.get("/generation/status", response_model=GenerationStatusResponse)
async def get_generation_status_by_url(
    repo_url: str = Query(..., description="Repository URL to check status for"),
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """Legacy polling endpoint, keyed by repo URL. Prefer `/{instance_id}/status`."""
    return await tutorial_service.get_status_by_repo_url(db, current_user.user_id, repo_url)


# --- Collection -------------------------------------------------------------


@router.get("", response_model=Page[TutorialListItem])
async def list_tutorials(
    params: PageParams = Depends(page_params),
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    items, total = await tutorial_service.list_tutorials(db, current_user.user_id, params)
    return Page[TutorialListItem].build(items, total, params)


# --- Single tutorial --------------------------------------------------------


@router.get("/{tutorial_id}", response_model=TutorialResponse)
async def get_tutorial(
    tutorial_id: UUID,
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Read a tutorial.

    Optional auth: the owner sees their private tutorials, and anyone — signed in
    or not — can read a public or unlisted one.

    The previous version took no ownership into account *at all*. It fetched by
    primary key and returned the whole body, so any authenticated user could read
    any other user's tutorial. It also declared `response_model=Any`, so the
    schema was absent from OpenAPI and nothing constrained what came back.
    """
    return await tutorial_service.get_tutorial(
        db, tutorial_id, current_user.user_id if current_user else None
    )


@router.delete("/{tutorial_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tutorial(
    tutorial_id: UUID,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
) -> None:
    await tutorial_service.delete_tutorial(db, tutorial_id, current_user.user_id)


@router.patch("/{tutorial_id}/visibility", response_model=TutorialResponse)
async def set_visibility(
    tutorial_id: UUID,
    body: VisibilityUpdate,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """Publish or unpublish. Owner only — visibility is not a read operation."""
    await tutorial_service.set_visibility(db, tutorial_id, current_user.user_id, body.visibility)
    return await tutorial_service.get_tutorial(db, tutorial_id, current_user.user_id)


# --- Generation instances ---------------------------------------------------


@router.post(
    "/{instance_id}/retry",
    response_model=GenerateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def retry_generation(
    instance_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    instance = await tutorial_service.retry_generation(
        db,
        instance_id,
        current_user.user_id,
        getattr(request.app.state, "redis_pool", None),
    )
    return GenerateResponse(instance_id=instance.id, status=instance.status)


@router.get("/{instance_id}/status", response_model=StatusResponse)
async def get_generation_status(
    instance_id: UUID,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    return await tutorial_service.get_generation_status(db, instance_id, current_user.user_id)


@router.get("/{instance_id}/result")
async def get_generation_result(
    instance_id: UUID,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """Raw pipeline output. Internal; use `GET /{tutorial_id}` to read a tutorial."""
    return await tutorial_service.get_generation_result(db, instance_id, current_user.user_id)
