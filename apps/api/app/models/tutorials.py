from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func, text

from ..db.session import Base
from .enums import TutorialLevel, enum_column


class Tutorial(Base):
    __tablename__ = "tutorials"

    __table_args__ = (Index("idx_tutorial_repo", "repo_id"),)

    tutorial_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    repo_id = Column(
        UUID(as_uuid=True),
        ForeignKey("repositories.repo_id", ondelete="CASCADE"),
        nullable=False,
    )

    level = Column(
        enum_column(TutorialLevel, "tutorial_level"),
        nullable=False,
        server_default=TutorialLevel.INTERMEDIATE.value,
    )

    title = Column(String(255), nullable=False)
    overview = Column(Text)
    overview_diagram_mermaid = Column(Text)  # For the main dependency graph

    # `generated_at` is domain-meaningful (when the pipeline produced this), so it
    # stays rather than being folded into TimestampMixin's created_at. `updated_at`
    # is added separately so authoring edits are distinguishable from generation.
    generated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
