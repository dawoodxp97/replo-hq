from typing import Any

from ..orchestrator.step import Step


class GenerateTutorialOutlineStep(Step):
    """Generates a tutorial outline based on repo analysis"""

    SYSTEM_PROMPT = "You are an expert technical writer. Create a comprehensive tutorial outline."

    async def execute(self) -> dict[str, Any]:
        # 1. Get input data
        # Input data contains everything from previous steps merged
        repo_analysis = {
            k: v
            for k, v in self.input_data.items()
            if k in ["entry_points", "core_features", "architecture_pattern", "tutorial_flow"]
        }

        # 2. Prepare prompt data
        prompt_data = {
            "repo_analysis": self._format_json_for_prompt(repo_analysis),
            "response_format": """
            {
                "title": "Tutorial Title",
                "estimated_duration": "30 mins",
                "chapters": [
                    {
                        "title": "Chapter 1",
                        "sections": ["Section 1.1", "Section 1.2"]
                    }
                ]
            }
            """,
        }

        # 3. Get template
        template = self.step_config.prompt_template
        if template == "Default prompt":
            template = """
Based on the following repository analysis, create a structured tutorial outline.

**Repository Analysis:**
{repo_analysis}

**Task:**
Create a step-by-step tutorial that guides a developer through building or understanding this project.
Structure it into logical chapters and sections.

Respond in JSON format:
{response_format}
"""

        prompt = template.format(**prompt_data)

        # 4. Call AI
        messages = [
            {"role": "system", "content": self.step_config.system_prompt or self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        response = await self.call_ai(messages, response_format={"type": "json_object"})

        # 5. Parse response
        return self.parse_ai_response(response)
