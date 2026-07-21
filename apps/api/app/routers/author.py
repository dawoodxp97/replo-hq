import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models
from ..core.dependencies import get_current_user
from ..db.session import get_db
from ..models.modules import Module
from ..models.quizzes import Quiz
from ..models.repositories import Repository
from ..models.tutorials import Tutorial

router = APIRouter()
class ModuleUpdate(BaseModel):
    title: str
    content_markdown: str
    code_snippet: str
    diagram_mermaid: Optional[str] = None

class QuizUpdate(BaseModel):
    question_text: str
    options: List[dict]

class TutorialUpdate(BaseModel):
    title: Optional[str] = None
    overview: Optional[str] = None
    level: Optional[str] = None
    overview_diagram_mermaid: Optional[str] = None

class ModuleReorder(BaseModel):
    module_ids: List[uuid.UUID]

class ModuleResponse(BaseModel):
    module_id: uuid.UUID
    title: str
    content_markdown: str
    code_snippet: str
    diagram_mermaid: Optional[str] = None

class TutorialListItem(BaseModel):
    tutorial_id: uuid.UUID
    title: str
    level: str
    overview: Optional[str] = None
    generated_at: str
    repo_name: Optional[str] = None
    repo_url: Optional[str] = None
    module_count: int = 0

# --- Helper Functions ---
def _verify_tutorial_ownership(tutorial_id: uuid.UUID, user_id: uuid.UUID, db: Session) -> Tutorial:
    """Verify that the user owns the tutorial and return the tutorial."""
    tutorial = db.query(Tutorial).join(
        Repository, Tutorial.repo_id == Repository.repo_id
    ).filter(
        Tutorial.tutorial_id == tutorial_id,
        Repository.user_id == user_id
    ).first()
    
    if not tutorial:
        raise HTTPException(status_code=404, detail="Tutorial not found or you don't have permission to edit it")
    
    return tutorial

def _verify_module_ownership(module_id: uuid.UUID, user_id: uuid.UUID, db: Session) -> Module:
    """Verify that the user owns the tutorial this module belongs to."""
    module = db.query(Module).join(
        Tutorial, Module.tutorial_id == Tutorial.tutorial_id
    ).join(
        Repository, Tutorial.repo_id == Repository.repo_id
    ).filter(
        Module.module_id == module_id,
        Repository.user_id == user_id
    ).first()
    
    if not module:
        raise HTTPException(status_code=404, detail="Module not found or you don't have permission to edit it")
    
    return module

def _verify_quiz_ownership(quiz_id: uuid.UUID, user_id: uuid.UUID, db: Session) -> Quiz:
    """Verify that the user owns the tutorial this quiz belongs to."""
    quiz = db.query(Quiz).join(
        Module, Quiz.module_id == Module.module_id
    ).join(
        Tutorial, Module.tutorial_id == Tutorial.tutorial_id
    ).join(
        Repository, Tutorial.repo_id == Repository.repo_id
    ).filter(
        Quiz.quiz_id == quiz_id,
        Repository.user_id == user_id
    ).first()
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found or you don't have permission to edit it")
    
    return quiz

