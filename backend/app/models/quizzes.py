from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import text

from ..db.session import Base

class Quiz(Base):
    __tablename__ = "quizzes"

    quiz_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    module_id = Column(
        UUID(as_uuid=True),
        ForeignKey("modules.module_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=False, server_default=text("'MULTIPLE_CHOICE'"))
    options = Column(JSONB)
    correct_answer = Column(Text)