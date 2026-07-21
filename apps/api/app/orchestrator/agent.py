from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from ..models.orchestration import TutorialExecution, TutorialStepConfig
from ..steps.analyze_repo import AnalyzeRepoStructureStep
from ..steps.generate_content import GenerateTutorialContentStep
from ..steps.generate_outline import GenerateTutorialOutlineStep
from ..steps.refine_tutorial import RefineTutorialStep
from ..steps.save_tutorial import SaveTutorialStep
from .step import Step


class TutorialAgent:
    def __init__(self, execution: TutorialExecution, db: Session):
        self.execution = execution
        self.db = db
        self.steps: list[Step] = []
        self.context: dict[str, Any] = {}  # Shared context between steps

    async def get_steps(self) -> list[Step]:
        """
        Determines which steps to run and initializes them.
        """
        # Order:
        # 1. analyze_repo_structure
        # 2. generate_tutorial_outline
        # 3. generate_tutorial_content
        # 4. refine_tutorial
        # 5. save_tutorial

        step_types = [
            "analyze_repo_structure",
            "generate_tutorial_outline",
            "generate_tutorial_content",
            "refine_tutorial",
            "save_tutorial",
        ]

        steps = []
        for step_type in step_types:
            config = self.db.query(TutorialStepConfig).filter_by(step_type=step_type).first()

            # If config doesn't exist, we might need to create a default one or error out.
            # For now, let's assume we need to create defaults if they don't exist to avoid blocking.
            if not config:
                config = self._create_default_config(step_type)

            # Factory to create step instance
            step_instance = self.create_step_instance(step_type, config)
            if step_instance:
                steps.append(step_instance)

        self.steps = steps
        return steps

    def create_step_instance(self, step_type: str, config: TutorialStepConfig) -> Step | None:
        # Pass self.context so steps can read/write to it if needed,
        # but currently Step receives initial_input.
        # The Orchestrator loop will feed output of one step to input of next.

        if step_type == "analyze_repo_structure":
            return AnalyzeRepoStructureStep(self.execution, config, self.db)
        elif step_type == "generate_tutorial_outline":
            return GenerateTutorialOutlineStep(self.execution, config, self.db)
        elif step_type == "generate_tutorial_content":
            return GenerateTutorialContentStep(self.execution, config, self.db)
        elif step_type == "refine_tutorial":
            return RefineTutorialStep(self.execution, config, self.db)
        elif step_type == "save_tutorial":
            return SaveTutorialStep(self.execution, config, self.db)

        return None

    def _create_default_config(self, step_type: str) -> TutorialStepConfig:
        # Helper to create default config if missing
        config = TutorialStepConfig(
            step_type=step_type,
            name=step_type.replace("_", " ").title(),
            description=f"Default config for {step_type}",
            prompt_template="Default prompt",
            system_prompt="You are a helpful assistant.",
            model_name="kwaipilot/kat-coder-pro:free",
            is_active=True,
        )
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    async def mark_execution_complete(self):
        self.execution.status = "completed"
        self.execution.completed_at = datetime.utcnow()
        self.execution.instance.status = "completed"
        self.execution.instance.updated_at = datetime.utcnow()
        self.db.commit()

    async def mark_execution_failed(self, error: str):
        self.execution.status = "failed"
        self.execution.instance.status = "failed"
        self.execution.instance.updated_at = datetime.utcnow()
        self.db.commit()
