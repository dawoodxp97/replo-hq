# ./backend/app/models/user_settings.py
from sqlalchemy import JSON, Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text

from ..db.session import Base
from .enums import TutorialLevel, enum_column
from .mixins import TimestampMixin


class UserSettings(Base, TimestampMixin):
    __tablename__ = "user_settings"

    settings_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # Profile Settings
    bio = Column(String, nullable=True)
    location = Column(String, nullable=True)
    website = Column(String, nullable=True)
    profile_picture_url = Column(String, nullable=True)

    # Connected Accounts (stored as JSON)
    connected_accounts = Column(JSON, nullable=True, default=list)

    # Notification Settings
    email_notifications_enabled = Column(Boolean, default=True)
    tutorial_completions = Column(Boolean, default=True)
    new_features = Column(Boolean, default=True)
    weekly_digest = Column(Boolean, default=True)
    browser_notifications = Column(Boolean, default=True)

    # Appearance Settings
    language = Column(String, default="en")
    code_editor_theme = Column(String, default="github-dark")

    # Learning Settings
    # Same vocabulary as Tutorial.level — a user's default and a tutorial's
    # actual level are the same concept and must not drift apart.
    default_difficulty_level = Column(
        enum_column(TutorialLevel, "tutorial_level"),
        nullable=False,
        server_default=TutorialLevel.BEGINNER.value,
    )
    daily_learning_goal = Column(Integer, default=10)  # minutes or modules
    auto_play_next_module = Column(Boolean, default=True)
    show_code_hints = Column(Boolean, default=True)
    quiz_mode = Column(Boolean, default=True)

    # Relationship
    user = relationship("User", back_populates="settings")
