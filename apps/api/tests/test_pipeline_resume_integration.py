"""Integration tests: pipeline checkpointing, resume and cost rollup.

Marked `integration` — needs real Postgres (testcontainers). Skipped
automatically when Docker is unavailable (see conftest).
"""

import uuid

import pytest
from sqlalchemy import select

from app.models.orchestration import (
    TutorialExecution,
    TutorialInstance,
    TutorialStepExecution,
)
from app.models.user import User
from app.pipeline.base_step import Step
from app.pipeline.contracts import BaseStepInput, BaseStepOutput
from app.pipeline.orchestrator import PipelineOrchestrator

pytestmark = pytest.mark.integration

ALL_STEPS = [
    "analyze_repo",
    "generate_outline",
    "generate_content",
    "refine",
    "save_tutorial",
]


async def _seed_instance(db) -> tuple[User, TutorialInstance]:
    user = User(email=f"{uuid.uuid4().hex[:10]}@example.com")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    instance = TutorialInstance(user_id=user.user_id, repo_url="https://github.com/a/b")
    db.add(instance)
    await db.commit()
    await db.refresh(instance)
    return user, instance


@pytest.fixture()
def stub_steps(monkeypatch):
    """Swap the real (LLM-calling) steps for stubs, without touching them."""
    ran = []

    classes = {}
    for name in ALL_STEPS:

        class _FakeModelClient:
            model = "openai/gpt-4o-mini"  # in MODEL_REGISTRY, so cost is estimable

        def _make_execute(step_name):
            async def _execute_impl(self):
                ran.append(step_name)
                self.usage["input_tokens"] += 10
                self.usage["output_tokens"] += 5
                # What the real steps do implicitly: a client exists once a
                # call has been made; its model is what the cost rollup prices.
                self._ai_client = _FakeModelClient()
                return BaseStepOutput(status="success", checkpoint={"completed": step_name})

            return _execute_impl

        cls = type(
            name.replace("_", " ").title().replace(" ", "_") + "Step",
            (Step,),
            {
                "_parse_input": lambda self, data: BaseStepInput(**data),
                "_parse_output": lambda self, data: BaseStepOutput(**data),
                "_execute_impl": _make_execute(name),
            },
        )
        classes[name] = cls

    async def _get_step_classes(self):
        return classes

    monkeypatch.setattr(PipelineOrchestrator, "_get_step_classes", _get_step_classes)
    return ran


class TestCheckpointing:
    async def test_step_record_written_after_each_step(self, db, stub_steps):
        _, instance = await _seed_instance(db)
        orchestrator = PipelineOrchestrator(str(instance.id), db)

        await orchestrator.execute()

        records = (
            (
                await db.execute(
                    select(TutorialStepExecution).order_by(TutorialStepExecution.step_order)
                )
            )
            .scalars()
            .all()
        )
        assert [r.step_type for r in records] == ALL_STEPS
        # "success" in contract vocabulary maps to the RunStatus value "completed".
        assert all(r.status == "completed" for r in records)
        # The checkpoint contract: every step persisted its output + usage.
        assert all(r.output_data["checkpoint"] == {"completed": r.step_type} for r in records)
        assert all(r.input_tokens == 10 and r.output_tokens == 5 for r in records)


class TestResume:
    async def test_resume_skips_completed_steps(self, db, stub_steps):
        """A run interrupted after step 2 must not re-run steps 1-2.

        This is the worker-crash scenario: the execution row survives with
        status=running and current_step_order=2; the next job picks it up from
        there.
        """
        _, instance = await _seed_instance(db)
        execution = TutorialExecution(
            tutorial_instance_id=instance.id,
            status="running",
            current_step_order=2,
        )
        db.add(execution)
        await db.commit()

        orchestrator = PipelineOrchestrator(str(instance.id), db)
        await orchestrator.execute()

        assert stub_steps == ["generate_content", "refine", "save_tutorial"]
        assert execution.status == "completed"
        assert execution.current_step_order == 5

    async def test_fresh_run_executes_every_step(self, db, stub_steps):
        _, instance = await _seed_instance(db)
        orchestrator = PipelineOrchestrator(str(instance.id), db)
        await orchestrator.execute()
        assert stub_steps == ALL_STEPS


