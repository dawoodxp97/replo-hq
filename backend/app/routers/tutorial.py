# ./backend/app/routers/tutorial.py
import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from ..db.session import get_db
from ..core.dependencies import get_current_user
from .. import models
from ..models.tutorials import Tutorial
from ..models.modules import Module
from ..models.quizzes import Quiz
from pydantic import BaseModel

router = APIRouter()

# --- Pydantic Models ---
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

# --- API Endpoints ---
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
        "modules": modules_response
    }
