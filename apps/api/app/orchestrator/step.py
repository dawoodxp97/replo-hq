import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from ..ai.client import AIClient
from ..models.orchestration import TutorialExecution, TutorialStepConfig, TutorialStepExecution


class Step(ABC):
    def __init__(
        self,
        execution: TutorialExecution,
        step_config: TutorialStepConfig,
        db: Session,
        initial_input: dict[str, Any] = None,
    ):
        self.execution = execution
        self.step_config = step_config
        self.db = db
        self.input_data = initial_input or {}
        self.output_data = None
        self.step_execution_record: TutorialStepExecution | None = None
        self.step_type = step_config.step_type

    @abstractmethod
    async def execute(self) -> dict[str, Any]:
        """
        Execute the step logic.
        Should return the output data.
        """
        pass

    async def validate(self) -> bool:
        """
        Validate input data before execution.
        """
        return True

    async def create_step_execution_record(self):
        """Creates the database record for this step execution"""
        self.step_execution_record = TutorialStepExecution(
            tutorial_execution_id=self.execution.id,
            step_type=self.step_type,
            step_order=self.execution.current_step_order,
            status="running",
            input_data=self.input_data,
            prompt_used=self.step_config.prompt_template,  # Initial snapshot
            started_at=datetime.utcnow(),
        )
        self.db.add(self.step_execution_record)
        self.db.commit()
        self.db.refresh(self.step_execution_record)

    async def update_step_execution_record(
        self,
        status: str = None,
        output_data: dict = None,
        error_message: str = None,
        llm_response: str = None,
    ):
        """Updates the database record"""
        if not self.step_execution_record:
            return

        if status:
            self.step_execution_record.status = status
            if status in ["completed", "failed"]:
                self.step_execution_record.completed_at = datetime.utcnow()

        if output_data:
            self.step_execution_record.output_data = output_data
        if error_message:
            self.step_execution_record.error_message = error_message
        if llm_response:
            self.step_execution_record.llm_response = llm_response

        self.db.commit()
        self.db.refresh(self.step_execution_record)

    def _format_json_for_prompt(self, data: Any) -> str:
        return json.dumps(data, indent=2)

    async def call_ai(self, messages: list[dict], **kwargs) -> str:
        client = AIClient()
        config_model = self.step_config.model_name
        config_temp = self.step_config.temperature
        config_tokens = self.step_config.max_tokens

        # Override defaults with config if present, then kwargs
        model = kwargs.get("model", config_model)
        temperature = kwargs.get("temperature", config_temp)
        max_tokens = kwargs.get("max_tokens", config_tokens)

        response = await client.send_message(
            messages=messages, model=model, temperature=temperature, max_tokens=max_tokens
        )
        return response

    def parse_ai_response(self, response: str) -> dict[str, Any]:
        client = AIClient()
        return client.parse_json_response(response)