class TestCostRollup:
    async def test_usage_and_cost_recorded_on_execution(self, db, stub_steps):
        _, instance = await _seed_instance(db)
        orchestrator = PipelineOrchestrator(str(instance.id), db)
        await orchestrator.execute()

        await db.refresh(orchestrator.execution)
        execution = orchestrator.execution
        # 5 steps x (10 in, 5 out)
        assert execution.input_tokens == 50
        assert execution.output_tokens == 25
        # Default model rate from MODEL_REGISTRY; a real number, not None, and
        # not zero unless the configured model is free-tier.
        assert execution.estimated_cost_usd is not None

    async def test_unknown_model_leaves_cost_null(self, db, stub_steps, monkeypatch):
        from app.pipeline import orchestrator as orch_module

        async def _get_step_classes(self):
            classes = {}
            for name in ALL_STEPS:

                def _make(step_name):
                    async def _execute_impl(self):
                        self.usage["input_tokens"] += 10
                        self.usage["output_tokens"] += 5
                        return BaseStepOutput(status="success")

                    return _execute_impl

                classes[name] = type(
                    name.replace("_", " ").title().replace(" ", "_") + "Step",
                    (Step,),
                    {
                        "_parse_input": lambda self, data: BaseStepInput(**data),
                        "_parse_output": lambda self, data: BaseStepOutput(**data),
                        "_execute_impl": _make(name),
                    },
                )
            return classes

        monkeypatch.setattr(
            orch_module.PipelineOrchestrator, "_get_step_classes", _get_step_classes
        )

        _, instance = await _seed_instance(db)
        orchestrator = PipelineOrchestrator(str(instance.id), db)
        await orchestrator.execute()

        await db.refresh(orchestrator.execution)
        # Tokens are known; the cost is not estimable without a registered
        # model, and None must be stored rather than a fabricated 0.0.
        assert orchestrator.execution.input_tokens == 50
        assert orchestrator.execution.estimated_cost_usd is None


class TestFailure:
    async def test_failed_step_marks_execution_failed(self, db, monkeypatch):
        """The failure path: execution failed + error recorded, not silently
        left 'running'."""
        ran = []
        classes = {}
        for name in ALL_STEPS:

            def _make(step_name):
                async def _execute_impl(self):
                    ran.append(step_name)
                    if step_name == "generate_content":
                        raise RuntimeError("LLM exploded")
                    return BaseStepOutput(status="success")

                return _execute_impl

            classes[name] = type(
                name.replace("_", " ").title().replace(" ", "_") + "Step",
                (Step,),
                {
                    "_parse_input": lambda self, data: BaseStepInput(**data),
                    "_parse_output": lambda self, data: BaseStepOutput(**data),
                    "_execute_impl": _make(name),
                },
            )

        async def _get_step_classes(self):
            return classes

        monkeypatch.setattr(PipelineOrchestrator, "_get_step_classes", _get_step_classes)

        _, instance = await _seed_instance(db)
        orchestrator = PipelineOrchestrator(str(instance.id), db)

        with pytest.raises(ValueError, match="generate_content"):
            await orchestrator.execute()

        await db.refresh(orchestrator.execution)
        assert orchestrator.execution.status == "failed"
        assert "LLM exploded" in (orchestrator.execution.error_message or "")
        # The two steps before the failure are checkpointed; a manual repair
        # can resume from them. generate_content appears MAX_RETRIES times —
        # the retry loop ran it three times before giving up.
        assert ran == ["analyze_repo", "generate_outline"] + ["generate_content"] * 3
