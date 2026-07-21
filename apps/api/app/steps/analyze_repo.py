from typing import Any

from ..orchestrator.step import Step
from ..utils.repo_utils import build_file_tree, clone_repo, get_file_content


class AnalyzeRepoStructureStep(Step):
    """Analyzes repository structure and identifies key components"""

    SYSTEM_PROMPT = """You are an expert code analyst.
    Your goal is to analyze a codebase and provide a structural overview for creating a tutorial."""

    async def execute(self) -> dict[str, Any]:
        # 1. Get repo info from execution context
        repo_url = self.input_data.get("repo_url")
        if not repo_url:
            raise ValueError("repo_url is required for AnalyzeRepoStructureStep")

        instance_id = self.execution.tutorial_instance_id

        # 2. Clone Repo
        repo_path = clone_repo(repo_url, instance_id)

        # 3. Build File Tree
        file_tree = build_file_tree(repo_path)

        # 4. Identify Key Files (heuristics)
        key_files = self._identify_key_files(file_tree)

        # 5. Read Key Files Content
        key_files_content = ""
        for file in key_files[:5]:  # Limit to top 5 files
            content = get_file_content(repo_path, file["path"])
            if content:
                key_files_content += f"\n--- {file['path']} ---\n{content[:2000]}\n"

        # 6. Prepare prompt data
        prompt_data = {
            "repo_name": repo_url.split("/")[-1],
            "primary_language": "Unknown",
            "repo_description": "A GitHub repository",
            "file_tree": self._format_json_for_prompt(file_tree),
            "key_files_content": key_files_content,
            "response_format": """
            {
                "entry_points": ["file1", "file2"],
                "core_features": ["feature1", "feature2"],
                "architecture_pattern": "description",
                "tutorial_flow": [{"step": "1", "description": "..."}]
            }
            """,
        }

        # 7. Get prompt template
        template = self.step_config.prompt_template
        if template == "Default prompt":
            template = """
Analyze the following repository structure and provide insights:

**Repository Information:**
- Name: {repo_name}
- Primary Language: {primary_language}
- Description: {repo_description}

**File Structure:**
{file_tree}

**Key Files Content:**
{key_files_content}

**Task:**
Identify:
1. Main entry points
2. Core functionality/features
3. Architecture patterns used
4. Dependencies and how they're used
5. Suggested tutorial flow

Respond in JSON format:
{response_format}
"""

        prompt = template.format(**prompt_data)

        # 8. Call AI
        messages = [
            {"role": "system", "content": self.step_config.system_prompt or self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        response = await self.call_ai(messages, response_format={"type": "json_object"})

        # 9. Parse response
        parsed_response = self.parse_ai_response(response)

        # Return both the analysis and the repo path for next steps
        result = parsed_response
        result["repo_path"] = repo_path
        result["key_files_content"] = key_files_content
        return result

    def _identify_key_files(self, tree: list[dict]) -> list[dict]:
        # BFS to find files
        queue = tree.copy()
        files = []
        while queue:
            node = queue.pop(0)
            if node["type"] == "file":
                files.append(node)
            elif node["children"]:
                queue.extend(node["children"])

        priority = [
            "readme.md",
            "main.py",
            "index.js",
            "app.py",
            "server.js",
            "package.json",
            "requirements.txt",
        ]

        def score(file):
            name = file["name"].lower()
            for i, p in enumerate(priority):
                if p in name:
                    return i
            return 100

        return sorted(files, key=score)
