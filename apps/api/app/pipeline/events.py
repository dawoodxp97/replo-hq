"""Generation progress events, published from the worker to Redis pub/sub.

The worker is the producer; `GET /api/tutorial/{id}/stream` (SSE) is the
consumer. Pub/sub, not a Redis stream or list: subscribers are ephemeral SSE
connections that only care about transitions happening *while they are
connected*, and the polling status endpoint remains the source of truth for
anything missed before connecting. Fire-and-forget is exactly the semantics we
want — nobody replays step events.

Publishing never raises into the pipeline: a failed publish must not fail a
generation that cost real LLM tokens. It is logged and dropped.
"""

import json
import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

CHANNEL_PREFIX = "generation:"

# Event types. A step transition emits `step_started`/`step_completed`;
# `completed`/`failed` are terminal and close the stream.
STEP_STARTED = "step_started"
STEP_COMPLETED = "step_completed"
STEP_FAILED = "step_failed"
COMPLETED = "completed"
FAILED = "failed"

TERMINAL_EVENTS = frozenset({COMPLETED, FAILED})


def channel_for(instance_id: str) -> str:
    return f"{CHANNEL_PREFIX}{instance_id}"


async def publish_generation_event(
    redis_pool,
    instance_id: str,
    event_type: str,
    *,
    step: str | None = None,
    step_order: int | None = None,
    step_status: str | None = None,
    error_message: str | None = None,
) -> None:
    """Push one transition to the instance's channel. Best-effort by design."""
    if redis_pool is None:
        return

    payload: dict[str, Any] = {
        "type": event_type,
        "instance_id": instance_id,
        "at": datetime.now(UTC).isoformat(),
    }
    if step is not None:
        payload["step"] = step
    if step_order is not None:
        payload["step_order"] = step_order
    if step_status is not None:
        payload["step_status"] = step_status
    if error_message is not None:
        payload["error_message"] = error_message

    try:
        await redis_pool.publish(channel_for(instance_id), json.dumps(payload))
    except Exception:
        # Never let telemetry break the run it is describing.
        logger.exception("Failed to publish %s event for instance %s", event_type, instance_id)
