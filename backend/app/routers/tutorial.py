import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from github import Github
from github.GithubException import BadCredentialsException, UnknownObjectException
from pydantic import BaseModel, HttpUrl
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from .. import models
from ..core.dependencies import get_current_user
from ..db.session import get_db
from ..models.modules import Module
from ..models.quizzes import Quiz
from ..models.repositories import Repository
from ..models.tutorial_generation import TutorialGeneration
from ..models.tutorials import Tutorial
from ..models.user_progress import UserProgress

router = APIRouter()
class QuizResponse(BaseModel):
    quiz_id: uuid.UUID
    question_text: str
    question_type: str
    options: List[Dict[str, Any]]

class ModuleResponse(BaseModel):
    module_id: uuid.UUID
    title: str
    order_index: int
    content_markdown: str
    file_path: Optional[str] = None
    code_snippet: Optional[str] = None
    diagram_mermaid: Optional[str] = None
    quiz: Optional[QuizResponse] = None

class TutorialResponse(BaseModel):
    tutorial_id: uuid.UUID
    repo_id: uuid.UUID
    level: str
    title: str
    overview: Optional[str] = None
    overview_diagram_mermaid: Optional[str] = None
    generated_at: str
    modules: List[ModuleResponse]
    repo_name: Optional[str] = None
    repo_url: Optional[str] = None

# Generation request/response models
class GenerateTutorialRequest(BaseModel):
    repoUrl: str
    difficulty: str  # beginner, intermediate, advanced
    focus: Optional[List[str]] = None
    description: Optional[str] = None

class GenerationStatusResponse(BaseModel):
    isGenerating: bool
    generationStep: int
    generationProgress: int
    generationId: Optional[str] = None
    repoId: Optional[str] = None
    status: str
    errorMessage: Optional[str] = None

class TutorialListItemResponse(BaseModel):
    tutorial_id: uuid.UUID
    repo_id: uuid.UUID
    level: str
    title: str
    overview: Optional[str] = None
    generated_at: str
    module_count: int = 0
    completed_modules: int = 0
    progress_percentage: int = 0
    repo_name: Optional[str] = None
    repo_url: Optional[str] = None

@router.get("", response_model=List[TutorialListItemResponse])
async def list_tutorials(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tutorials = db.query(Tutorial).join(
        Repository, Tutorial.repo_id == Repository.repo_id
    ).filter(
        Repository.user_id == current_user.user_id
    ).order_by(Tutorial.generated_at.desc()).all()
    
    # Get module counts for each tutorial
    module_counts = db.query(
        Module.tutorial_id,
        func.count(Module.module_id).label('count')
    ).filter(
        Module.tutorial_id.in_([t.tutorial_id for t in tutorials])
    ).group_by(Module.tutorial_id).all()
    
    module_count_map = {str(tutorial_id): count for tutorial_id, count in module_counts}
    
    # Get all modules for all tutorials in a single query
    tutorial_ids = [t.tutorial_id for t in tutorials]
    all_modules = db.query(Module.tutorial_id, Module.module_id).filter(
        Module.tutorial_id.in_(tutorial_ids)
    ).all()
    
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
    completed_progress = db.query(UserProgress.module_id).filter(
        UserProgress.user_id == current_user.user_id,
        UserProgress.module_id.in_(all_module_ids)
    ).all()
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
        progress_pct = int((completed_count / total_modules * 100)) if total_modules > 0 else 0
        
        repo = repo_map.get(str(tutorial.repo_id))
        
        tutorials_response.append({
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
            "repo_url": repo.github_url if repo else None
        })
    
    return tutorials_response
@router.get("/{tutorial_id}", response_model=TutorialResponse)
async def get_tutorial_content(
    tutorial_id: uuid.UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    THE MAIN ENDPOINT for the tutorial player.
    Returns the full tutorial, all modules, and all quizzes.
    """
    # Get the tutorial
    tutorial = db.query(Tutorial).filter(Tutorial.tutorial_id == tutorial_id).first()
    if not tutorial:
        raise HTTPException(status_code=404, detail="Tutorial not found")
    
    # Get repository information
    repo = db.query(Repository).filter(Repository.repo_id == tutorial.repo_id).first()
    
    # Get all modules for this tutorial, ordered by order_index
    modules = db.query(Module).filter(Module.tutorial_id == tutorial_id).order_by(Module.order_index).all()
    
    # Get all quizzes for these modules
    module_ids = [module.module_id for module in modules]
    quizzes = db.query(Quiz).filter(Quiz.module_id.in_(module_ids)).all()
    
    # Create a dictionary mapping module_id to quiz
    quiz_map = {quiz.module_id: quiz for quiz in quizzes}
    
    # Build the response
    modules_response = []
    for module in modules:
        quiz = quiz_map.get(module.module_id)
        quiz_response = None
        if quiz:
            quiz_response = {
                "quiz_id": quiz.quiz_id,
                "question_text": quiz.question_text,
                "question_type": quiz.question_type,
                "options": quiz.options
            }
        
        modules_response.append({
            "module_id": module.module_id,
            "title": module.title,
            "order_index": module.order_index,
            "content_markdown": module.content_markdown,
            "file_path": module.file_path,
            "code_snippet": module.code_snippet,
            "diagram_mermaid": module.diagram_mermaid,
            "quiz": quiz_response
        })
    
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
        "repo_url": repo.github_url if repo else None
    }

# --- Generation Endpoints ---
@router.post("/generate")
async def generate_tutorial(
    request_data: GenerateTutorialRequest,
    request: Request,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initiate tutorial generation for a repository.
    Creates a generation record and enqueues the job.
    """
    # Check if user has LLM API key configured (primary provider)
    settings = db.query(models.UserSettings).filter(
        models.UserSettings.user_id == current_user.user_id
    ).first()
    
    if not settings:
        raise HTTPException(
            status_code=400,
            detail="LLM provider not configured. Please configure your LLM provider in settings."
        )
    
    # Check for primary LLM API key or backward compatibility with openai_api_key
    llm_provider = settings.llm_provider or "openai"
    has_api_key = bool(settings.llm_api_key)
    
    # Backward compatibility: check openai_api_key if no llm_api_key and provider is openai
    if not has_api_key and llm_provider == "openai" and settings.openai_api_key:
        has_api_key = True
    
    # Ollama doesn't require an API key
    if llm_provider != "ollama" and not has_api_key:
        raise HTTPException(
            status_code=400,
            detail=f"{llm_provider.upper()} API key is required. Please add it in your LLM settings."
        )
    
    # Check if user has an active generation (only one at a time)
    active_generation = db.query(TutorialGeneration).filter(
        TutorialGeneration.user_id == current_user.user_id,
        TutorialGeneration.status.in_(['PENDING', 'CLONING', 'ANALYZING', 'PROCESSING', 'GENERATING'])
    ).first()
    
    if active_generation:
        raise HTTPException(
            status_code=400,
            detail="You already have a tutorial generation in progress. Please wait for it to complete."
        )
    
    # Validate GitHub repository URL and check if it's public
    try:
        # Extract owner and repo from URL
        url_parts = request_data.repoUrl.replace('https://github.com/', '').replace('http://github.com/', '').strip('/')
        if url_parts.endswith('.git'):
            url_parts = url_parts[:-4]
        
        parts = url_parts.split('/')
        if len(parts) < 2:
            raise HTTPException(status_code=400, detail="Invalid GitHub repository URL")
        
        owner = parts[0]
        repo_name = '/'.join(parts[1:])
        
        # Check if repository is public (no auth needed for public repos)
        # Using GitHub API without token to check if repo is public
        g = Github()  # No token - only works for public repos
        repo = g.get_repo(f"{owner}/{repo_name}")
        
        if repo.private:
            raise HTTPException(
                status_code=400,
                detail="Private repositories are not supported. Please use a public repository."
            )
    except UnknownObjectException:
        raise HTTPException(
            status_code=404,
            detail="Repository not found or is not accessible. Please ensure the repository is public."
        )
    except BadCredentialsException:
        # This shouldn't happen with no token, but handle it
        raise HTTPException(
            status_code=500,
            detail="Error validating repository"
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error validating repository: {str(e)}"
        )
    
    # Normalize difficulty level
    difficulty_upper = request_data.difficulty.upper()
    if difficulty_upper not in ['BEGINNER', 'INTERMEDIATE', 'ADVANCED']:
        difficulty_upper = 'INTERMEDIATE'
    
    # Check if repository already exists in our DB
    repo = db.query(Repository).filter(
        Repository.github_url == request_data.repoUrl
    ).first()
    
    if not repo:
        # Create new repository
        repo_name = request_data.repoUrl.split('/')[-1].replace('.git', '')
        repo = Repository(
            github_url=request_data.repoUrl,
            name=repo_name,
            status='PENDING',
            user_id=current_user.user_id,
        )
        db.add(repo)
        db.commit()
        db.refresh(repo)
    
    # Create generation record
    generation = TutorialGeneration(
        user_id=current_user.user_id,
        repo_id=repo.repo_id,
        repo_url=request_data.repoUrl,
        difficulty=difficulty_upper,
        focus_areas=request_data.focus if request_data.focus else None,
        description=request_data.description,
        status='PENDING',
        generation_step=0,
        generation_progress=0,
    )
    db.add(generation)
    db.commit()
    db.refresh(generation)
    
    # Enqueue the job
    try:
        import logging
        logging.basicConfig(level=logging.INFO)
        log = logging.getLogger(__name__)
        
        log.info(f"[GENERATION INIT] Starting job enqueue for generation_id: {generation.generation_id}")
        log.info(f"[GENERATION INIT] Repo URL: {request_data.repoUrl}")
        log.info(f"[GENERATION INIT] Difficulty: {difficulty_upper}")
        log.info(f"[GENERATION INIT] User ID: {current_user.user_id}")
        
        redis_pool = request.app.state.redis_pool
        if not redis_pool:
            log.error("[GENERATION INIT] ERROR: Redis pool not initialized!")
            raise Exception("Redis pool not initialized")
        
        log.info("[GENERATION INIT] Redis pool found, enqueueing job...")
        job = await redis_pool.enqueue_job(
            'generate_tutorial',
            {
                "generation_id": str(generation.generation_id),
                "repo_id": str(repo.repo_id),
                "github_url": request_data.repoUrl,
                "user_id": str(current_user.user_id),
                "difficulty": difficulty_upper,
                "focus_areas": request_data.focus,
                "description": request_data.description,
            }
        )
        log.info(f"[GENERATION INIT] ✅ Job enqueued successfully! Job ID: {job.job_id if hasattr(job, 'job_id') else 'unknown'}")
        log.info(f"[GENERATION INIT] Job data: generation_id={generation.generation_id}, repo_id={repo.repo_id}")
        
    except Exception as e:
        import logging
        logging.basicConfig(level=logging.ERROR)
        log = logging.getLogger(__name__)
        log.error(f"[GENERATION INIT] ❌ ERROR enqueueing job: {str(e)}")
        log.error(f"[GENERATION INIT] Exception type: {type(e).__name__}")
        import traceback
        log.error(f"[GENERATION INIT] Traceback: {traceback.format_exc()}")
        
        # Update generation status to FAILED
        generation.status = 'FAILED'
        generation.error_message = f"Failed to enqueue job: {str(e)}"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to enqueue generation job: {str(e)}")
    
    return {
        "generationId": str(generation.generation_id),
        "message": "Tutorial generation started"
    }

@router.get("/generation/status", response_model=GenerationStatusResponse)
async def get_generation_status(
    repo_url: str = Query(..., description="Repository URL to check status for"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the status of an ongoing tutorial generation.
    """
    # Find the most recent generation for this repo and user
    generation = db.query(TutorialGeneration).filter(
        TutorialGeneration.repo_url == repo_url,
        TutorialGeneration.user_id == current_user.user_id
    ).order_by(TutorialGeneration.created_at.desc()).first()
    
    if not generation:
        # No generation found
        return {
            "isGenerating": False,
            "generationStep": 0,
            "generationProgress": 0,
            "generationId": None,
            "repoId": None,
            "status": "NOT_FOUND",
            "errorMessage": None
        }
    
    # Determine if generation is active
    is_generating = generation.status in ['PENDING', 'CLONING', 'ANALYZING', 'PROCESSING', 'GENERATING']
    
    return {
        "isGenerating": is_generating,
        "generationStep": generation.generation_step,
        "generationProgress": generation.generation_progress,
        "generationId": str(generation.generation_id),
        "repoId": str(generation.repo_id),
        "status": generation.status,
        "errorMessage": generation.error_message
    }
