from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text

from ..db.session import Base
from .enums import RunStatus, enum_column
from .mixins import TimestampMixin


class TutorialInstance(Base, TimestampMixin):
    __tablename__ = "tutorial_instances"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    repo_url = Column(String, nullable=False)
    status = Column(
        enum_column(RunStatus, "run_status"),
        nullable=False,
        server_default=RunStatus.PENDING.value,
    )

    executions = relationship(
        "TutorialExecution", back_populates="instance", cascade="all, delete-orphan"
    )


class TutorialExecution(Base):
    __tablename__ = "tutorial_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    # ondelete CASCADE is required, not tidiness. The ORM relationship's
    # `cascade="all, delete-orphan"` only fires when SQLAlchemy walks the
    # relationship itself — deleting a *user* cascades to tutorial_instances in
    # the database, which never loads these rows, so without this the FK aborts
    # the whole transaction. Account deletion failed for anyone who had ever run
    # a generation.
    tutorial_instance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tutorial_instances.id", ondelete="CASCADE"),
        nullable=False,
    )
    status = Column(
        enum_column(RunStatus, "run_status"),
        nullable=False,
        server_default=RunStatus.PENDING.value,
    )
    current_step_order = Column(Integer, nullable=False, server_default=text("0"))
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    # Phase 3.6: the failure reason was only ever recorded on the step row, so a
    # failed run gave no top-level explanation.
    error_message = Column(Text, nullable=True)

    instance = relationship("TutorialInstance", back_populates="executions")
    step_executions = relationship(
        "TutorialStepExecution", back_populates="execution", cascade="all, delete-orphan"
    )


class TutorialStepExecution(Base):
    __tablename__ = "tutorial_step_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tutorial_execution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tutorial_executions.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_type = Column(String, nullable=False)
    step_order = Column(Integer, nullable=False)
    status = Column(
        enum_column(RunStatus, "run_status"),
        nullable=False,
        server_default=RunStatus.PENDING.value,
    )
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    prompt_used = Column(Text, nullable=True)
    llm_response = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    execution = relationship("TutorialExecution", back_populates="step_executions")


class TutorialStepConfig(Base):
    __tablename__ = "tutorial_step_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    step_type = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    prompt_template = Column(Text, nullable=False)
    system_prompt = Column(Text, nullable=True)
    model_name = Column(String, nullable=True)
    max_tokens = Column(Integer, nullable=True)
    temperature = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
