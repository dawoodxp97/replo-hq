from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Boolean, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func, text
from sqlalchemy.orm import relationship

from ..db.session import Base

class TutorialInstance(Base):
    __tablename__ = "tutorial_instances"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    repo_url = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, running, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    executions = relationship("TutorialExecution", back_populates="instance", cascade="all, delete-orphan")

class TutorialExecution(Base):
    __tablename__ = "tutorial_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tutorial_instance_id = Column(UUID(as_uuid=True), ForeignKey("tutorial_instances.id"), nullable=False)
    status = Column(String, default="running") # running, completed, failed
    current_step_order = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    instance = relationship("TutorialInstance", back_populates="executions")
    step_executions = relationship("TutorialStepExecution", back_populates="execution", cascade="all, delete-orphan")

class TutorialStepExecution(Base):
    __tablename__ = "tutorial_step_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tutorial_execution_id = Column(UUID(as_uuid=True), ForeignKey("tutorial_executions.id"), nullable=False)
    step_type = Column(String, nullable=False)
    step_order = Column(Integer, nullable=False)
    status = Column(String, default="pending") # pending, running, completed, failed
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

