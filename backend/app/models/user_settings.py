# ./backend/app/models/user_settings.py
from sqlalchemy import Column, String, Boolean, Integer, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text
from sqlalchemy.orm import relationship

from ..db.session import Base


class UserSettings(Base):
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
        index=True
    )
    
    # Profile Settings
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
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
    default_difficulty_level = Column(String, default="beginner")  # beginner, intermediate, advanced
    daily_learning_goal = Column(Integer, default=10)  # minutes or modules
    auto_play_next_module = Column(Boolean, default=True)
    show_code_hints = Column(Boolean, default=True)
    quiz_mode = Column(Boolean, default=True)
    
    # Relationship
    user = relationship("User", back_populates="settings")
