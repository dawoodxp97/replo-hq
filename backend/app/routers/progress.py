# ./backend/app/routers/progress.py
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..db.session import get_db
from ..models.user_progress import UserProgress
from ..models.quizzes import Quiz

router = APIRouter()

# --- Pydantic Models ---
class ProgressUpdate(BaseModel):
    module_id: uuid.UUID

class QuizSubmit(BaseModel):
    quiz_id: uuid.UUID
    submitted_answer: str

class ProgressResponse(BaseModel):
    progress_id: uuid.UUID
    module_id: uuid.UUID
    completed_at: str
    quiz_score: Optional[int] = None

class UserProgressResponse(BaseModel):
    user_id: uuid.UUID
    progress: List[ProgressResponse]

# --- API Endpoints ---
@router.post("/complete_module", response_model=ProgressResponse)
async def mark_module_complete(progress: ProgressUpdate, db: Session = Depends(get_db)):
    """
    Called when a user clicks "Next" on a module.
    """
    # In a real implementation, get user_id from auth
    user_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
    
    # Check if progress already exists
    existing_progress = db.query(UserProgress).filter(
        UserProgress.user_id == user_id,
        UserProgress.module_id == progress.module_id
    ).first()
    
    if existing_progress:
        # Update existing progress
        existing_progress.completed_at = datetime.now()
        db.commit()
        db.refresh(existing_progress)
        return {
            "progress_id": existing_progress.progress_id,
            "module_id": existing_progress.module_id,
            "completed_at": existing_progress.completed_at.isoformat(),
            "quiz_score": existing_progress.quiz_score
        }
    else:
        # Create new progress
        new_progress = UserProgress(
            user_id=user_id,
            module_id=progress.module_id,
            completed_at=datetime.now()
        )
        db.add(new_progress)
        db.commit()
        db.refresh(new_progress)
        return {
            "progress_id": new_progress.progress_id,
            "module_id": new_progress.module_id,
            "completed_at": new_progress.completed_at.isoformat(),
            "quiz_score": new_progress.quiz_score
        }

@router.post("/submit_quiz", response_model=dict)
async def submit_quiz_answer(submission: QuizSubmit, db: Session = Depends(get_db)):
    """
    Check a user's quiz answer.
    """
    # In a real implementation, get user_id from auth
    user_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
    
    # Get the quiz
    quiz = db.query(Quiz).filter(Quiz.quiz_id == submission.quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Check the answer
    is_correct = False
    for option in quiz.options:
        if option.get("text") == submission.submitted_answer and option.get("is_correct"):
            is_correct = True
            break
    
    # Update the user progress
    progress = db.query(UserProgress).filter(
        UserProgress.user_id == user_id,
        UserProgress.module_id == quiz.module_id
    ).first()
    
    if progress:
        progress.quiz_score = 1 if is_correct else 0
        db.commit()
    else:
        # Create new progress with quiz score
        new_progress = UserProgress(
            user_id=user_id,
            module_id=quiz.module_id,
            completed_at=datetime.now(),
            quiz_score=1 if is_correct else 0
        )
        db.add(new_progress)
        db.commit()
    
    return {"is_correct": is_correct}

@router.get("/", response_model=UserProgressResponse)
async def get_user_progress(db: Session = Depends(get_db)):
    """
    Get all progress for the current user.
    """
    # In a real implementation, get user_id from auth
    user_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
    
    progress_entries = db.query(UserProgress).filter(UserProgress.user_id == user_id).all()
    
    return {
        "user_id": user_id,
        "progress": [
            {
                "progress_id": entry.progress_id,
                "module_id": entry.module_id,
                "completed_at": entry.completed_at.isoformat(),
                "quiz_score": entry.quiz_score
            }
            for entry in progress_entries
        ]
    }