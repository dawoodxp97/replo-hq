from typing import Any

from ..orchestrator.step import Step


class GenerateTutorialContentStep(Step):
    """Generates content for each chapter in the outline"""

    SYSTEM_PROMPT = (
        "You are an expert technical instructor. Write clear, code-focused tutorial content."
    )

    async def execute(self) -> dict[str, Any]:
        outline = self.input_data
        key_files_content = self.input_data.get("key_files_content", "")

        chapters = outline.get("chapters", [])
        generated_content = []

        # Process chapters sequentially
        for i, chapter in enumerate(chapters):
            chapter_title = chapter.get("title")
            sections = chapter.get("sections", [])

            # Generate content for this chapter
            content = await self._generate_chapter_content(
                chapter_title, sections, key_files_content
            )

            generated_content.append({"title": chapter_title, "content": content, "order": i})

        return {"modules": generated_content}

    async def _generate_chapter_content(self, title: str, sections: list[str], context: str) -> str:
        prompt_data = {
            "chapter_title": title,
            "sections": ", ".join(sections) if isinstance(sections, list) else str(sections),
            "repo_context": context,
        }

        template = self.step_config.prompt_template
        if template == "Default prompt":
            template = """
Write a comprehensive tutorial chapter.

**Chapter Title:** {chapter_title}
**Sections to Cover:** {sections}

**Context (Key Files):**
{repo_context}

**Instructions:**
- Write in Markdown.
- Explain the concepts clearly.
- Use code snippets from the context where relevant.
- Keep it practical and hands-on.
"""

        prompt = template.format(**prompt_data)

        messages = [
            {"role": "system", "content": self.step_config.system_prompt or self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        response = await self.call_ai(messages)
        return response
