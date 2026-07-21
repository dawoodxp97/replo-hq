# ./backend/app/schemas/notifications.py

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: str  # notification_id as string
    title: str
    message: str
    type: str  # success, info, warning, default
    created_at: str  # ISO format datetime
    read: bool
    link: str | None = None

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    notifications: list[NotificationResponse]
    unread_count: int


class MarkAsReadRequest(BaseModel):
    notification_id: str


class MarkAsReadResponse(BaseModel):
    success: bool
    message: str
