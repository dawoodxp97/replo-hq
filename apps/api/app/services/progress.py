"""Progress service.

Three problems this replaces:

1. **Neither write endpoint validated what it was writing to.**
   `complete_module` took a `module_id` and inserted a row; `submit_quiz` looked
   a quiz up by primary key. No ownership, no visibility check, nothing. Any user
   could record progress against any module in the product — and because
   `GET /progress` joins Module and Tutorial to enrich the response, those rows
   came back carrying **other users' private module and tutorial titles**. A
   write endpoint was a read primitive for private data.

2. **Check-then-insert against a unique constraint.** `uq_user_module` exists, so
   two concurrent completions of the same module raced into an IntegrityError and
   a 500. Now a single `ON CONFLICT` statement.

3. **`datetime.now()` — naive — into a `timestamptz` column.** Postgres applied
   the server's timezone, so completion times were wrong by the UTC offset.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.ownership import get_readable_module, get_readable_quiz
from ..core.pagination import PageParams
from ..models.modules import Module
from ..models.quizzes import Quiz
from ..models.tutorials import Tutorial
from ..models.user_progress import UserProgress
from ..schemas.progress import (
    ModuleProgressDetail,
    QuizResult,
    TutorialProgressSummary,
    UserProgressStats,
)

logger = logging.getLogger(__name__)

# How many tutorial summaries the overview returns. Bounded because the overview
# is a fixed-size dashboard payload, not a browsable list.
MAX_SUMMARIES = 100


# --- Writes -----------------------------------------------------------------


async def complete_module(db: AsyncSession, user_id: UUID, module_id: UUID) -> UserProgress:
    """Record completion of a module. Idempotent.

    `ON CONFLICT DO NOTHING` rather than DO UPDATE: `completed_at` means *when
    this was first finished*, and re-opening a module to re-read it should not
    rewrite that. It also preserves a `quiz_score` already recorded by
    `submit_quiz`, which the old update-in-place path did not consider.
    """
    await get_readable_module(db, module_id, user_id)

    stmt = (
        pg_insert(UserProgress)
        .values(
            user_id=user_id,
            module_id=module_id,
            completed_at=datetime.now(UTC),
        )
        .on_conflict_do_nothing(constraint="uq_user_module")
    )
    await db.execute(stmt)
    await db.commit()

    # Re-read rather than use RETURNING: DO NOTHING returns no row on conflict,
    # so RETURNING would give None exactly in the repeat case.
    return (
        await db.execute(
            select(UserProgress).where(
                UserProgress.user_id == user_id,
                UserProgress.module_id == module_id,
            )
        )
    ).scalar_one()


async def uncomplete_module(db: AsyncSession, user_id: UUID, module_id: UUID) -> None:
    """Undo a completion. Absent before — progress was write-once.

    Deliberately not an ownership check on the progress row itself: the delete is
    already scoped to `user_id`, so it can only ever affect the caller's own row.
    """
    row = (
        await db.execute(
            select(UserProgress).where(
                UserProgress.user_id == user_id,
                UserProgress.module_id == module_id,
            )
        )
    ).scalar_one_or_none()

    if row is not None:
        await db.delete(row)
        await db.commit()


def _grade(quiz: Quiz, submitted: str) -> bool:
    """Compare an answer against the stored key.

    `correct_answer` is authoritative — `routers/author.py` derives it from
    whichever option carries `is_correct`. The options list is the fallback for
    rows written before that column was populated.

    Comparison is case- and whitespace-insensitive: the client submits option
    *text*, and the old exact `==` meant a trailing space marked a right answer
    wrong.
    """
    answer = submitted.strip().casefold()

    if quiz.correct_answer:
        return quiz.correct_answer.strip().casefold() == answer

    for option in quiz.options or []:
        if not isinstance(option, dict):
            continue
        if option.get("is_correct") and str(option.get("text", "")).strip().casefold() == answer:
            return True
    return False


async def submit_quiz(db: AsyncSession, user_id: UUID, quiz_id: UUID, submitted: str) -> QuizResult:
    """Grade an attempt and record the score.

    Submitting also marks the module complete, which is the pre-existing
    behaviour and is what the player UI relies on.

    `quiz_score` is overwritten on re-submission — there is no attempt history.
    That is a product decision to revisit (it makes "average score" mean "average
    latest score"), not an oversight.
    """
    quiz = await get_readable_quiz(db, quiz_id, user_id)
    is_correct = _grade(quiz, submitted)
    score = 1 if is_correct else 0

    stmt = (
        pg_insert(UserProgress)
        .values(
            user_id=user_id,
            module_id=quiz.module_id,
            completed_at=datetime.now(UTC),
            quiz_score=score,
        )
        .on_conflict_do_update(
            constraint="uq_user_module",
            set_={"quiz_score": score},
        )
    )
    await db.execute(stmt)
    await db.commit()

    return QuizResult(
        is_correct=is_correct,
        # Revealed only after an attempt.
        correct_answer=quiz.correct_answer,
        module_id=quiz.module_id,
    )


# --- Reads ------------------------------------------------------------------


def _detail_stmt(user_id: UUID) -> Select:
    return (
        select(
            UserProgress.progress_id,
            UserProgress.module_id,
            UserProgress.completed_at,
            UserProgress.quiz_score,
            Module.title.label("module_title"),
            Module.order_index.label("module_order_index"),
            Tutorial.tutorial_id,
            Tutorial.title.label("tutorial_title"),
            Tutorial.level.label("tutorial_level"),
        )
        .join(Module, UserProgress.module_id == Module.module_id)
        .join(Tutorial, Module.tutorial_id == Tutorial.tutorial_id)
        .where(UserProgress.user_id == user_id)
    )


async def list_module_progress(
    db: AsyncSession, user_id: UUID, params: PageParams
) -> tuple[list[ModuleProgressDetail], int]:
    """Paginated completion history.

    Split out of the old `GET /progress`, which returned **every** progress row
    the user had ever created alongside the stats — unbounded, and growing with
    engagement, so the most active users got the slowest response.
    """
    stmt = _detail_stmt(user_id)

    total = (
        await db.execute(select(func.count()).select_from(stmt.order_by(None).subquery()))
    ).scalar_one()

    rows = (
        await db.execute(
            stmt.order_by(UserProgress.completed_at.desc())
            .limit(params.limit)
            .offset(params.offset)
        )
    ).all()

    return [ModuleProgressDetail(**row._mapping) for row in rows], total


async def get_stats(db: AsyncSession, user_id: UUID) -> UserProgressStats:
    """Aggregate in Postgres rather than in Python.

    The old version pulled every progress row into memory and looped over the
    list four times to compute these five numbers.
    """
    row = (
        await db.execute(
            select(
                func.count(UserProgress.progress_id).label("completed"),
                func.count(UserProgress.quiz_score).label("attempted"),
                func.coalesce(func.sum(UserProgress.quiz_score), 0).label("correct"),
                func.avg(UserProgress.quiz_score).label("avg_score"),
                func.count(func.distinct(Module.tutorial_id)).label("tutorials"),
                func.max(UserProgress.completed_at).label("last_activity"),
            )
            .select_from(UserProgress)
            .join(Module, UserProgress.module_id == Module.module_id)
            .where(UserProgress.user_id == user_id)
        )
    ).one()

    return UserProgressStats(
        total_modules_completed=row.completed,
        # count() skips NULLs, which is exactly "quizzes attempted" — a completed
        # module with no quiz has quiz_score NULL.
        total_quizzes_attempted=row.attempted,
        total_quizzes_correct=int(row.correct),
        average_quiz_score=round(float(row.avg_score) * 100, 2)
        if row.avg_score is not None
        else 0.0,
        total_tutorials_with_progress=row.tutorials,
        last_activity_at=row.last_activity,
    )


async def list_tutorial_summaries(db: AsyncSession, user_id: UUID) -> list[TutorialProgressSummary]:
    """Per-tutorial rollup, one query.

    The old version ran two queries *per tutorial* inside a Python loop — a
    textbook N+1 that scaled with how much the user had studied. The total module
    count is a correlated subquery so tutorials with zero completions are still
    divided by the right denominator.
    """
    total_modules = (
        select(func.count(Module.module_id))
        .where(Module.tutorial_id == Tutorial.tutorial_id)
        .correlate(Tutorial)
        .scalar_subquery()
    )

    rows = (
        await db.execute(
            select(
                Tutorial.tutorial_id,
                Tutorial.title,
                Tutorial.level,
                total_modules.label("total_modules"),
                func.count(UserProgress.progress_id).label("completed_modules"),
                func.avg(UserProgress.quiz_score).label("avg_score"),
                func.max(UserProgress.completed_at).label("last_completed_at"),
            )
            .select_from(UserProgress)
            .join(Module, UserProgress.module_id == Module.module_id)
            .join(Tutorial, Module.tutorial_id == Tutorial.tutorial_id)
            .where(UserProgress.user_id == user_id)
            .group_by(Tutorial.tutorial_id, Tutorial.title, Tutorial.level)
            .order_by(func.max(UserProgress.completed_at).desc())
            .limit(MAX_SUMMARIES)
        )
    ).all()

    return [
        TutorialProgressSummary(
            tutorial_id=r.tutorial_id,
            tutorial_title=r.title,
            tutorial_level=r.level,
            total_modules=r.total_modules,
            completed_modules=r.completed_modules,
            progress_percentage=(
                round(r.completed_modules / r.total_modules * 100, 2) if r.total_modules else 0.0
            ),
            average_quiz_score=(
                round(float(r.avg_score) * 100, 2) if r.avg_score is not None else None
            ),
            last_completed_at=r.last_completed_at,
        )
        for r in rows
    ]
