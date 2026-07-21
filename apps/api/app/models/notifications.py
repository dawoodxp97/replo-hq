# ./backend/app/models/notifications.py
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text

from ..db.session import Base
from .enums import NotificationType, enum_column


class Notification(Base):
    __tablename__ = "notifications"

    __table_args__ = (
        Index("idx_notif_user_created", "user_id", "created_at"),
        Index("idx_notif_user_read", "user_id", "read"),
    )

    notification_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(
        enum_column(NotificationType, "notification_type"),
        nullable=False,
        server_default=NotificationType.DEFAULT.value,
    )

    read = Column(Boolean, nullable=False, server_default=text("false"))
    read_at = Column(DateTime(timezone=True), nullable=True)

    # Optional link to navigate to when clicking notification
    link = Column(String(500), nullable=True)

    # Optional notification data stored as JSON (e.g., tutorial_id, repo_id, etc.)
    # Note: Using 'notification_data' instead of 'metadata' as 'metadata' is reserved by SQLAlchemy
    notification_data = Column(Text, nullable=True)  # Stored as JSON string

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationship
    user = relationship("User", back_populates="notifications")
