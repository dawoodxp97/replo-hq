"""ARQ task: run the generation pipeline for one TutorialInstance."""

import logging
import uuid

from ..db.session import SessionLocal
from ..models.orchestration import TutorialInstance
from ..models.repositories import Repository
from ..models.tutorials import Tutorial
from ..orchestrator.orchestrator import TutorialOrchestrator
from ..services import notifications as notification_service

# Was a module-level `logging.basicConfig(...)`. It happened to be a no-op —
# `worker.py` calls `configure_logging()` before importing this module, and
# basicConfig returns early when the root logger already has handlers — but it is
# a landmine: any import-order change would let it seize the root logger and drop
# the redaction filter in the one process that actually handles API keys. Gone.
logger = logging.getLogger(__name__)


def _notify(db, instance_id: uuid.UUID, *, success: bool, error: str | None = None) -> None:
    """Record the completion notification.

    This is the wiring that was missing entirely: `create_notification` existed
    and was called from nowhere, so the notifications table stayed empty and the
    whole UI rendered nothing. This is the only event that produces one.
    """
    instance = db.query(TutorialInstance).filter(TutorialInstance.id == instance_id).first()
    if instance is None:
        return

    repo = (
        db.query(Repository)
        .filter(
            Repository.github_url == instance.repo_url,
            Repository.user_id == instance.user_id,
        )
        .first()
    )

    tutorial_id = None
    if success and repo is not None:
        tutorial = (
            db.query(Tutorial)
            .filter(Tutorial.repo_id == repo.repo_id)
            .order_by(Tutorial.generated_at.desc())
            .first()
        )
        tutorial_id = tutorial.tutorial_id if tutorial else None

    notification_service.notify_generation_finished(
        db,
        user_id=instance.user_id,
        repo_name=repo.name if repo else instance.repo_url.rstrip("/").split("/")[-1],
        tutorial_id=tutorial_id,
        success=success,
        error_message=error,
    )


async def generate_tutorial_task(ctx, tutorial_instance_id: str):
    logger.info("Starting tutorial generation for instance %s", tutorial_instance_id)

    instance_uuid = uuid.UUID(tutorial_instance_id)
    db = SessionLocal()
    try:
        orchestrator = TutorialOrchestrator(tutorial_instance_id=instance_uuid, db=db)
        result = await orchestrator.execute()
        logger.info("Tutorial generation completed for instance %s", tutorial_instance_id)
        _notify(db, instance_uuid, success=True)
        return result
    except Exception as exc:
        # exception() already emits the traceback; the old code logged the
        # message and then `traceback.format_exc()` as a second record.
        logger.exception("Tutorial generation failed for instance %s", tutorial_instance_id)
        # The orchestrator owns the DB status transitions; this only adds the
        # user-visible notification.
        _notify(db, instance_uuid, success=False, error=str(exc))
        raise
    finally:
        db.close()
