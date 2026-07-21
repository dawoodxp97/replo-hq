"""Authoring endpoints — manual editing of tutorials, modules and quizzes."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.dependencies import get_current_user_async
from ..core.pagination import Page, PageParams, page_params
from ..db.session import get_async_db
from ..models.user import User
from ..schemas.author import (
    AuthorTutorialListItem,
    ModuleReorder,
    ModuleResponse,
    ModuleWrite,
    QuizResponse,
    QuizWrite,
    TutorialMetaResponse,
    TutorialUpdate,
)
from ..services import author as author_service

router = APIRouter()


# --- Tutorials --------------------------------------------------------------


@router.get("/tutorials", response_model=Page[AuthorTutorialListItem])
async def list_authored_tutorials(
    params: PageParams = Depends(page_params),
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """The authoring dashboard. Ordered by last edit, not generation date."""
    items, total = await author_service.list_authored_tutorials(db, current_user.user_id, params)
    return Page[AuthorTutorialListItem].build(items, total, params)


@router.patch("/tutorials/{tutorial_id}", response_model=TutorialMetaResponse)
async def update_tutorial(
    tutorial_id: UUID,
    body: TutorialUpdate,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """PATCH, not PUT: every field is optional and omitted fields are left alone."""
    return await author_service.update_tutorial(db, tutorial_id, current_user.user_id, body)


# --- Modules ----------------------------------------------------------------


@router.get("/tutorials/{tutorial_id}/modules", response_model=list[ModuleResponse])
async def list_modules(
    tutorial_id: UUID,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """Bounded by one tutorial, so unpaginated."""
    return await author_service.list_modules(db, tutorial_id, current_user.user_id)


@router.post(
    "/tutorials/{tutorial_id}/modules",
    response_model=ModuleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_module(
    tutorial_id: UUID,
    body: ModuleWrite,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """Append a module. Authoring could previously edit but never add."""
    return await author_service.create_module(db, tutorial_id, current_user.user_id, body)


@router.put("/tutorials/{tutorial_id}/modules/reorder", response_model=list[ModuleResponse])
async def reorder_modules(
    tutorial_id: UUID,
    body: ModuleReorder,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """Submit **every** module id in the new order — a partial list is rejected."""
    return await author_service.reorder_modules(db, tutorial_id, current_user.user_id, body)


@router.put("/modules/{module_id}", response_model=ModuleResponse)
async def update_module(
    module_id: UUID,
    body: ModuleWrite,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    return await author_service.update_module(db, module_id, current_user.user_id, body)


@router.delete("/modules/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_module(
    module_id: UUID,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
) -> None:
    """Deletes the module, its quiz (FK cascade), and closes the `order_index` gap."""
    await author_service.delete_module(db, module_id, current_user.user_id)


# --- Quizzes ----------------------------------------------------------------
#
# Addressed by module: `quizzes.module_id` is UNIQUE, so a module has at most one
# quiz and the module id is the stable handle. This replaces
# `PUT /quizzes/{quiz_id}`, which could only edit a quiz that already existed —
# and since the pipeline creates none, nothing could create the first one.


@router.get("/modules/{module_id}/quiz", response_model=QuizResponse | None)
async def get_quiz(
    module_id: UUID,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """The authoring view, answer key included — the owner wrote it."""
    return await author_service.get_quiz(db, module_id, current_user.user_id)


@router.put("/modules/{module_id}/quiz", response_model=QuizResponse)
async def upsert_quiz(
    module_id: UUID,
    body: QuizWrite,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """Create or replace a module's quiz."""
    return await author_service.upsert_quiz(db, module_id, current_user.user_id, body)


@router.delete("/modules/{module_id}/quiz", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quiz(
    module_id: UUID,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
) -> None:
    await author_service.delete_quiz(db, module_id, current_user.user_id)
