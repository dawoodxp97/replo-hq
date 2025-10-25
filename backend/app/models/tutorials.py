



from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func, text

from ..db.session import Base


class Tutorial(Base):
    __tablename__ = "tutorials"

    __table_args__ = (
        Index("idx_tutorial_repo", "repo_id"),
    )

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

    level = Column(String(50), nullable=False)  # BEGINNER, INTERMEDIATE, ADVANCED
    title = Column(String(255), nullable=False)
    overview = Column(Text)
    overview_diagram_mermaid = Column(Text)  # For the main dependency graph

    generated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )


