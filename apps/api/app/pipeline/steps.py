"""Phase 3: Step implementations."""

import asyncio
import logging
import shutil
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from ..core.exceptions import InvalidInputError
from ..models.orchestration import TutorialExecution
from ..utils.repo_utils import (
    build_file_tree,
    clone_repository,
    normalise_repo_url,
    read_file,
    repo_name_from_url,
)
from .base_step import Step
from .contracts import (
    AnalyzeRepoStepInput,
    AnalyzeRepoStepOutput,
    GenerateContentStepInput,
    GenerateContentStepOutput,
    GenerateOutlineStepInput,
    GenerateOutlineStepOutput,
    RefineStepInput,
    RefineStepOutput,
    SaveTutorialStepInput,
    SaveTutorialStepOutput,
    RepoAnalysis,
    TutorialOutline,
    OutlineChapter,
    GeneratedModule,
    TutorialSaveResult,
)
from .prompts import (
    ANALYZE_REPO_SYSTEM,
    ANALYZE_REPO_USER,
    GENERATE_OUTLINE_SYSTEM,
    GENERATE_OUTLINE_USER,
    GENERATE_CONTENT_SYSTEM,
    GENERATE_CONTENT_USER,
    REFINE_SYSTEM,
    REFINE_USER,
)

logger = logging.getLogger(__name__)


class AnalyzeRepoStep(Step):
    """Analyzes repository structure and identifies key components."""

    def _parse_input(self, data: dict[str, Any]) -> AnalyzeRepoStepInput:
        return AnalyzeRepoStepInput(**data)

    def _parse_output(self, data: dict[str, Any]) -> AnalyzeRepoStepOutput:
        return AnalyzeRepoStepOutput(**data)

    async def _execute_impl(self) -> AnalyzeRepoStepOutput:
        repo_url = self.input.repo_url
        instance_id = self.input.instance_id

        if not repo_url:
            raise InvalidInputError("repo_url is required for AnalyzeRepoStep")
        if not instance_id:
            raise InvalidInputError("instance_id is required for AnalyzeRepoStep")

        # Clone repository
        repo_url = normalise_repo_url(repo_url)
        import uuid
        repo_path = await clone_repository(repo_url, uuid.UUID(instance_id))

        # Build file tree
        file_tree = build_file_tree(repo_path)

        # Identify and read key files
        key_files = self._identify_key_files(file_tree)
        key_files_content = ""

        for file in key_files[:5]:
            try:
                content, _size = read_file(repo_path, file["path"])
                key_files_content += f"\n--- {file['path']} ---\n{content[:2000]}\n"
            except InvalidInputError:
                continue

        # Build prompt data
        repo_name = repo_name_from_url(repo_url)
        prompt_data = {
            "repo_name": repo_name,
            "primary_language": "Unknown",
            "repo_description": "A GitHub repository",
            "file_tree": str(file_tree),
            "key_files_content": key_files_content,
            "response_format": """{
    "entry_points": ["file1", "file2"],
    "core_features": ["feature1", "feature2"],
    "architecture_pattern": "description",
    "tutorial_flow": [{"step": "1", "description": "..."}]
}""",
        }

        # Call AI
        messages = [
            {"role": "system", "content": str(ANALYZE_REPO_SYSTEM)},
            {"role": "user", "content": str(ANALYZE_REPO_USER.substitute(prompt_data))},
        ]

        response = await self._call_ai(messages, response_format={"type": "json_object"})
        parsed = self._parse_json_response(response)

        return AnalyzeRepoStepOutput(
            analysis=RepoAnalysis(
                entry_points=parsed.get("entry_points", []),
                core_features=parsed.get("core_features", []),
                architecture_pattern=parsed.get("architecture_pattern", ""),
                tutorial_flow=parsed.get("tutorial_flow", []),
                primary_language=parsed.get("primary_language", "Unknown"),
                repo_description=parsed.get("repo_description", ""),
            ),
            repo_path=str(repo_path),
            key_files_content=key_files_content,
            file_tree=file_tree,
        )

    def _identify_key_files(self, tree: list[dict]) -> list[dict]:
        """Priority-ordered file discovery."""
        queue = tree.copy()
        files = []
        while queue:
            node = queue.pop(0)
            if node["type"] == "file":
                files.append(node)
            elif node.get("children"):
                queue.extend(node["children"])

        priority = [
            "readme.md", "main.py", "index.js", "app.py", "server.js",
            "package.json", "requirements.txt", "Cargo.toml", "go.mod",
        ]

        def score(file):
            name = file["name"].lower()
            for i, p in enumerate(priority):
                if p in name:
                    return i
            return 100

        return sorted(files, key=score)

    async def _call_ai(self, messages: list[dict], **kwargs) -> str:
        """Delegate to AIClient."""
        from ..ai.client import AIClient
        client = AIClient()
        return await client.send_message(messages, **kwargs)

    def _parse_json_response(self, response: str) -> dict[str, Any]:
        """Parse JSON from AI response."""
        import json
        import re
        match = re.search(r"```(?:json)?\s*(.*?)```", response, re.DOTALL)
        json_str = match.group(1).strip() if match else response.strip()
        return json.loads(json_str)


class GenerateOutlineStep(Step):
    """Generates a tutorial outline based on repo analysis."""

    def _parse_input(self, data: dict[str, Any]) -> GenerateOutlineStepInput:
        return GenerateOutlineStepInput(**data)

    def _parse_output(self, data: dict[str, Any]) -> GenerateOutlineStepOutput:
        return GenerateOutlineStepOutput(**data)

    async def _execute_impl(self) -> GenerateOutlineStepOutput:
        analysis_data = self.input.analysis.model_dump() if self.input.analysis else {}

        prompt_data = {
            "repo_analysis": str(analysis_data),
            "response_format": """{
    "title": "Tutorial Title",
    "estimated_duration": "30 mins",
    "chapters": [
        {
            "title": "Chapter 1",
            "sections": ["Section 1.1", "Section 1.2"]
        }
    ]
}""",
        }

        messages = [
            {"role": "system", "content": str(GENERATE_OUTLINE_SYSTEM)},
            {
                "role": "user",
                "content": str(GENERATE_OUTLINE_USER.substitute(prompt_data)),
            },
        ]

        response = await self._call_ai(messages, response_format={"type": "json_object"})
        parsed = self._parse_json_response(response)

        return GenerateOutlineStepOutput(
            outline=TutorialOutline(
                title=parsed.get("title", "Tutorial"),
                estimated_duration=parsed.get("estimated_duration", "30 mins"),
                chapters=[
                    OutlineChapter(
                        title=c.get("title", f"Chapter {i+1}"),
                        sections=c.get("sections", []),
                    )
                    for i, c in enumerate(parsed.get("chapters", []))
                ],
            ),
        )

    async def _call_ai(self, messages: list[dict], **kwargs) -> str:
        from ..ai.client import AIClient
        return await AIClient().send_message(messages, **kwargs)

    def _parse_json_response(self, response: str) -> dict[str, Any]:
        import json
        import re
        match = re.search(r"```(?:json)?\s*(.*?)```", response, re.DOTALL)
        json_str = match.group(1).strip() if match else response.strip()
        return json.loads(json_str)


class GenerateContentStep(Step):
    """Generates content for each chapter in the outline."""

    def _parse_input(self, data: dict[str, Any]) -> GenerateContentStepInput:
        return GenerateContentStepInput(**data)

    def _parse_output(self, data: dict[str, Any]) -> GenerateContentStepOutput:
        return GenerateContentStepOutput(**data)

    async def _execute_impl(self) -> GenerateContentStepOutput:
        outline = self.input.outline
        key_files_content = self.input.key_files_content

        if not outline:
            return GenerateContentStepOutput()

        generated = []
        for i, chapter in enumerate(outline.chapters):
            content = await self._generate_chapter_content(
                chapter.title, chapter.sections, key_files_content
            )
            generated.append(GeneratedModule(title=chapter.title, content=content, order=i))

        return GenerateContentStepOutput(modules=generated)

    async def _generate_chapter_content(
        self, title: str, sections: list[str], context: str
    ) -> str:
        prompt_data = {
            "chapter_title": title,
            "sections": ", ".join(sections),
            "repo_context": context[:10000] if context else "",
        }

        messages = [
            {"role": "system", "content": str(GENERATE_CONTENT_SYSTEM)},
            {
                "role": "user",
                "content": str(GENERATE_CONTENT_USER.substitute(prompt_data)),
            },
        ]

        response = await self._call_ai(messages)
        return response

    async def _call_ai(self, messages: list[dict], **kwargs) -> str:
        from ..ai.client import AIClient
        return await AIClient().send_message(messages, **kwargs)


class RefineStep(Step):
    """Refines and polishes the tutorial content."""

    def _parse_input(self, data: dict[str, Any]) -> RefineStepInput:
        return RefineStepInput(**data)

    def _parse_output(self, data: dict[str, Any]) -> RefineStepOutput:
        return RefineStepOutput(**data)

    async def _execute_impl(self) -> RefineStepOutput:
        modules = self.input.modules
        refined = []

        for module in modules:
            refined_content = await self._refine_content(module.title, module.content)
            refined.append(GeneratedModule(title=module.title, content=refined_content, order=module.order))

        return RefineStepOutput(modules=refined)

    async def _refine_content(self, title: str, content: str) -> str:
        prompt_data = {"title": title, "content": content[:8000]}

        messages = [
            {"role": "system", "content": str(REFINE_SYSTEM)},
            {
                "role": "user",
                "content": str(REFINE_USER.substitute(prompt_data)),
            },
        ]

        response = await self._call_ai(messages)
        return response

    async def _call_ai(self, messages: list[dict], **kwargs) -> str:
        from ..ai.client import AIClient
        return await AIClient().send_message(messages, **kwargs)


class SaveTutorialStep(Step):
    """Saves the generated tutorial to the database atomically."""

    def _parse_input(self, data: dict[str, Any]) -> SaveTutorialStepInput:
        return SaveTutorialStepInput(**data)

    def _parse_output(self, data: dict[str, Any]) -> SaveTutorialStepOutput:
        return SaveTutorialStepOutput(**data)

    async def _execute_impl(self) -> SaveTutorialStepOutput:
        from ..models.modules import Module
        from ..models.repositories import Repository
        from ..models.tutorials import Tutorial
        from sqlalchemy import select

        title = self.input.title or "Generated Tutorial"
        overview = self.input.overview
        modules_data = self.input.modules
        user_id = self.input.user_id
        repo_id = self.input.repo_id

        if not user_id:
            raise InvalidInputError("user_id is required for SaveTutorialStep")

        # Find the associated tutorial execution's instance
        instance = self.execution.instance
        if not instance:
            raise InvalidInputError("Tutorial instance not found")

        user_id = str(instance.user_id)

        # Find or create repository
        repo = (
            await self.db.execute(
                select(Repository).where(
                    Repository.github_url == instance.repo_url,
                    Repository.user_id == instance.user_id,
                )
            )
        ).scalar_one_or_none()

        if not repo:
            repo_name = instance.repo_url.split("/")[-1].replace(".git", "")
            repo = Repository(
                user_id=instance.user_id,
                github_url=instance.repo_url,
                name=repo_name,
                status="COMPLETED",
            )
            self.db.add(repo)
            await self.db.flush()
        else:
            repo.status = "COMPLETED"

        # Create tutorial atomically
        tutorial = Tutorial(
            repo_id=repo.repo_id,
            level=self.input.difficulty or "INTERMEDIATE",
            title=title,
            overview=overview,
        )
        self.db.add(tutorial)
        await self.db.flush()

        # Create all modules in one transaction
        for i, module_data in enumerate(modules_data):
            module = Module(
                tutorial_id=tutorial.tutorial_id,
                title=module_data.title,
                order_index=i,
                content_markdown=module_data.content,
            )
            self.db.add(module)

        await self.db.commit()

        return SaveTutorialStepOutput(
            result=TutorialSaveResult(
                tutorial_id=str(tutorial.tutorial_id),
                module_count=len(modules_data),
            ),
        )
