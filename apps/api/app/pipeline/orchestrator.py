"""Phase 3: Pipeline orchestrator with resume support."""

import logging
from typing import Any

from sqlalchemy.orm import Session

from ..models.orchestration import TutorialExecution, TutorialInstance

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Orchestrates the tutorial generation pipeline.

    Features:
    - Resume from last completed step (Phase 3.4)
    - Per-step checkpointing (Phase 3.3)
    - Typed step contracts (Phase 3.1)
    - Automatic registry-based step discovery (Phase 3.2)
    """

    STEP_CLASSES = {
        "analyze_repo": "AnalyzeRepoStep",
        "generate_outline": "GenerateOutlineStep",
        "generate_content": "GenerateContentStep",
        "refine": "RefineStep",
        "save_tutorial": "SaveTutorialStep",
    }

    def __init__(self, tutorial_instance_id: str, db: Session):
        self.tutorial_instance_id = tutorial_instance_id
        self.db = db
        self.execution: TutorialExecution | None = None
        self.instance: TutorialInstance | None = None
        self.current_step_order: int = 0
        self.aggregated_output: dict[str, Any] = {}
        self._step_classes: dict[str, type] | None = None

    async def setup(self) -> None:
        """Initialize execution and check for resume."""
        from sqlalchemy import select

        instance = (
            await self.db.execute(
                select(TutorialInstance).where(
                    TutorialInstance.id == self.tutorial_instance_id,
                )
            )
        ).scalar_one_or_none()

        if not instance:
            raise ValueError(f"Tutorial instance {self.tutorial_instance_id} not found")

        self.instance = instance

        # Find existing execution or create new one
        execution = (
            await self.db.execute(
                select(TutorialExecution).where(
                    TutorialExecution.tutorial_instance_id == instance.id,
                    TutorialExecution.status.in_(["running", "pending"]),
                )
            )
        ).scalar_one_or_none()

        if execution:
            # Resume existing execution
            self.execution = execution
            self.current_step_order = execution.current_step_order
            logger.info(f"Resuming execution {execution.id} from step {self.current_step_order}")
        else:
            # Create new execution
            self.execution = TutorialExecution(
                tutorial_instance_id=instance.id,
                status="running",
                current_step_order=0,
            )
            self.db.add(self.execution)
            await self.db.commit()
            await self.db.refresh(self.execution)
            logger.info(f"Started new execution {self.execution.id}")

        # Update instance status
        instance.status = "running"
        await self.db.commit()

    async def _get_step_classes(self) -> dict[str, type]:
        """Lazy load step classes to avoid circular imports."""
        if self._step_classes is None:
            from .steps import (
                AnalyzeRepoStep,
                GenerateOutlineStep,
                GenerateContentStep,
                RefineStep,
                SaveTutorialStep,
            )

            self._step_classes = {
                "analyze_repo": AnalyzeRepoStep,
                "generate_outline": GenerateOutlineStep,
                "generate_content": GenerateContentStep,
                "refine": RefineStep,
                "save_tutorial": SaveTutorialStep,
            }
        return self._step_classes

    async def get_remaining_steps(self) -> list[str]:
        """Get list of steps that still need to run."""
        # Default step order - can be made configurable
        all_steps = [
            "analyze_repo",
            "generate_outline",
            "generate_content",
            "refine",
            "save_tutorial",
        ]
        # Skip already completed steps
        return all_steps[self.current_step_order:]

    async def execute(self) -> dict[str, Any]:
        """Execute the pipeline, resuming from where it left off."""
        await self.setup()

        remaining_steps = await self.get_remaining_steps()
        logger.info(f"Executing {len(remaining_steps)} remaining steps: {remaining_steps}")

        step_classes = await self._get_step_classes()

        for i, step_type in enumerate(remaining_steps):
            actual_order = self.current_step_order + i + 1
            self.execution.current_step_order = actual_order
            await self.db.commit()

            step = self._create_step(step_type, step_classes)
            step.input_data = self.aggregated_output

            await step.create_execution_record()

            logger.info(f"Executing step: {step_type}")
            try:
                result = await step.execute_with_retry()
                await step.update_execution_record(result)

                # Merge result into aggregated output
                if result.status == "success":
                    self._merge_output(result)
                else:
                    # Record failure at execution level
                    self.execution.error_message = result.error_message
                    await self.db.commit()
                    raise ValueError(f"Step {step_type} failed: {result.error_message}")

            except Exception as e:
                logger.error(f"Step {step_type} failed: {str(e)}")
                self.execution.status = "failed"
                await self.db.commit()
                raise

        # Mark execution complete
        self.execution.status = "completed"
        self.execution.completed_at = self._utcnow()
        self.instance.status = "completed"
        self.instance.updated_at = self._utcnow()
        await self.db.commit()

        logger.info(f"Pipeline complete. Tutorial: {self.aggregated_output.get('tutorial_id')}")
        return self.aggregated_output

    def _create_step(self, step_type: str, step_classes: dict[str, type]) -> Any:
        """Create a step instance."""
        step_class = step_classes.get(step_type)
        if not step_class:
            raise ValueError(f"Unknown step type: {step_type}")
        return step_class(self.execution, self.db)

    def _merge_output(self, result: Any) -> None:
        """Merge step output into aggregated context."""
        output_dict = result.model_dump()
        checkpoint = output_dict.get("checkpoint", {})

        # Merge checkpoint fields
        self.aggregated_output.update(checkpoint)

        # Also merge top-level result fields for backwards compatibility
        for key, value in output_dict.items():
            if key not in ("status", "error_reason", "error_message", "checkpoint"):
                self.aggregated_output[key] = value

    def _utcnow(self):
        from datetime import datetime
        return datetime.utcnow()
