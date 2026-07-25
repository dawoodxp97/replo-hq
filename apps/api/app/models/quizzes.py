from sqlalchemy import Column, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import text

from ..db.session import Base
from .enums import QuestionType, enum_column
from .mixins import TimestampMixin


class Quiz(Base, TimestampMixin):
    __tablename__ = "quizzes"

    __table_args__ = (
        # Trigram GIN index for services/search.py (see migration 80e2e03a0776).
        Index(
            "idx_trgm_quiz_question",
            "question_text",
            postgresql_using="gin",
            postgresql_ops={"question_text": "gin_trgm_ops"},
        ),
    )

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
    question_type = Column(
        enum_column(QuestionType, "question_type"),
        nullable=False,
        server_default=QuestionType.MULTIPLE_CHOICE.value,
    )
    options = Column(JSONB)
    correct_answer = Column(Text)