# --- API Endpoints ---
@router.get("/", response_model=List[TutorialListItem])
def get_author_dashboard(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all tutorials for the current user (for authoring).
    Returns tutorials owned by the user through their repositories.
    """
    # Get tutorials owned by the user through repositories
    tutorials = db.query(Tutorial).join(
        Repository, Tutorial.repo_id == Repository.repo_id
    ).filter(
        Repository.user_id == current_user.user_id
    ).order_by(Tutorial.generated_at.desc()).all()
    
    # Get module counts for each tutorial
    tutorial_ids = [t.tutorial_id for t in tutorials]
    module_counts = db.query(
        Module.tutorial_id,
        func.count(Module.module_id).label('count')
    ).filter(
        Module.tutorial_id.in_(tutorial_ids)
    ).group_by(Module.tutorial_id).all()
    
    module_count_map = {str(tutorial_id): count for tutorial_id, count in module_counts}
    
    # Get repository information
    repo_ids = [t.repo_id for t in tutorials]
    repos = db.query(Repository).filter(Repository.repo_id.in_(repo_ids)).all()
    repo_map = {repo.repo_id: repo for repo in repos}
    
    result = []
    for tutorial in tutorials:
        repo = repo_map.get(tutorial.repo_id)
        result.append(
            TutorialListItem(
                tutorial_id=tutorial.tutorial_id,
                title=tutorial.title,
                level=tutorial.level,
                overview=tutorial.overview,
                generated_at=tutorial.generated_at.isoformat(),
                repo_name=repo.name if repo else None,
                repo_url=repo.github_url if repo else None,
                module_count=module_count_map.get(str(tutorial.tutorial_id), 0)
            )
        )
    return result

@router.put("/tutorials/{tutorial_id}")
async def update_tutorial_metadata(
    tutorial_id: uuid.UUID,
    data: TutorialUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update tutorial metadata (title, overview, level, diagram).
    """
    tutorial = _verify_tutorial_ownership(tutorial_id, current_user.user_id, db)
    
    # Update fields if provided
    if data.title is not None:
        tutorial.title = data.title
    if data.overview is not None:
        tutorial.overview = data.overview
    if data.level is not None:
        if data.level.upper() not in ['BEGINNER', 'INTERMEDIATE', 'ADVANCED']:
            raise HTTPException(status_code=400, detail="Level must be BEGINNER, INTERMEDIATE, or ADVANCED")
        tutorial.level = data.level.upper()
    if data.overview_diagram_mermaid is not None:
        tutorial.overview_diagram_mermaid = data.overview_diagram_mermaid
    
    db.commit()
    db.refresh(tutorial)
    
    return {
        "message": "Tutorial updated successfully",
        "tutorial_id": tutorial.tutorial_id,
        "title": tutorial.title,
        "level": tutorial.level,
        "overview": tutorial.overview
    }

@router.put("/tutorials/{tutorial_id}/modules/reorder")
async def reorder_modules(
    tutorial_id: uuid.UUID,
    data: ModuleReorder,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reorder modules within a tutorial.
    """
    tutorial = _verify_tutorial_ownership(tutorial_id, current_user.user_id, db)
    
    # Verify all modules belong to this tutorial
    modules = db.query(Module).filter(
        Module.tutorial_id == tutorial_id,
        Module.module_id.in_(data.module_ids)
    ).all()
    
    if len(modules) != len(data.module_ids):
        raise HTTPException(status_code=400, detail="Some modules don't belong to this tutorial")
    
    # Create a map of module_id to new order_index
    order_map = {module_id: index for index, module_id in enumerate(data.module_ids)}
    
    # Update order_index for each module
    for module in modules:
        module.order_index = order_map[module.module_id]
    
    db.commit()
    
    return {"message": "Modules reordered successfully"}

@router.put("/modules/{module_id}", response_model=ModuleResponse)
async def update_module_content(
    module_id: uuid.UUID, 
    data: ModuleUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Allows a user to manually edit a generated module.
    """
    # Verify ownership
    module = _verify_module_ownership(module_id, current_user.user_id, db)
    
    # Update the module
    module.title = data.title
    module.content_markdown = data.content_markdown
    module.code_snippet = data.code_snippet
    if data.diagram_mermaid is not None:
        module.diagram_mermaid = data.diagram_mermaid
    
    db.commit()
    db.refresh(module)
    
    return {
        "module_id": module.module_id,
        "title": module.title,
        "content_markdown": module.content_markdown,
        "code_snippet": module.code_snippet,
        "diagram_mermaid": module.diagram_mermaid
    }

@router.put("/quizzes/{quiz_id}")
async def update_quiz_content(
    quiz_id: uuid.UUID, 
    data: QuizUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Allows a user to manually edit a generated quiz.
    """
    # Verify ownership
    quiz = _verify_quiz_ownership(quiz_id, current_user.user_id, db)
    
    # Update the quiz
    quiz.question_text = data.question_text
    quiz.options = data.options
    
    # Find the correct answer
    correct_answer = next((opt["text"] for opt in data.options if opt.get("is_correct")), None)
    if correct_answer:
        quiz.correct_answer = correct_answer
    
    db.commit()
    
    return {"message": "Quiz updated successfully"}
