from typing import Any

from ..orchestrator.step import Step


class RefineTutorialStep(Step):
    """Refines and polishes the tutorial content"""

    SYSTEM_PROMPT = "You are an expert editor. Improve clarity, flow, and technical accuracy."

    async def execute(self) -> dict[str, Any]:
        modules = self.input_data.get("modules", [])
        refined_modules = []

        for module in modules:
            content = module["content"]
            title = module["title"]

            refined_content = await self._refine_content(title, content)

            # Create a copy to update
            new_module = module.copy()
            new_module["content"] = refined_content
            refined_modules.append(new_module)

        return {"modules": refined_modules}

    async def _refine_content(self, title: str, content: str) -> str:
        prompt_data = {"title": title, "content": content}

        template = self.step_config.prompt_template
        if template == "Default prompt":
            template = """
Review and refine the following tutorial chapter: "{title}".

**Content:**
{content}

**Instructions:**
- Improve clarity and readability.
- Fix any grammatical errors.
- Ensure code snippets are properly formatted.
- Make it engaging.
- Return ONLY the refined Markdown.
"""

        prompt = template.format(**prompt_data)

        messages = [
            {"role": "system", "content": self.step_config.system_prompt or self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        response = await self.call_ai(messages)
        return response
