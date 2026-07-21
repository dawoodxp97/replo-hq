import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.dependencies import get_current_user
from ..db.session import get_db
from ..models.modules import Module
from ..models.orchestration import TutorialExecution, TutorialInstance, TutorialStepExecution
from ..models.quizzes import Quiz
from ..models.repositories import Repository
from ..models.tutorials import Tutorial
from ..models.user import User
from ..models.user_progress import UserProgress

router = APIRouter()


# --- Old Response Models (Restored) ---
class QuizResponse(BaseModel):
    quiz_id: uuid.UUID
    question_text: str
    question_type: str
    options: list[dict[str, Any]]


class ModuleResponse(BaseModel):
    module_id: uuid.UUID
    title: str
    order_index: int
    content_markdown: str
    file_path: str | None = None
    code_snippet: str | None = None
    diagram_mermaid: str | None = None
    quiz: QuizResponse | None = None


class TutorialResponse(BaseModel):
    tutorial_id: uuid.UUID
    repo_id: uuid.UUID
    level: str
    title: str
    overview: str | None = None
    overview_diagram_mermaid: str | None = None
    generated_at: str
    modules: list[ModuleResponse]
    repo_name: str | None = None
    repo_url: str | None = None


class TutorialListItemResponse(BaseModel):
    tutorial_id: uuid.UUID
    repo_id: uuid.UUID
    level: str
    title: str
    overview: str | None = None
    generated_at: str
    module_count: int = 0
    completed_modules: int = 0
    progress_percentage: int = 0
    repo_name: str | None = None
    repo_url: str | None = None


# --- New Generation Models ---
class GenerateRequest(BaseModel):
    repoUrl: str
    difficulty: str
    focus: list[str] | None = None
    description: str | None = None


class GenerateResponse(BaseModel):
    instance_id: uuid.UUID
    status: str


class StatusResponse(BaseModel):
    status: str
    current_step: str | None = None
    step_status: str | None = None
    created_at: Any
    updated_at: Any


# For frontend compatibility
class GenerationStatusResponse(BaseModel):
    isGenerating: bool
    generationStep: int
    generationProgress: int
    generationId: str | None = None
    repoId: str | None = None
    status: str
    errorMessage: str | None = None


# --- Existing Endpoints (Restored) ---


