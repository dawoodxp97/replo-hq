from sqlalchemy import Column, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text

from ..db.session import Base
from .mixins import TimestampMixin


class Module(Base, TimestampMixin):
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
    __table_args__ = (Index("idx_module_tutorial", "tutorial_id"),)
