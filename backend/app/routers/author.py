# ./backend/app/routers/author.py
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..db.session import get_db
from ..models.tutorials import Tutorial
from ..models.modules import Module
from ..models.quizzes import Quiz

router = APIRouter()

# --- Pydantic Models ---
class ModuleUpdate(BaseModel):
    title: str
    content_markdown: str
    code_snippet: str
    diagram_mermaid: Optional[str] = None

class QuizUpdate(BaseModel):
    question_text: str
    options: List[dict]

class ModuleResponse(BaseModel):
    module_id: uuid.UUID
    title: str
    content_markdown: str
    code_snippet: str
    diagram_mermaid: Optional[str] = None

# --- API Endpoints ---
@router.get("/")
def get_author_dashboard(db: Session = Depends(get_db)):
    """
    Get all tutorials for the current user (for authoring).
    """
    # In a real implementation, get user_id from auth and filter by it
    tutorials = db.query(Tutorial).all()
    
    return {
        "tutorials": [
            {
                "tutorial_id": tutorial.tutorial_id,
                "title": tutorial.title,
                "level": tutorial.level,
                "generated_at": tutorial.generated_at.isoformat()
            }
            for tutorial in tutorials
        ]
    }

@router.put("/modules/{module_id}", response_model=ModuleResponse)
async def update_module_content(
    module_id: uuid.UUID, 
    data: ModuleUpdate, 
    db: Session = Depends(get_db)
):
    """
    Allows a user to manually edit a generated module.
    """
    # Get the module
    module = db.query(Module).filter(Module.module_id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    # In a real implementation, check if user owns the tutorial this module belongs to
    
    # Update the module
    module.title = data.title
    module.content_markdown = data.content_markdown
    module.code_snippet = data.code_snippet
    if data.diagram_mermaid:
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
    db: Session = Depends(get_db)
):
    """
    Allows a user to manually edit a generated quiz.
    """
    # Get the quiz
    quiz = db.query(Quiz).filter(Quiz.quiz_id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # In a real implementation, check if user owns the tutorial this quiz belongs to
    
    # Update the quiz
    quiz.question_text = data.question_text
    quiz.options = data.options
    
    # Find the correct answer
    correct_answer = next((opt["text"] for opt in data.options if opt.get("is_correct")), None)
    if correct_answer:
        quiz.correct_answer = correct_answer
    
    db.commit()
    
    return {"message": "Quiz updated successfully"}
