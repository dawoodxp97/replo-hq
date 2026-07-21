"""Progress endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.dependencies import get_current_user_async
from ..core.pagination import Page, PageParams, page_params
from ..db.session import get_async_db
from ..models.user import User
from ..schemas.progress import (
    ModuleProgressDetail,
    ProgressResponse,
    ProgressUpdate,
    QuizResult,
    QuizSubmit,
    TutorialProgressSummary,
    UserProgressStats,
)
from ..services import progress as progress_service

router = APIRouter()


class ProgressOverview(BaseModel):
    """Fixed-size dashboard payload.

    The completion history used to be inlined here and was unbounded — it now
    lives at `GET /api/progress/modules`, paginated.
    """

    user_id: UUID
    stats: UserProgressStats
    tutorials: list[TutorialProgressSummary]


@router.post("/complete_module", response_model=ProgressResponse)
async def mark_module_complete(
    body: ProgressUpdate,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """Mark a module finished. Idempotent — repeat calls keep the first timestamp."""
    return await progress_service.complete_module(db, current_user.user_id, body.module_id)


@router.delete("/modules/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unmark_module_complete(
    module_id: UUID,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
) -> None:
    """Undo a completion. Progress was previously write-once."""
    await progress_service.uncomplete_module(db, current_user.user_id, module_id)


@router.post("/submit_quiz", response_model=QuizResult)
async def submit_quiz_answer(
    body: QuizSubmit,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """Grade an attempt, record the score, and mark the module complete.

    The response carries `correct_answer` — after an attempt, which is the only
    place it is disclosed. The quiz body itself never includes it; see
    `schemas/tutorial.py::QuizOption`.
    """
    return await progress_service.submit_quiz(
        db, current_user.user_id, body.quiz_id, body.submitted_answer
    )


@router.get("", response_model=ProgressOverview)
async def get_progress_overview(
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    stats = await progress_service.get_stats(db, current_user.user_id)
    tutorials = await progress_service.list_tutorial_summaries(db, current_user.user_id)
    return ProgressOverview(user_id=current_user.user_id, stats=stats, tutorials=tutorials)


@router.get("/modules", response_model=Page[ModuleProgressDetail])
async def list_module_progress(
    params: PageParams = Depends(page_params),
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """Completion history, newest first."""
    items, total = await progress_service.list_module_progress(db, current_user.user_id, params)
    return Page[ModuleProgressDetail].build(items, total, params)
