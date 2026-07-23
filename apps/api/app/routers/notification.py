"""Notification endpoints.

**Route order matters.** `PUT /read-all` is declared before `PUT /{id}/read`;
they do not currently collide (different segment counts), but adding a
`PUT /{id}` later would shadow it.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.dependencies import get_current_user_async
from ..core.pagination import Page, PageParams, page_params
from ..db.session import get_async_db
from ..models.user import User
from ..schemas.notifications import (
    MarkAsReadResponse,
    NotificationResponse,
    UnreadCountResponse,
)
from ..services import notifications as notification_service

router = APIRouter()


@router.get("", response_model=Page[NotificationResponse])
async def list_notifications(
    unread_only: bool = Query(default=False),
    params: PageParams = Depends(page_params),
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """Newest first. `limit` is capped at 100 — it was an unbounded `int`."""
    rows, total = await notification_service.list_notifications(
        db, current_user.user_id, params, unread_only
    )
    return Page[NotificationResponse].build(
        [NotificationResponse.model_validate(r) for r in rows], total, params
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """Split out of the list response so a polling bell badge costs one count
    query instead of a page of notification bodies."""
    return UnreadCountResponse(
        unread_count=await notification_service.unread_count(db, current_user.user_id)
    )


@router.put("/read-all", response_model=MarkAsReadResponse)
async def mark_all_read(
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    return MarkAsReadResponse(
        updated=await notification_service.mark_all_read(db, current_user.user_id)
    )


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """`notification_id` is a `UUID` path parameter, so a malformed id is a 422
    from FastAPI. The old handler took a `str`, parsed it by hand, and wrapped
    everything in a `try/except Exception` that returned `str(e)` to the client."""
    return await notification_service.mark_read(db, current_user.user_id, notification_id)


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
) -> None:
    """Dismiss. Previously the list could only grow."""
    await notification_service.delete_notification(db, current_user.user_id, notification_id)
