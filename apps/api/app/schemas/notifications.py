"""Notification schemas.

The old models typed everything as `str` — `id`, `type` and `created_at` — with
`str(...)` and `.isoformat()` called by hand at the one construction site.
Pydantic serialises UUIDs, enums and datetimes on its own, and typing them
properly is what lets a generated client know a date is a date.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from ..models.enums import NotificationType


class NotificationResponse(BaseModel):
    # Was `id: str`. Renamed to match the column — the `id` alias existed only
    # because the value was being stringified by hand.
    notification_id: UUID
    title: str
    message: str
    type: NotificationType
    created_at: datetime
    read: bool
    read_at: datetime | None = None
    link: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UnreadCountResponse(BaseModel):
    """Its own endpoint so a bell badge can poll the count without pulling a
    page of notification bodies every few seconds."""

    unread_count: int


class MarkAsReadResponse(BaseModel):
    updated: int
