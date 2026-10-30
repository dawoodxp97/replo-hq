"""Phase 3: Base step implementation with retry logic and checkpointing.

Also owns two Phase 6 concerns that apply to *every* step, which is why they
live here rather than in each subclass:

- **Retention caps (3.13).** `_serialize_for_db` is the single write path for
  `TutorialStepExecution.input_data`/`output_data`; the byte cap is applied there
  once, not re-implemented per step.
- **AI delegation + token usage.** `_call_ai` routes every LLM call through one
  lazily-created `AIClient` per step and records the provider-reported token
  usage, which the orchestrator rolls up onto the execution record (Phase 6
  cost tracking, D7: visibility only).
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
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
        db: AsyncSession,
        input_data: dict[str, Any] | None = None,
    ):
        self.execution = execution
        self.db = db
        self.input = self._parse_input(input_data or {})
        self.output: BaseStepOutput | None = None
        self.step_execution_record: TutorialStepExecution | None = None
        self.step_type: str = self.__class__.__name__.replace("Step", "").lower()
        self.retry_count: int = 0
        # Token usage reported by the provider across this step's LLM calls.
        self.usage: dict[str, int] = {"input_tokens": 0, "output_tokens": 0}
        self._ai_client: Any = None

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
        await self.db.commit()
        await self.db.refresh(self.step_execution_record)

    async def update_execution_record(self, result: BaseStepOutput) -> None:
        """Update the step execution record with results."""
        if not self.step_execution_record:
            return

        # The contract vocabulary ("success") is not the DB enum vocabulary
        # ("completed") — RunStatus has no "success". Mapped here, at the single
        # write point, so step classes keep their contract values and the row
        # stores what the enum allows.
        self.step_execution_record.status = (
            "completed" if result.status == "success" else result.status
        )
        self.step_execution_record.output_data = self._serialize_for_db(result.model_dump())
        # Provider-reported usage for this step. Zero-valued (rather than NULL)
        # when the provider reported nothing, so "no data" and "no tokens used"
        # stay distinguishable in queries.
        self.step_execution_record.input_tokens = self.usage["input_tokens"]
        self.step_execution_record.output_tokens = self.usage["output_tokens"]

        if result.error_message:
            self.step_execution_record.error_message = result.error_message

        if result.status in ("completed", "failed"):
            self.step_execution_record.completed_at = self._utcnow()

        await self.db.commit()
        await self.db.refresh(self.step_execution_record)

    def _serialize_for_db(self, data: dict[str, Any]) -> dict[str, Any]:
        """Serialize data for database storage.

        Two independent guards, applied once here because this is the only write
        path for step data (Phase 6, retention caps):

        1. Sensitive-field filtering — the credential never enters step context
           (D9); filtering is the seatbelt behind that structural guarantee.
        2. **Byte cap.** Serialized JSON over `settings.step_data_max_bytes` is
           replaced by a truncation marker. There is no preview on purpose: the
           oversized payloads are repo source code and LLM output, which is
           exactly the content "never log input data" exists for, and a preview
           would quietly re-introduce the bytes the cap exists to bound.
        """
        filtered = self._filter_sensitive(data)

        try:
            blob = json.dumps(filtered, default=str)
        except (TypeError, ValueError):
            # Unserializable object somewhere in the payload: keep the shape of
            # the marker consistent so readers only ever handle two shapes.
            return self._truncation_marker(0)

        size = len(blob.encode("utf-8"))
        if size > settings.step_data_max_bytes:
            return self._truncation_marker(size)
        return filtered

    def _truncation_marker(self, original_bytes: int) -> dict[str, Any]:
        return {
            "truncated": True,
            "original_bytes": original_bytes,
            "max_bytes": settings.step_data_max_bytes,
        }

    def _filter_sensitive(self, data: Any, _path: set[int] | None = None) -> Any:
        """Deep-copy `data`, dropping `api_key` keys at any depth.

        `_path` holds the ids of containers on the current recursion path so a
        self-referential payload (step input can reference the aggregated
        context) terminates instead of recursing forever.
        """
        seen = _path if _path is not None else set()
        if isinstance(data, (dict, list)):
            if id(data) in seen:
                return None
            seen = seen | {id(data)}

        if isinstance(data, dict):
            return {k: self._filter_sensitive(v, seen) for k, v in data.items() if k != "api_key"}
        if isinstance(data, list):
            return [self._filter_sensitive(item, seen) for item in data]
        return data

    # --- AI delegation (shared by every step; was copy-pasted four times) ----

    def _get_ai_client(self):
        """One AIClient per step instance, created lazily so importing a step
        never constructs HTTP machinery."""
        if self._ai_client is None:
            from ..ai.client import AIClient

            self._ai_client = AIClient()
        return self._ai_client

    async def _call_ai(self, messages: list[dict], **kwargs) -> str:
        """Delegate to AIClient and capture the provider-reported token usage."""
        client = self._get_ai_client()
        response = await client.send_message(messages, **kwargs)
        usage = getattr(client, "last_usage", None)
        if usage:
            self.usage["input_tokens"] += usage.get("input_tokens") or 0
            self.usage["output_tokens"] += usage.get("output_tokens") or 0
        return response

    def _parse_json_response(self, response: str) -> dict[str, Any]:
        import json
        import re

        match = re.search(r"```(?:json)?\s*(.*?)```", response, re.DOTALL)
        json_str = match.group(1).strip() if match else response.strip()
        return json.loads(json_str)

    def _utcnow(self):
        """Return current UTC datetime."""
        from datetime import datetime

        return datetime.utcnow()
