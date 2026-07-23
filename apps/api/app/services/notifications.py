"""Notification service — reading, marking, and creating.

## The feature was dead

`core/notification_service.py` held a perfectly good producer that **nothing
called**. `grep -rn "create_notification" app/` matched only its own definition,
so the table was always empty and the entire notification UI rendered nothing.
Same shape as the quiz feature: the code exists, the wiring does not.

The producer now lives here (it is a service, not `core/` plumbing) and is called
from `workers/tutorial_worker.py`, which is the only place that knows whether a
generation succeeded.

## Sync and async

The API is async; the ARQ worker and orchestrator are still synchronous — that is
Phase 3's conversion, not this slice's. So the producer exists twice over one
shared gate: `create_notification` for the worker, `create_notification_async`
for anything already on an `AsyncSession`. The duplication is small and explicit,
which beats the worker awaiting into a second event loop.
"""

import json
import logging
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ..core.exceptions import NotFoundError
from ..core.pagination import PageParams, paginate
from ..models.enums import NotificationType
from ..models.notifications import Notification
from ..models.user_settings import UserSettings

logger = logging.getLogger(__name__)


# --- Reading ----------------------------------------------------------------


async def list_notifications(
    db: AsyncSession, user_id: UUID, params: PageParams, unread_only: bool = False
) -> tuple[list[Notification], int]:
    stmt = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        stmt = stmt.where(Notification.read.is_(False))

    rows, total = await paginate(db, stmt.order_by(Notification.created_at.desc()), params)
    return list(rows), total


async def unread_count(db: AsyncSession, user_id: UUID) -> int:
    return (
        await db.execute(
            select(func.count(Notification.notification_id)).where(
                Notification.user_id == user_id,
                Notification.read.is_(False),
            )
        )
    ).scalar_one()


# --- Marking ----------------------------------------------------------------


async def mark_read(db: AsyncSession, user_id: UUID, notification_id: UUID) -> Notification:
    """Mark one notification read.

    A single UPDATE scoped by `user_id`, so it cannot touch another account's row
    and there is no read-then-write gap. The 404 comes from the row not existing
    *for this user* — same as everywhere else, never a 403.
    """
    result = await db.execute(
        update(Notification)
        .where(
            Notification.notification_id == notification_id,
            Notification.user_id == user_id,
        )
        .values(read=True, read_at=func.coalesce(Notification.read_at, func.now()))
        .returning(Notification)
    )
    notification = result.scalar_one_or_none()

    if notification is None:
        raise NotFoundError("Notification not found.")

    await db.commit()
    return notification


async def mark_all_read(db: AsyncSession, user_id: UUID) -> int:
    result = await db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.read.is_(False))
        .values(read=True, read_at=func.now())
    )
    await db.commit()
    return result.rowcount or 0


async def delete_notification(db: AsyncSession, user_id: UUID, notification_id: UUID) -> None:
    """Dismiss a notification. There was no way to remove one — the list only
    ever grew."""
    notification = (
        await db.execute(
            select(Notification).where(
                Notification.notification_id == notification_id,
                Notification.user_id == user_id,
            )
        )
    ).scalar_one_or_none()

    if notification is None:
        raise NotFoundError("Notification not found.")

    await db.delete(notification)
    await db.commit()


# --- Creating ---------------------------------------------------------------


def _wants(settings: UserSettings | None, notification_type: NotificationType) -> bool:
    """Whether to persist this notification, per the user's preferences.

    The old producer gated on **`browser_notifications`**, which is the wrong
    switch: that setting is about browser push popups, so turning popups off also
    threw away the stored record and emptied the user's notification history.

    In-app records are gated on the preference for the *event* instead.
    `browser_notifications` is left for whatever actually pushes to a browser.
    """
    if settings is None:
        return True
    if (
        notification_type is NotificationType.SUCCESS
        or notification_type is NotificationType.WARNING
    ):
        return bool(settings.tutorial_completions)
    return True


def _build(
    user_id: UUID,
    title: str,
    message: str,
    notification_type: NotificationType,
    link: str | None,
    metadata: dict | None,
) -> Notification:
    return Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notification_type,
        link=link,
        notification_data=json.dumps(metadata) if metadata else None,
    )


def create_notification(
    db: Session,
    *,
    user_id: UUID,
    title: str,
    message: str,
    notification_type: NotificationType = NotificationType.DEFAULT,
    link: str | None = None,
    metadata: dict | None = None,
) -> Notification | None:
    """Synchronous producer, for the ARQ worker. Returns None if suppressed.

    `user_id` is a `UUID`, not `str | UUID`. The old signature accepted either
    and parsed the string itself, raising a bare `ValueError` on a bad one — from
    inside a background job, where nothing catches it.
    """
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    if not _wants(settings, notification_type):
        return None

    notification = _build(user_id, title, message, notification_type, link, metadata)
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


async def create_notification_async(
    db: AsyncSession,
    *,
    user_id: UUID,
    title: str,
    message: str,
    notification_type: NotificationType = NotificationType.DEFAULT,
    link: str | None = None,
    metadata: dict | None = None,
) -> Notification | None:
    settings = (
        await db.execute(select(UserSettings).where(UserSettings.user_id == user_id))
    ).scalar_one_or_none()
    if not _wants(settings, notification_type):
        return None

    notification = _build(user_id, title, message, notification_type, link, metadata)
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification


def notify_generation_finished(
    db: Session,
    *,
    user_id: UUID,
    repo_name: str,
    tutorial_id: UUID | None = None,
    success: bool = True,
    error_message: str | None = None,
) -> Notification | None:
    """The one event the product actually emits. Called by the worker.

    Never raises: a notification is a nicety, and a failure to record one must
    not fail — or worse, retry — a generation that has already completed.
    """
    if success:
        title = "Tutorial ready"
        message = f"Your tutorial for '{repo_name}' has been generated."
        notification_type = NotificationType.SUCCESS
        link = f"/tutorial/{tutorial_id}" if tutorial_id else None
        metadata = {
            "event": "tutorial_generation_completed",
            "repo_name": repo_name,
            "tutorial_id": str(tutorial_id) if tutorial_id else None,
        }
    else:
        title = "Tutorial generation failed"
        message = f"Generation for '{repo_name}' failed. {error_message or 'Please try again.'}"
        notification_type = NotificationType.WARNING
        link = None
        metadata = {
            "event": "tutorial_generation_failed",
            "repo_name": repo_name,
            "error": error_message,
        }

    try:
        return create_notification(
            db,
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            link=link,
            metadata=metadata,
        )
    except Exception:
        logger.exception("Failed to record notification for user %s", user_id)
        db.rollback()
        return None
