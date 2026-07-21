from typing import Any

from ..models.modules import Module
from ..models.repositories import Repository
from ..models.tutorials import Tutorial
from ..orchestrator.step import Step


class SaveTutorialStep(Step):
    """Saves the generated tutorial to the database"""

    async def execute(self) -> dict[str, Any]:
        # 1. Gather data from input (merged context)
        repo_url = self.input_data.get("repo_url")
        title = self.input_data.get("title", "Generated Tutorial")
        overview = self.input_data.get("overview", "")
        modules_data = self.input_data.get("modules", [])

        user_id = self.execution.instance.user_id

        # 2. Find or Create Repository
        repo = (
            self.db.query(Repository)
            .filter(Repository.github_url == repo_url, Repository.user_id == user_id)
            .first()
        )

        if not repo:
            # This should have been created or found earlier, but let's ensure it exists
            repo_name = repo_url.split("/")[-1].replace(".git", "")
            repo = Repository(
                user_id=user_id, github_url=repo_url, name=repo_name, status="COMPLETED"
            )
            self.db.add(repo)
            self.db.commit()
            self.db.refresh(repo)
        else:
            repo.status = "COMPLETED"
            self.db.commit()

        # 3. Create Tutorial
        tutorial = Tutorial(
            repo_id=repo.repo_id,
            level="INTERMEDIATE",  # Default for now, or extract from analysis
            title=title,
            overview=overview,
        )
        self.db.add(tutorial)
        self.db.commit()
        self.db.refresh(tutorial)

        # 4. Create Modules
        for i, module_data in enumerate(modules_data):
            module_title = module_data.get("title", f"Module {i + 1}")
            content = module_data.get("content", "")

            module = Module(
                tutorial_id=tutorial.tutorial_id,
                title=module_title,
                order_index=i,
                content_markdown=content,
            )
            self.db.add(module)
            self.db.commit()  # Commit early to get ID for quizzes if needed
            self.db.refresh(module)

            # Add dummy quiz for now or extract if generated
            # Future: Generate quizzes in a separate step

        return {"tutorial_id": str(tutorial.tutorial_id)}
