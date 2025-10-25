from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func, text

from ..db.session import Base


class UserProgress(Base):
    __tablename__ = "user_progress"

    progress_id = Column(
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

    module_id = Column(
        UUID(as_uuid=True),
        ForeignKey("modules.module_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    completed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    quiz_score = Column(Integer)

    __table_args__ = (
        UniqueConstraint("user_id", "module_id", name="uq_user_module"),
        Index("idx_progress_user_module", "user_id", "module_id"),
    )