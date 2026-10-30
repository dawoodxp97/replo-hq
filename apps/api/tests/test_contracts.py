"""Unit tests for the step contracts and registry (Phase 3.1/3.2)."""

import pytest
from pydantic import ValidationError

from app.pipeline import registry
from app.pipeline.base_step import Step
from app.pipeline.contracts import (
    AnalyzeRepoStepInput,
    AnalyzeRepoStepOutput,
    BaseStepInput,
    BaseStepOutput,
    StepFailureReason,
)
from app.pipeline.prompts import GENERATE_OUTLINE_USER


class TestBaseContracts:
    def test_base_input_defaults_are_none(self):
        parsed = BaseStepInput()
        assert parsed.repo_url is None
        assert parsed.instance_id is None
        assert parsed.user_id is None

    def test_step_input_rejects_wrong_types(self):
        with pytest.raises(ValidationError):
            AnalyzeRepoStepInput(repo_url=123, instance_id="x")

    def test_output_defaults_to_success(self):
        out = BaseStepOutput()
        assert out.status == "success"
        assert out.error_reason is None
        assert out.checkpoint == {}

    def test_failure_reason_values_are_stable(self):
        # These strings are persisted in the step execution rows and read by
        # the retry logic; renaming one is a data migration, not a rename.
        assert StepFailureReason.LLM_RATE_LIMITED.value == "llm_rate_limited"
        assert StepFailureReason.REPO_TOO_LARGE.value == "repo_too_large"

    def test_str_enum_serialises_as_string(self):
        # StepFailureReason lands in JSON payloads and DB columns; it must
        # behave as its value string, not as an enum repr.
        assert f"{StepFailureReason.INTERNAL}" == "internal"
        assert StepFailureReason.INTERNAL.value == "internal"


class TestRegistry:
    def test_default_order_is_the_five_step_chain(self):
        assert registry.DEFAULT_STEP_ORDER == [
            "analyze_repo",
            "generate_outline",
            "generate_content",
            "refine",
            "save_tutorial",
        ]

    def test_unknown_step_type_has_no_class(self):
        assert registry.get_step_class("does_not_exist") is None
        assert registry.get_step_contract("does_not_exist") is None

    def test_register_step_roundtrip(self):
        class _FakeStep(Step):
            async def _execute_impl(self):
                return BaseStepOutput()

        @registry.register_step("test_only_step", AnalyzeRepoStepInput, AnalyzeRepoStepOutput)
        class _Registered(_FakeStep):
            pass

        try:
            assert registry.get_step_class("test_only_step") is _Registered
            in_cls, out_cls = registry.get_step_contract("test_only_step")
            assert in_cls is AnalyzeRepoStepInput
            assert out_cls is AnalyzeRepoStepOutput
        finally:
            # Leave the global registries exactly as we found them — tests share
            # the process-wide dict.
            registry.STEP_REGISTRY.pop("test_only_step", None)
            registry.STEP_CONTRACTS.pop("test_only_step", None)


class TestPrompts:
    def test_template_survives_braces_in_repo_code(self):
        # The reason for string.Template: repo source code is interpolated into
        # prompts and is full of `{}`. str.format would explode on it.
        out = GENERATE_OUTLINE_USER.substitute(
            repo_analysis='{"nested": {"json": True}}',
            response_format="{}",
        )
        assert '{"nested": {"json": True}}' in out

    def test_missing_placeholder_raises_key_error(self):
        # Deliberate: a typo'd placeholder must fail loudly at generation time,
        # not silently render an unfilled `$variable` into the prompt.
        import string

        template = string.Template("hello $name")
        import pytest

        with pytest.raises(KeyError):
            template.substitute({})
