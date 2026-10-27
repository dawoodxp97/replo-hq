"""Phase 3: Base step implementation with retry logic and checkpointing."""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.orm import Session

from ..models.orchestration import TutorialExecution, TutorialStepExecution
from .contracts import (
    BaseStepInput,
    BaseStepOutput,
    StepFailureReason,
)

logger = logging.getLogger(__name__)


class Step(ABC):
    """Base class for all pipeline steps.

    Features:
    - Typed input/output via Pydantic
    - Automatic step execution record creation
    - Retry logic with backoff for transient failures
    - Checkpoint support for resume functionality
    """

    MAX_RETRIES = 3
    BASE_DELAY_SECONDS = 1.0

    def __init__(
        self,
        execution: TutorialExecution,
        db: Session,
        input_data: dict[str, Any] | None = None,
    ):
        self.execution = execution
        self.db = db
        self.input = self._parse_input(input_data or {})
        self.output: BaseStepOutput | None = None
        self.step_execution_record: TutorialStepExecution | None = None
        self.step_type: str = self.__class__.__name__.replace("Step", "").lower()
        self.retry_count: int = 0

    def _parse_input(self, data: dict[str, Any]) -> BaseStepInput:
        """Parse input dict into typed input model. Override in subclasses."""
        return BaseStepInput(**data)

    def _parse_output(self, data: dict[str, Any]) -> BaseStepOutput:
        """Parse output dict into typed output model. Override in subclasses."""
        return BaseStepOutput(**data)

    @abstractmethod
    async def _execute_impl(self) -> BaseStepOutput:
        """Execute the step's core logic. Must return a BaseStepOutput."""
        pass

    async def execute_with_retry(self) -> BaseStepOutput:
        """Execute with retry logic for transient failures."""
        last_error: str | None = None
        last_reason: StepFailureReason | None = None

        while self.retry_count < self.MAX_RETRIES:
            try:
                return await self._execute_impl()
            except Exception as e:
                last_error = str(e)
                last_reason = self._categorize_error(e)

                self.retry_count += 1
                if self.retry_count < self.MAX_RETRIES:
                    delay = self.BASE_DELAY_SECONDS * (2 ** (self.retry_count - 1))
                    logger.warning(
                        f"Step {self.step_type} failed (attempt {self.retry_count}/{self.MAX_RETRIES}): "
                        f"{last_reason.value} - {last_error}. Retrying in {delay:.1f}s..."
                    )
                    import asyncio
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Step {self.step_type} failed permanently after {self.MAX_RETRIES} attempts: "
                        f"{last_reason.value} - {last_error}"
                    )

        # All retries exhausted
        return BaseStepOutput(
            status="failed",
            error_reason=last_reason,
            error_message=last_error,
        )

    def _categorize_error(self, e: Exception) -> StepFailureReason:
        """Categorize an error for retry decisions."""
        error_str = str(e).lower()

        if "rate limit" in error_str or "429" in error_str:
            return StepFailureReason.LLM_RATE_LIMITED
        elif "timeout" in error_str or "connection" in error_str:
            return StepFailureReason.LLM_API_ERROR
        elif "invalid json" in error_str or "parse error" in error_str:
            return StepFailureReason.LLM_INVALID_JSON
        elif "not found" in error_str or "404" in error_str:
            return StepFailureReason.REPO_NOT_FOUND
        elif "too large" in error_str or "size" in error_str:
            return StepFailureReason.REPO_TOO_LARGE
        elif "permission" in error_str or "unauthorized" in error_str:
            return StepFailureReason.CREDENTIAL_INVALID
        elif "invalid" in error_str or "expired" in error_str:
            return StepFailureReason.CREDENTIAL_EXPIRED

        return StepFailureReason.INTERNAL

    async def create_execution_record(self) -> None:
        """Create the database record for this step execution."""
        self.step_execution_record = TutorialStepExecution(
            tutorial_execution_id=self.execution.id,
            step_type=self.step_type,
            step_order=self.execution.current_step_order,
            status="running",
            input_data=self._serialize_for_db(self.input.model_dump()),
            started_at=self._utcnow(),
        )
        self.db.add(self.step_execution_record)
        self.db.commit()
        self.db.refresh(self.step_execution_record)

    async def update_execution_record(self, result: BaseStepOutput) -> None:
        """Update the step execution record with results."""
        if not self.step_execution_record:
            return

        self.step_execution_record.status = result.status
        self.step_execution_record.output_data = self._serialize_for_db(result.model_dump())

        if result.error_message:
            self.step_execution_record.error_message = result.error_message

        if result.status in ("completed", "failed"):
            self.step_execution_record.completed_at = self._utcnow()

        self.db.commit()
        self.db.refresh(self.step_execution_record)

    def _serialize_for_db(self, data: dict[str, Any]) -> dict[str, Any]:
        """Serialize data for database storage, filtering sensitive fields."""
        # Deep copy and filter sensitive fields
        def filter_sensitive(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {k: filter_sensitive(v) for k, v in obj.items() if k != "api_key"}
            elif isinstance(obj, list):
                return [filter_sensitive(item) for item in obj]
            return obj

        return filter_sensitive(data)

    def _utcnow(self):
        """Return current UTC datetime."""
        from datetime import datetime

        return datetime.utcnow()
