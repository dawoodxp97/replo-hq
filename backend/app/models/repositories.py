from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func, text

from ..db.session import Base

class Repository(Base):
    __tablename__ = "repositories"

    __table_args__ = (
        Index("idx_repo_user", "user_id"),
    )

    repo_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )

    github_url = Column(String(255), unique=True, nullable=False)
    name = Column(String(255))
    description = Column(Text)

    # PENDING, ANALYZING, COMPLETED, FAILED
    status = Column(String(50), nullable=False, server_default=text("'PENDING'"))

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )