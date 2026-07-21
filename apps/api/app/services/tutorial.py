"""Tutorial service.

Absorbs the query logic that lived in `routers/tutorial.py` — the largest router
in the app at 443 lines, of which most was ORM code and dict assembly.

Two things worth reading before editing:

1. **`get_tutorial` used to have no ownership check whatsoever.** It looked up by
   primary key alone and returned the full body, so any authenticated user could
   read any other user's tutorial by guessing or observing an id. Reads now go
   through `get_readable_tutorial`, which also handles public/anonymous access.
2. **`generate` never validated the URL.** It stored `request.repoUrl` verbatim
   on the instance row and handed it to the worker, which passed it to
   `git clone` — routing straight around every check the repo slice added. It is
   normalised here now.
"""

import logging
import re
import uuid
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.exceptions import ConflictError, ExternalServiceError, NotFoundError
from ..core.ownership import get_owned_tutorial, get_readable_tutorial
from ..core.pagination import PageParams
from ..models.enums import RunStatus, TutorialVisibility
from ..models.modules import Module
from ..models.orchestration import TutorialExecution, TutorialInstance, TutorialStepExecution
from ..models.quizzes import Quiz
from ..models.repositories import Repository
from ..models.tutorials import Tutorial
from ..models.user_progress import UserProgress
from ..schemas.tutorial import (
    GenerateRequest,
    ModuleResponse,
    QuizResponse,
    TutorialListItem,
    TutorialResponse,
)
from ..utils import repo_utils
from . import repo as repo_service

logger = logging.getLogger(__name__)

# The pipeline is a fixed 5-step chain (orchestrator/agent.py). Used only to turn
# a step index into a percentage for the legacy status endpoint.
TOTAL_STEPS = 5


# --- Listing ----------------------------------------------------------------


async def list_tutorials(
    db: AsyncSession, user_id: UUID, params: PageParams
) -> tuple[list[TutorialListItem], int]:
    """One page of the caller's tutorials, with per-tutorial progress.

    The old version issued five queries and stitched the result together in
    Python: tutorials, a GROUP BY for module counts, *all* module ids for those
    tutorials, all matching progress rows, then all repositories — then built
    dicts in a loop. On an account with a few hundred tutorials the third query
    alone pulled every module id in the account into memory.

    This is one query. The two counts are correlated scalar subqueries, so
    Postgres computes them per row against its own indexes
    (`idx_module_tutorial`, `idx_progress_user_module`) and nothing intermediate
    crosses the wire.
    """
    module_count = (
        select(func.count(Module.module_id))
        .where(Module.tutorial_id == Tutorial.tutorial_id)
        .correlate(Tutorial)
        .scalar_subquery()
    )

    completed_count = (
        select(func.count(UserProgress.progress_id))
        .select_from(UserProgress)
        .join(Module, UserProgress.module_id == Module.module_id)
        .where(
            Module.tutorial_id == Tutorial.tutorial_id,
            UserProgress.user_id == user_id,
        )
        .correlate(Tutorial)
        .scalar_subquery()
    )

    base = (
        select(
            Tutorial,
            Repository.name.label("repo_name"),
            Repository.github_url.label("repo_url"),
            module_count.label("module_count"),
            completed_count.label("completed_modules"),
        )
        .join(Repository, Tutorial.repo_id == Repository.repo_id)
        .where(Repository.user_id == user_id)
    )

    # Counted separately rather than via `paginate()`: that helper returns
    # `.scalars()`, which would discard every column but the Tutorial entity.
    count_stmt = select(func.count()).select_from(
        select(Tutorial.tutorial_id)
        .join(Repository, Tutorial.repo_id == Repository.repo_id)
        .where(Repository.user_id == user_id)
        .subquery()
    )
    total = (await db.execute(count_stmt)).scalar_one()

    rows = (
        await db.execute(
            base.order_by(Tutorial.generated_at.desc()).limit(params.limit).offset(params.offset)
        )
    ).all()

    items = [
        TutorialListItem(
            tutorial_id=row.Tutorial.tutorial_id,
            repo_id=row.Tutorial.repo_id,
            level=row.Tutorial.level,
            title=row.Tutorial.title,
            overview=row.Tutorial.overview,
            visibility=row.Tutorial.visibility,
            slug=row.Tutorial.slug,
            generated_at=row.Tutorial.generated_at,
            module_count=row.module_count,
            completed_modules=row.completed_modules,
            progress_percentage=(
                int(row.completed_modules / row.module_count * 100) if row.module_count else 0
            ),
            repo_name=row.repo_name,
            repo_url=row.repo_url,
        )
        for row in rows
    ]
    return items, total


