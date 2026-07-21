from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func, text

from ..db.session import Base

class Module(Base):
    __tablename__ = "modules"

    module_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    tutorial_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tutorials.tutorial_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title = Column(String(255), nullable=False)
    order_index = Column(Integer, nullable=False)
    content_markdown = Column(Text, nullable=False)
    file_path = Column(String(255))
    code_snippet = Column(Text)
    diagram_mermaid = Column(Text)

    # Performance index on tutorial_id
    __table_args__ = (
        Index("idx_module_tutorial", "tutorial_id"),
    )