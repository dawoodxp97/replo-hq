"""Phase 3: ARQ task using the new PipelineOrchestrator.

Runs on an **async** session (AsyncSessionLocal) — the orchestrator and steps
issue `await`ed ORM calls, so a sync Session here would break at the first
`await self.db.execute(...)`. This flips the last sync-session caller of the
pipeline; `SessionLocal` survives only for legacy code outside it.

The task also publishes step transitions to Redis pub/sub (see
app/pipeline/events.py) so the SSE stream endpoint can forward them live, and
records the repository's primary language for the /explore filter.
"""

import logging
import uuid

from sqlalchemy import select

from ..db.session import AsyncSessionLocal
from ..models.orchestration import TutorialInstance
from ..models.repositories import Repository
from ..models.tutorials import Tutorial
from ..pipeline import PipelineOrchestrator
from ..services import notifications as notification_service

logger = logging.getLogger(__name__)


async def _notify(db, instance_id: uuid.UUID, *, success: bool, error: str | None = None) -> None:
    """Record the completion notification."""
    instance = (
        await db.execute(select(TutorialInstance).where(TutorialInstance.id == instance_id))
    ).scalar_one_or_none()
    if instance is None:
        return

    repo = (
        await db.execute(
            select(Repository).where(
                Repository.github_url == instance.repo_url,
                Repository.user_id == instance.user_id,
            )
        )
    ).scalar_one_or_none()

    tutorial_id = None
    if success and repo is not None:
        tutorial = (
            await db.execute(
                select(Tutorial)
                .filter(Tutorial.repo_id == repo.repo_id)
                .order_by(Tutorial.generated_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        tutorial_id = tutorial.tutorial_id if tutorial else None

    await notification_service.notify_generation_finished(
        db,
        user_id=instance.user_id,
        repo_name=repo.name if repo else instance.repo_url.rstrip("/").split("/")[-1],
        tutorial_id=tutorial_id,
        success=success,
        error_message=error,
    )


async def _record_language(db, instance_id: str, result: dict) -> None:
    """Store the analyzed primary language on the Repository row.

    /explore filters on `Repository.language` (Phase 5.5). The pipeline learns
    the language in the analyze step; this is the one place that both sees the
    result and knows which Repository row the run belongs to.
    """
    analysis = result.get("analysis") or {}
    language = analysis.get("primary_language") if isinstance(analysis, dict) else None
    if not language:
        return

    instance = (
        await db.execute(select(TutorialInstance).where(TutorialInstance.id == instance_id))
    ).scalar_one_or_none()
    if instance is None:
        return

    repo = (
        await db.execute(
            select(Repository).where(
                Repository.github_url == instance.repo_url,
                Repository.user_id == instance.user_id,
            )
        )
    ).scalar_one_or_none()
    if repo is not None and repo.language != language:
        repo.language = str(language)[:100]
        await db.commit()


async def generate_tutorial_task(ctx, tutorial_instance_id: str):
    """Run the generation pipeline for one TutorialInstance."""
    logger.info("Starting tutorial generation for instance %s", tutorial_instance_id)

    instance_uuid = uuid.UUID(tutorial_instance_id)
    redis_pool = ctx.get("redis")
    async with AsyncSessionLocal() as db:
        orchestrator = PipelineOrchestrator(
            tutorial_instance_id=str(instance_uuid),
            db=db,
            redis_pool=redis_pool,
        )
        try:
            result = await orchestrator.execute()
            logger.info("Tutorial generation completed for instance %s", tutorial_instance_id)
            await _record_language(db, tutorial_instance_id, result)
            await _notify(db, instance_uuid, success=True)
            return result
        except Exception as exc:
            logger.exception("Tutorial generation failed for instance %s", tutorial_instance_id)
            await _notify(db, instance_uuid, success=False, error=str(exc))
            raise