# --- Read -------------------------------------------------------------------


async def get_tutorial(
    db: AsyncSession, tutorial_id: UUID, user_id: UUID | None
) -> TutorialResponse:
    """Full tutorial body: modules in order, each with its quiz.

    `get_readable_tutorial` is the wider check — it admits the owner, and admits
    anyone (including anonymous callers) for public and unlisted tutorials. That
    is what will back the public `/t/{slug}` pages without a second code path.

    Three queries total, all bounded by one tutorial. The alternative — a single
    join across modules and quizzes — multiplies the module's `content_markdown`
    across rows, and that column is the largest in the schema.
    """
    tutorial = await get_readable_tutorial(db, tutorial_id, user_id)

    repo = (
        await db.execute(select(Repository).where(Repository.repo_id == tutorial.repo_id))
    ).scalar_one_or_none()

    modules = (
        (
            await db.execute(
                select(Module)
                .where(Module.tutorial_id == tutorial.tutorial_id)
                .order_by(Module.order_index)
            )
        )
        .scalars()
        .all()
    )

    quiz_by_module: dict[UUID, Quiz] = {}
    if modules:
        quizzes = (
            (
                await db.execute(
                    select(Quiz).where(Quiz.module_id.in_([m.module_id for m in modules]))
                )
            )
            .scalars()
            .all()
        )
        quiz_by_module = {q.module_id: q for q in quizzes}

    return TutorialResponse(
        tutorial_id=tutorial.tutorial_id,
        repo_id=tutorial.repo_id,
        level=tutorial.level,
        title=tutorial.title,
        overview=tutorial.overview,
        overview_diagram_mermaid=tutorial.overview_diagram_mermaid,
        visibility=tutorial.visibility,
        slug=tutorial.slug,
        published_at=tutorial.published_at,
        generated_at=tutorial.generated_at,
        modules=[
            ModuleResponse(
                module_id=m.module_id,
                title=m.title,
                order_index=m.order_index,
                content_markdown=m.content_markdown,
                file_path=m.file_path,
                code_snippet=m.code_snippet,
                diagram_mermaid=m.diagram_mermaid,
                quiz=(
                    QuizResponse.model_validate(quiz_by_module[m.module_id])
                    if m.module_id in quiz_by_module
                    else None
                ),
            )
            for m in modules
        ],
        repo_name=repo.name if repo else None,
        repo_url=repo.github_url if repo else None,
    )


async def delete_tutorial(db: AsyncSession, tutorial_id: UUID, user_id: UUID) -> None:
    """Modules and quizzes cascade via their FKs."""
    tutorial = await get_owned_tutorial(db, tutorial_id, user_id)
    await db.delete(tutorial)
    await db.commit()


# --- Publishing -------------------------------------------------------------

_SLUG_STRIP = re.compile(r"[^a-z0-9]+")


def _slugify(title: str) -> str:
    base = _SLUG_STRIP.sub("-", title.lower()).strip("-")
    # Bound it well under the column's 280 chars — the uniqueness suffix is
    # appended after this.
    return base[:200] or "tutorial"


async def set_visibility(
    db: AsyncSession,
    tutorial_id: UUID,
    user_id: UUID,
    visibility: TutorialVisibility,
) -> Tutorial:
    """Publish or unpublish. This is the only writer of `visibility`.

    Publishing is an explicit act and never a side effect of generation — rows
    are created PRIVATE by the column default (docs/DECISIONS.md D8).

    The slug is assigned on first publish and then **never changes**, even if the
    tutorial is unpublished and republished or its title is edited. A public URL
    that stops resolving is worse than one that no longer matches the title.
    """
    tutorial = await get_owned_tutorial(db, tutorial_id, user_id)

    if visibility != TutorialVisibility.PRIVATE and tutorial.slug is None:
        tutorial.slug = await _allocate_slug(db, tutorial.title, tutorial.tutorial_id)

    if visibility == TutorialVisibility.PUBLIC and tutorial.published_at is None:
        tutorial.published_at = datetime.now(UTC)

    tutorial.visibility = visibility
    await db.commit()
    await db.refresh(tutorial)
    return tutorial