@router.get("", response_model=list[TutorialListItemResponse])
async def list_tutorials(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    tutorials = (
        db.query(Tutorial)
        .join(Repository, Tutorial.repo_id == Repository.repo_id)
        .filter(Repository.user_id == current_user.user_id)
        .order_by(Tutorial.generated_at.desc())
        .all()
    )

    if not tutorials:
        return []

    # Get module counts for each tutorial
    module_counts = (
        db.query(Module.tutorial_id, func.count(Module.module_id).label("count"))
        .filter(Module.tutorial_id.in_([t.tutorial_id for t in tutorials]))
        .group_by(Module.tutorial_id)
        .all()
    )

    module_count_map = {str(tutorial_id): count for tutorial_id, count in module_counts}

    # Get all modules for all tutorials in a single query
    tutorial_ids = [t.tutorial_id for t in tutorials]
    all_modules = (
        db.query(Module.tutorial_id, Module.module_id)
        .filter(Module.tutorial_id.in_(tutorial_ids))
        .all()
    )

    # Build module_ids_by_tutorial map
    module_ids_by_tutorial = {}
    all_module_ids = []
    for tutorial_id, module_id in all_modules:
        tutorial_id_str = str(tutorial_id)
        if tutorial_id_str not in module_ids_by_tutorial:
            module_ids_by_tutorial[tutorial_id_str] = []
        module_ids_by_tutorial[tutorial_id_str].append(module_id)
        all_module_ids.append(module_id)

    # Get completed progress for current user
    completed_progress = (
        db.query(UserProgress.module_id)
        .filter(
            UserProgress.user_id == current_user.user_id, UserProgress.module_id.in_(all_module_ids)
        )
        .all()
    )
    completed_module_ids = {str(p.module_id) for p in completed_progress}

    # Get repository information
    repo_ids = [t.repo_id for t in tutorials]
    repositories = db.query(Repository).filter(Repository.repo_id.in_(repo_ids)).all()
    repo_map = {str(r.repo_id): r for r in repositories}

    # Build response
    tutorials_response = []
    for tutorial in tutorials:
        tutorial_id_str = str(tutorial.tutorial_id)
        module_ids = module_ids_by_tutorial.get(tutorial_id_str, [])
        completed_count = sum(1 for mid in module_ids if str(mid) in completed_module_ids)
        total_modules = module_count_map.get(tutorial_id_str, 0)
        progress_pct = int(completed_count / total_modules * 100) if total_modules > 0 else 0

        repo = repo_map.get(str(tutorial.repo_id))

        tutorials_response.append(
            {
                "tutorial_id": tutorial.tutorial_id,
                "repo_id": tutorial.repo_id,
                "level": tutorial.level,
                "title": tutorial.title,
                "overview": tutorial.overview,
                "generated_at": tutorial.generated_at.isoformat(),
                "module_count": total_modules,
                "completed_modules": completed_count,
                "progress_percentage": progress_pct,
                "repo_name": repo.name if repo else None,
                "repo_url": repo.github_url if repo else None,
            }
        )

    return tutorials_response


@router.get("/generation/status", response_model=GenerationStatusResponse)
async def get_generation_status(
    repo_url: str = Query(..., description="Repository URL to check status for"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Frontend compatibility endpoint.
    Maps new TutorialInstance status to old GenerationStatus format.
    """
    # Find the most recent instance for this repo and user
    instance = (
        db.query(TutorialInstance)
        .filter(
            TutorialInstance.repo_url == repo_url, TutorialInstance.user_id == current_user.user_id
        )
        .order_by(TutorialInstance.created_at.desc())
        .first()
    )

    if not instance:
        return {
            "isGenerating": False,
            "generationStep": 0,
            "generationProgress": 0,
            "generationId": None,
            "repoId": None,
            "status": "NOT_FOUND",
            "errorMessage": None,
        }

    is_generating = instance.status in ["pending", "running"]

    # Calculate progress based on steps
    progress = 0
    step = 0

    if instance.status == "completed":
        progress = 100
        step = 5
    elif instance.status == "failed":
        progress = 0
        step = 0
    elif instance.status == "running":
        execution = (
            db.query(TutorialExecution)
            .filter(TutorialExecution.tutorial_instance_id == instance.id)
            .order_by(TutorialExecution.started_at.desc())
            .first()
        )
        if execution:
            step = execution.current_step_order
            progress = min(step * 20, 90)  # 5 steps approx

    # Find repo id if available
    repo = (
        db.query(Repository)
        .filter(Repository.github_url == repo_url, Repository.user_id == current_user.user_id)
        .first()
    )

    return {
        "isGenerating": is_generating,
        "generationStep": step,
        "generationProgress": int(progress),
        "generationId": str(instance.id),
        "repoId": str(repo.repo_id) if repo else None,
        "status": instance.status.upper(),
        "errorMessage": None,  # Simplify
    }


@router.get("/{tutorial_id_or_instance_id}", response_model=Any)
async def get_tutorial_or_result(
    tutorial_id_or_instance_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Unified endpoint to get either a completed Tutorial or the result of a TutorialInstance.
    This handles the confusion between tutorial_id and instance_id.
    """
    # First try to find a Tutorial
    tutorial = db.query(Tutorial).filter(Tutorial.tutorial_id == tutorial_id_or_instance_id).first()
    if tutorial:
        # It's a Tutorial ID, return the full tutorial content
        repo = db.query(Repository).filter(Repository.repo_id == tutorial.repo_id).first()
        modules = (
            db.query(Module)
            .filter(Module.tutorial_id == tutorial.tutorial_id)
            .order_by(Module.order_index)
            .all()
        )
        module_ids = [module.module_id for module in modules]
        quizzes = db.query(Quiz).filter(Quiz.module_id.in_(module_ids)).all()
        quiz_map = {quiz.module_id: quiz for quiz in quizzes}

        modules_response = []
        for module in modules:
            quiz = quiz_map.get(module.module_id)
            quiz_response = None
            if quiz:
                quiz_response = {
                    "quiz_id": quiz.quiz_id,
                    "question_text": quiz.question_text,
                    "question_type": quiz.question_type,
                    "options": quiz.options,
                }

            modules_response.append(
                {
                    "module_id": module.module_id,
                    "title": module.title,
                    "order_index": module.order_index,
                    "content_markdown": module.content_markdown,
                    "file_path": module.file_path,
                    "code_snippet": module.code_snippet,
                    "diagram_mermaid": module.diagram_mermaid,
                    "quiz": quiz_response,
                }
            )

        return {
            "tutorial_id": tutorial.tutorial_id,
            "repo_id": tutorial.repo_id,
            "level": tutorial.level,
            "title": tutorial.title,
            "overview": tutorial.overview,
            "overview_diagram_mermaid": tutorial.overview_diagram_mermaid,
            "generated_at": tutorial.generated_at.isoformat(),
            "modules": modules_response,
            "repo_name": repo.name if repo else None,
            "repo_url": repo.github_url if repo else None,
        }

    # If not a tutorial, maybe it's a TutorialInstance ID (for status/result)
    # But status/result have their own sub-paths.
    # However, if the frontend calls /api/tutorial/{id}, it expects a tutorial.
    # If we are here, it means no tutorial found.

    raise HTTPException(status_code=404, detail="Tutorial not found")


# --- New Generation Endpoints ---


@router.post("/generate", response_model=GenerateResponse)
async def generate_tutorial(
    request_data: GenerateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Create instance
    instance = TutorialInstance(
        user_id=current_user.user_id,
        repo_url=request_data.repoUrl,  # Use repoUrl from frontend
        status="pending",
    )
    db.add(instance)
    db.commit()
    db.refresh(instance)

    # Enqueue job
    redis_pool = getattr(request.app.state, "redis_pool", None)
    if redis_pool:
        await redis_pool.enqueue_job(
            "generate_tutorial_task", tutorial_instance_id=str(instance.id)
        )

    return {"instance_id": instance.id, "status": instance.status}


@router.post("/{instance_id}/retry", response_model=GenerateResponse)
async def retry_tutorial(
    instance_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    instance = db.query(TutorialInstance).filter(TutorialInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail="Tutorial instance not found")

    if instance.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if instance.status not in ["failed", "completed"]:
        raise HTTPException(status_code=400, detail="Can only retry failed or completed tutorials")

    # Reset status
    instance.status = "pending"
    db.commit()

    # Enqueue job
    redis_pool = getattr(request.app.state, "redis_pool", None)
    if redis_pool:
        await redis_pool.enqueue_job(
            "generate_tutorial_task", tutorial_instance_id=str(instance.id)
        )

    return {"instance_id": instance.id, "status": instance.status}


@router.get("/{instance_id}/status", response_model=StatusResponse)
async def get_status(
    instance_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    instance = db.query(TutorialInstance).filter(TutorialInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail="Tutorial instance not found")

    if instance.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get current execution info
    execution = (
        db.query(TutorialExecution)
        .filter(TutorialExecution.tutorial_instance_id == instance.id)
        .order_by(TutorialExecution.started_at.desc())
        .first()
    )

    current_step = None
    step_status = None

    if execution:
        latest_step = (
            db.query(TutorialStepExecution)
            .filter(TutorialStepExecution.tutorial_execution_id == execution.id)
            .order_by(TutorialStepExecution.started_at.desc())
            .first()
        )

        if latest_step:
            current_step = latest_step.step_type
            step_status = latest_step.status

    return {
        "status": instance.status,
        "current_step": current_step,
        "step_status": step_status,
        "created_at": instance.created_at,
        "updated_at": instance.updated_at,
    }


@router.get("/{instance_id}/result")
async def get_result(
    instance_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the raw result of the generation process.
    Does NOT return the formatted Tutorial object from the database.
    Use GET /api/tutorial/{tutorial_id} for that.
    """
    instance = db.query(TutorialInstance).filter(TutorialInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail="Tutorial instance not found")

    if instance.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if instance.status != "completed":
        raise HTTPException(status_code=400, detail="Tutorial generation not completed")

    # Get the final output from the last step of the last execution
    execution = (
        db.query(TutorialExecution)
        .filter(TutorialExecution.tutorial_instance_id == instance.id)
        .order_by(TutorialExecution.started_at.desc())
        .first()
    )

    if not execution:
        return {"error": "No execution found"}

    steps = (
        db.query(TutorialStepExecution)
        .filter(TutorialStepExecution.tutorial_execution_id == execution.id)
        .order_by(TutorialStepExecution.step_order)
        .all()
    )

    # Construct result by merging outputs
    result = {}
    for step in steps:
        if step.output_data:
            result.update(step.output_data)

    return result
