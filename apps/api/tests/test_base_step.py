"""Unit tests for the step base class: retry/backoff, retention caps, usage.

No DB, no network — `Step` is exercised through a stub subclass, with the
execution-record methods kept out of the paths under test.
"""

import pytest

from app.core.exceptions import InvalidInputError
from app.pipeline.base_step import Step
from app.pipeline.contracts import BaseStepOutput, StepFailureReason


class _StubStep(Step):
    """Concrete enough to run `execute_with_retry`; no DB touched."""

    def __init__(self, outcomes=None, **kwargs):
        super().__init__(execution=None, db=None, input_data={})
        self._outcomes = list(outcomes or [])

    async def _execute_impl(self) -> BaseStepOutput:
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


@pytest.fixture(autouse=True)
def _no_backoff_sleep(monkeypatch):
    """Backoff delays are production behaviour (1s/2s/4s); tests must not wait."""
    import asyncio

    async def _instant(_seconds):
        return None

    monkeypatch.setattr(asyncio, "sleep", _instant)


class TestRetryAndBackoff:
    async def test_transient_failure_is_retried_and_succeeds(self, monkeypatch):
        delays = []
        import asyncio

        async def _capture(seconds):
            delays.append(seconds)

        monkeypatch.setattr(asyncio, "sleep", _capture)
        step = _StubStep(
            outcomes=[RuntimeError("connection timeout"), BaseStepOutput(status="success")]
        )
        result = await step.execute_with_retry()

        assert result.status == "success"
        assert delays == [1.0]  # first backoff: BASE_DELAY * 2^0

    async def test_backoff_doubles_between_attempts(self, monkeypatch):
        delays = []
        import asyncio

        async def _capture(seconds):
            delays.append(seconds)

        monkeypatch.setattr(asyncio, "sleep", _capture)
        step = _StubStep(
            outcomes=[
                RuntimeError("429"),
                RuntimeError("429"),
                BaseStepOutput(status="success"),
            ]
        )
        result = await step.execute_with_retry()

        assert result.status == "success"
        assert delays == [1.0, 2.0]

    async def test_permanent_failure_returns_failed_output(self):
        step = _StubStep(outcomes=[RuntimeError("boom")] * 10)
        result = await step.execute_with_retry()

        assert result.status == "failed"
        assert result.error_reason == StepFailureReason.INTERNAL
        assert "boom" in result.error_message

    async def test_failure_reason_categorisation(self):
        cases = {
            "HTTP 429 slow down": StepFailureReason.LLM_RATE_LIMITED,
            "connection reset": StepFailureReason.LLM_API_ERROR,
            "invalid json returned": StepFailureReason.LLM_INVALID_JSON,
            "repository not found": StepFailureReason.REPO_NOT_FOUND,
            "unauthorized": StepFailureReason.CREDENTIAL_INVALID,
        }
        for message, expected in cases.items():
            step = _StubStep(outcomes=[RuntimeError(message)] * 10)
            result = await step.execute_with_retry()
            assert result.error_reason == expected, message


class TestRetentionCaps:
    def test_small_payload_round_trips_intact(self, monkeypatch):
        monkeypatch.setattr("app.core.config.settings.step_data_max_bytes", 10_000)
        step = _StubStep()
        data = {"key": "value", "nested": {"list": [1, 2, 3]}}
        assert step._serialize_for_db(data) == data

    def test_oversized_payload_is_replaced_by_marker(self, monkeypatch):
        monkeypatch.setattr("app.core.config.settings.step_data_max_bytes", 64)
        step = _StubStep()
        big = {"content": "x" * 10_000}
        stored = step._serialize_for_db(big)

        # The content itself is gone — that is the point of the cap.
        assert stored["truncated"] is True
        assert stored["original_bytes"] > 64
        assert stored["max_bytes"] == 64
        assert "xxxxx" not in str(stored)

    def test_no_preview_of_oversized_content(self, monkeypatch):
        # The truncation marker must not carry a preview: step data is repo
        # source and LLM output, and a preview re-introduces the bytes the cap
        # exists to bound.
        monkeypatch.setattr("app.core.config.settings.step_data_max_bytes", 32)
        step = _StubStep()
        stored = step._serialize_for_db({"secret_content": "y" * 5_000})
        assert "yyyyy" not in str(stored)

    def test_api_key_never_survives_serialisation(self):
        step = _StubStep()
        stored = step._serialize_for_db({"repo_url": "x", "api_key": "sk-or-v1-abc123"})
        assert "api_key" not in stored

    def test_self_referential_payload_does_not_recurse_forever(self):
        # Step input can reference the aggregated context; a cycle must be
        # broken by the deep-copy guard, not blow the stack.
        step = _StubStep()
        circular: dict = {}
        circular["self"] = circular
        assert step._serialize_for_db(circular) == {"self": None}


class TestAIUsageCapture:
    async def test_usage_accumulates_across_calls(self):
        step = _StubStep()

        class _FakeClient:
            model = "openai/gpt-4o-mini"
            calls = 0

            async def send_message(self, messages, **kwargs):
                usage = [
                    {"input_tokens": 10, "output_tokens": 5},
                    {"input_tokens": 7, "output_tokens": 3},
                ][self.calls]
                self.calls += 1
                self.last_usage = usage
                return "ok"

        # Assigned directly — Step.__init__ sets the instance attribute to None,
        # which is what `_call_ai` reads.
        step._ai_client = _FakeClient()

        await step._call_ai([{"role": "user", "content": "hi"}])
        await step._call_ai([{"role": "user", "content": "hi"}])

        assert step.usage == {"input_tokens": 17, "output_tokens": 8}

    async def test_missing_usage_is_tolerated(self):
        step = _StubStep()

        class _NoUsageClient:
            model = "m"

            async def send_message(self, messages, **kwargs):
                return "ok"

        step._ai_client = _NoUsageClient()
        await step._call_ai([{"role": "user", "content": "hi"}])
        assert step.usage == {"input_tokens": 0, "output_tokens": 0}


class TestCostEstimation:
    def test_known_model_estimates_from_rates(self):
        from app.pipeline.prompts import estimate_cost_usd

        cost = estimate_cost_usd("openai/gpt-4o-mini", 1_000_000, 1_000_000)
        assert cost == round(0.15 + 0.60, 6)

    def test_unknown_model_is_none_not_zero(self):
        from app.pipeline.prompts import estimate_cost_usd

        # None, not 0.0: "we don't know" must not be stored as "this was free".
        assert estimate_cost_usd("unknown/model", 1000, 1000) is None

    def test_missing_usage_is_none(self):
        from app.pipeline.prompts import estimate_cost_usd

        assert estimate_cost_usd("openai/gpt-4o-mini", None, None) is None

    def test_free_model_costs_zero(self):
        from app.pipeline.prompts import estimate_cost_usd

        assert estimate_cost_usd("kwaipilot/kat-coder-pro:free", 1000, 2000) == 0.0


class TestErrorTypes:
    def test_invalid_input_is_an_app_error(self):
        # Steps raise service-layer errors, never HTTPException.
        from app.core.exceptions import AppError

        assert issubclass(InvalidInputError, AppError)