async def _allocate_slug(db: AsyncSession, title: str, tutorial_id: UUID) -> str:
    """Build a globally unique slug.

    `slug` is unique across the whole table, not per user — it addresses
    `/t/{slug}` on apps/site, so two users publishing tutorials for the same repo
    would otherwise collide. The id fragment makes that essentially impossible
    while keeping the URL readable; the loop covers the remaining case rather
    than trusting a probability argument to hold under a UNIQUE constraint.
    """
    base = _slugify(title)

    for attempt in range(5):
        suffix = str(tutorial_id)[:8] if attempt == 0 else uuid.uuid4().hex[:8]
        candidate = f"{base}-{suffix}"

        taken = (
            await db.execute(select(Tutorial.tutorial_id).where(Tutorial.slug == candidate))
        ).scalar_one_or_none()

        if taken is None:
            return candidate

    raise ConflictError("Could not allocate a unique URL for this tutorial.")


# --- Generation -------------------------------------------------------------


async def start_generation(
    db: AsyncSession,
    user_id: UUID,
    body: GenerateRequest,
    redis_pool,
) -> TutorialInstance:
    """Create a generation instance and enqueue the pipeline job.

    ## Two fixes

    **The URL was never validated.** `repoUrl` went onto the row verbatim and the
    worker handed it to `git clone`, so `file:///etc/` and
    `http://169.254.169.254/` were reachable through this endpoint even after the
    repo slice locked down the repo endpoints. Normalising here means one
    canonical form reaches the database and the worker.

    **A missing Redis pool was silent.** The old code was
    `if redis_pool: await enqueue(...)` with no else, so when Redis was down the
    caller got a 200, an instance id and `status: pending` for a job that had
    never been queued — and then polled a status that would never change. It now
    fails loudly and the instance is not left behind.
    """
    url = repo_utils.normalise_repo_url(body.repoUrl)

    # Ensure the user owns a Repository row for this URL. TutorialInstance stores
    # a raw string with no FK, so the produced tutorial is matched back by URL —
    # normalising both sides through the same function is what makes that join
    # work at all.
    await repo_service.add_repository(db, user_id, url)

    instance = TutorialInstance(user_id=user_id, repo_url=url, status=RunStatus.PENDING)
    db.add(instance)
    await db.commit()
    await db.refresh(instance)

    await _enqueue(db, instance, redis_pool)
    return instance


async def retry_generation(
    db: AsyncSession, instance_id: UUID, user_id: UUID, redis_pool
) -> TutorialInstance:
    instance = await _get_owned_instance(db, instance_id, user_id)

    if instance.status not in (RunStatus.FAILED, RunStatus.COMPLETED):
        raise ConflictError("This generation is still running.")

    instance.status = RunStatus.PENDING
    await db.commit()
    await db.refresh(instance)

    await _enqueue(db, instance, redis_pool)
    return instance


async def _enqueue(db: AsyncSession, instance: TutorialInstance, redis_pool) -> None:
    if redis_pool is None:
        await db.delete(instance)
        await db.commit()
        raise ExternalServiceError("Generation queue is unavailable. Please try again shortly.")

    try:
        await redis_pool.enqueue_job(
            "generate_tutorial_task", tutorial_instance_id=str(instance.id)
        )
    except Exception as exc:
        # Mark it failed rather than leaving a pending row nothing will ever pick
        # up — a stuck "pending" is indistinguishable from a slow job in the UI.
        instance.status = RunStatus.FAILED
        await db.commit()
        logger.exception("Failed to enqueue generation for instance %s", instance.id)
        raise ExternalServiceError("Could not start generation. Please try again.") from exc


async def _get_owned_instance(
    db: AsyncSession, instance_id: UUID, user_id: UUID
) -> TutorialInstance:
    """404, not 403, when the instance belongs to someone else.

    The old handlers returned 403 here, which confirms the id is real — an
    enumeration oracle. See core/ownership.py.
    """
    instance = (
        await db.execute(
            select(TutorialInstance).where(
                TutorialInstance.id == instance_id,
                TutorialInstance.user_id == user_id,
            )
        )
    ).scalar_one_or_none()

    if instance is None:
        raise NotFoundError("Tutorial generation not found.")
    return instance


