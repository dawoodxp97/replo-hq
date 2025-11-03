from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func, text

from ..db.session import Base


class TutorialGeneration(Base):
    __tablename__ = "tutorial_generations"

    __table_args__ = (
        Index("idx_gen_repo_user", "repo_id", "user_id"),
        Index("idx_gen_status", "status"),
    )

    generation_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )

    repo_id = Column(
        UUID(as_uuid=True),
        ForeignKey("repositories.repo_id", ondelete="CASCADE"),
        nullable=False,
    )

    # Repository URL for quick lookup
    repo_url = Column(String(255), nullable=False)

    # Generation parameters
    difficulty = Column(String(50), nullable=False)  # beginner, intermediate, advanced
    focus_areas = Column(JSON, nullable=True)  # Array of focus area strings
    description = Column(Text, nullable=True)  # Additional context

    # Generation status tracking
    status = Column(String(50), nullable=False, server_default=text("'PENDING'"))
    # PENDING, CLONING, ANALYZING, PROCESSING, GENERATING, COMPLETED, FAILED

    # Progress tracking (0-100)
    generation_step = Column(Integer, nullable=False, server_default=text("0"))
    # 0: Initializing, 1: Cloning, 2: Analyzing, 3: Processing, 4: Generating

    generation_progress = Column(Integer, nullable=False, server_default=text("0"))
    # 0-100 percentage

    # Error tracking
    error_message = Column(Text, nullable=True)

    # Tutorial ID once generation is complete
    tutorial_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tutorials.tutorial_id", ondelete="SET NULL"),
        nullable=True,
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

