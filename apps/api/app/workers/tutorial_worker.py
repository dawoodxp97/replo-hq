import logging
import sys
import uuid

from ..db.session import SessionLocal
from ..orchestrator.orchestrator import TutorialOrchestrator

# Ensure logger is configured
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


async def generate_tutorial_task(ctx, tutorial_instance_id: str):
    """ARQ background task for tutorial generation"""
    logger.info(f"[TASK START] Starting tutorial generation for instance {tutorial_instance_id}")

    db = SessionLocal()
    try:
        # Convert string to UUID
        instance_uuid = uuid.UUID(tutorial_instance_id)

        orchestrator = TutorialOrchestrator(tutorial_instance_id=instance_uuid, db=db)
        result = await orchestrator.execute()
        logger.info(
            f"[TASK COMPLETE] Tutorial generation completed for instance {tutorial_instance_id}"
        )
        return result
    except Exception as e:
        logger.error(
            f"[TASK FAILED] Tutorial generation failed for instance {tutorial_instance_id}: {str(e)}"
        )
        import traceback

        logger.error(traceback.format_exc())
        # Orchestrator handles DB status updates on failure
        raise e
    finally:
        db.close()
