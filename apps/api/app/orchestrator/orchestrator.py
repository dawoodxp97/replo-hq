import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from ..models.orchestration import TutorialExecution, TutorialInstance
from .agent import TutorialAgent

logger = logging.getLogger(__name__)


class TutorialOrchestrator:
    def __init__(self, tutorial_instance_id: uuid.UUID, db: Session):
        self.tutorial_instance_id = tutorial_instance_id
        self.db = db
        self.agent = None
        self.execution = None

    async def setup(self):
        # Get instance
        instance = (
            self.db.query(TutorialInstance)
            .filter(TutorialInstance.id == self.tutorial_instance_id)
            .first()
        )
        if not instance:
            raise ValueError(f"Tutorial instance {self.tutorial_instance_id} not found")

        # Create execution record
        self.execution = TutorialExecution(tutorial_instance_id=instance.id, status="running")
        self.db.add(self.execution)
        self.db.commit()
        self.db.refresh(self.execution)

        # Update instance status
        instance.status = "running"
        self.db.commit()

        # Initialize Agent
        self.agent = TutorialAgent(self.execution, self.db)

    async def execute(self) -> dict[str, Any]:
        try:
            await self.setup()

            steps = await self.agent.get_steps()

            previous_output = {}
            # Add repo_url to initial input
            previous_output["repo_url"] = self.execution.instance.repo_url

            for i, step_instance in enumerate(steps):
                # Update current step order in execution
                self.execution.current_step_order = i + 1
                self.db.commit()

                # Pass previous output as input
                step_instance.input_data = previous_output

                await step_instance.validate()
                await step_instance.create_step_execution_record()

                logger.info(f"Executing step: {step_instance.step_type}")
                try:
                    result = await step_instance.execute()
                    await step_instance.update_step_execution_record(
                        status="completed", output_data=result
                    )

                    # Update previous_output with result.
                    # We merge it so context accumulates.
                    if isinstance(result, dict):
                        previous_output.update(result)

                except Exception as e:
                    logger.error(f"Step {step_instance.step_type} failed: {str(e)}")
                    await step_instance.update_step_execution_record(
                        status="failed", error_message=str(e)
                    )
                    raise e  # Stop execution

            await self.agent.mark_execution_complete()
            return previous_output

        except Exception as e:
            logger.error(f"Orchestration failed: {str(e)}")
            if self.agent:
                await self.agent.mark_execution_failed(str(e))
            raise e