async def _latest_execution(db: AsyncSession, instance_id: UUID) -> TutorialExecution | None:
    return (
        await db.execute(
            select(TutorialExecution)
            .where(TutorialExecution.tutorial_instance_id == instance_id)
            .order_by(TutorialExecution.started_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()


async def get_generation_status(db: AsyncSession, instance_id: UUID, user_id: UUID) -> dict:
    instance = await _get_owned_instance(db, instance_id, user_id)
    execution = await _latest_execution(db, instance.id)

    current_step = None
    step_status = None
    error_message = execution.error_message if execution else None

    if execution is not None:
        latest_step = (
            await db.execute(
                select(TutorialStepExecution)
                .where(TutorialStepExecution.tutorial_execution_id == execution.id)
                .order_by(TutorialStepExecution.started_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()

        if latest_step is not None:
            current_step = latest_step.step_type
            step_status = latest_step.status
            error_message = error_message or latest_step.error_message

    return {
        "status": instance.status,
        "current_step": current_step,
        "step_status": step_status,
        "error_message": error_message,
        "created_at": instance.created_at,
        "updated_at": instance.updated_at,
    }


async def get_status_by_repo_url(db: AsyncSession, user_id: UUID, raw_url: str) -> dict:
    """Legacy frontend polling endpoint, keyed by repo URL rather than id.

    The URL is normalised on the way in for the same reason it is on the way out:
    the row was written with a canonical URL, so a caller passing the `.git` form
    or a trailing slash would otherwise never match and would see NOT_FOUND
    forever.
    """
    url = repo_utils.normalise_repo_url(raw_url)

    instance = (
        await db.execute(
            select(TutorialInstance)
            .where(
                TutorialInstance.repo_url == url,
                TutorialInstance.user_id == user_id,
            )
            .order_by(TutorialInstance.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    if instance is None:
        return {
            "isGenerating": False,
            "generationStep": 0,
            "generationProgress": 0,
            "generationId": None,
            "repoId": None,
            "status": "NOT_FOUND",
            "errorMessage": None,
        }

    step = 0
    progress = 0
    error_message = None

    if instance.status == RunStatus.COMPLETED:
        step, progress = TOTAL_STEPS, 100
    elif instance.status == RunStatus.FAILED:
        execution = await _latest_execution(db, instance.id)
        error_message = execution.error_message if execution else None
    elif instance.status == RunStatus.RUNNING:
        execution = await _latest_execution(db, instance.id)
        if execution is not None:
            step = execution.current_step_order
            # Capped below 100 on purpose: the run is not done until the instance
            # says so, and showing 100% while still working reads as a hang.
            progress = min(int(step / TOTAL_STEPS * 100), 90)

    repo = (
        await db.execute(
            select(Repository).where(
                Repository.github_url == url,
                Repository.user_id == user_id,
            )
        )
    ).scalar_one_or_none()

    return {
        "isGenerating": instance.status in (RunStatus.PENDING, RunStatus.RUNNING),
        "generationStep": step,
        "generationProgress": progress,
        "generationId": str(instance.id),
        "repoId": str(repo.repo_id) if repo else None,
        # Uppercase for the legacy client. The enum is lowercase everywhere else.
        "status": str(instance.status).upper(),
        "errorMessage": error_message,
    }


async def get_generation_result(db: AsyncSession, instance_id: UUID, user_id: UUID) -> dict:
    """Raw merged step output.

    Internal pipeline state, not a product surface — `GET /api/tutorial/{id}`
    is the endpoint for reading a tutorial. Kept because the legacy client calls
    it during generation; it should go once apps/web lands.
    """
    instance = await _get_owned_instance(db, instance_id, user_id)

    if instance.status != RunStatus.COMPLETED:
        raise ConflictError("Generation has not completed.")

    execution = await _latest_execution(db, instance.id)
    if execution is None:
        raise NotFoundError("No execution found for this generation.")

    steps = (
        (
            await db.execute(
                select(TutorialStepExecution)
                .where(TutorialStepExecution.tutorial_execution_id == execution.id)
                .order_by(TutorialStepExecution.step_order)
            )
        )
        .scalars()
        .all()
    )

    result: dict = {}
    for step in steps:
        if step.output_data:
            result.update(step.output_data)
    return result
