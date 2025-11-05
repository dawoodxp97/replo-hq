import uuid
from datetime import datetime
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
from ..models.tutorials import Tutorial
from ..models.user_progress import UserProgress

router = APIRouter()
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

class ModuleProgressDetail(BaseModel):
    progress_id: uuid.UUID
    module_id: uuid.UUID
    module_title: str
    module_order_index: int
    tutorial_id: uuid.UUID
    tutorial_title: str
    tutorial_level: str
    completed_at: str
    quiz_score: Optional[int] = None

class TutorialProgressSummary(BaseModel):
    tutorial_id: uuid.UUID
    tutorial_title: str
    tutorial_level: str
    total_modules: int
    completed_modules: int
    progress_percentage: float
    average_quiz_score: Optional[float] = None
    last_completed_at: Optional[str] = None

class UserProgressStats(BaseModel):
    total_modules_completed: int
    total_quizzes_attempted: int
    total_quizzes_correct: int
    average_quiz_score: float
    total_tutorials_with_progress: int
    last_activity_at: Optional[str] = None

class UserProgressResponse(BaseModel):
    user_id: uuid.UUID
    stats: UserProgressStats
    progress: List[ModuleProgressDetail]
    tutorials: List[TutorialProgressSummary]

# --- API Endpoints ---
@router.post("/complete_module", response_model=ProgressResponse)
async def mark_module_complete(
    progress: ProgressUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Called when a user clicks "Next" on a module.
    """
    user_id = current_user.user_id
    
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
async def submit_quiz_answer(
    submission: QuizSubmit,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check a user's quiz answer.
    """
    user_id = current_user.user_id
    
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
async def get_user_progress(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all progress for the current user with comprehensive details.
    Returns enriched progress data including module titles, tutorial info, and statistics.
    """
    user_id = current_user.user_id
    
    # Get all progress entries with joined module and tutorial data
    progress_entries = (
        db.query(
            UserProgress,
            Module,
            Tutorial
        )
        .join(Module, UserProgress.module_id == Module.module_id)
        .join(Tutorial, Module.tutorial_id == Tutorial.tutorial_id)
        .filter(UserProgress.user_id == user_id)
        .order_by(UserProgress.completed_at.desc())
        .all()
    )
    
    # Build detailed progress list
    progress_details = []
    tutorial_ids_set = set()
    
    for progress, module, tutorial in progress_entries:
        tutorial_ids_set.add(tutorial.tutorial_id)
        progress_details.append({
            "progress_id": progress.progress_id,
            "module_id": progress.module_id,
            "module_title": module.title,
            "module_order_index": module.order_index,
            "tutorial_id": tutorial.tutorial_id,
            "tutorial_title": tutorial.title,
            "tutorial_level": tutorial.level,
            "completed_at": progress.completed_at.isoformat(),
            "quiz_score": progress.quiz_score
        })
    
    # Calculate statistics
    total_modules_completed = len(progress_details)
    quizzes_attempted = sum(1 for p in progress_details if p["quiz_score"] is not None)
    quizzes_correct = sum(1 for p in progress_details if p["quiz_score"] == 1)
    quiz_scores = [p["quiz_score"] for p in progress_details if p["quiz_score"] is not None]
    average_quiz_score = sum(quiz_scores) / len(quiz_scores) * 100 if quiz_scores else 0.0
    total_tutorials_with_progress = len(tutorial_ids_set)
    
    last_activity = progress_details[0]["completed_at"] if progress_details else None
    
    stats = {
        "total_modules_completed": total_modules_completed,
        "total_quizzes_attempted": quizzes_attempted,
        "total_quizzes_correct": quizzes_correct,
        "average_quiz_score": round(average_quiz_score, 2),
        "total_tutorials_with_progress": total_tutorials_with_progress,
        "last_activity_at": last_activity
    }
    
    # Build tutorial summaries
    tutorial_summaries = []
    if tutorial_ids_set:
        for tutorial_id in tutorial_ids_set:
            # Get all modules for this tutorial
            tutorial_modules = db.query(Module).filter(Module.tutorial_id == tutorial_id).all()
            total_modules = len(tutorial_modules)
            
            # Get completed modules for this tutorial
            tutorial_module_ids = [m.module_id for m in tutorial_modules]
            completed_module_ids = {
                p["module_id"] for p in progress_details 
                if p["tutorial_id"] == tutorial_id
            }
            completed_count = sum(1 for mid in tutorial_module_ids if mid in completed_module_ids)
            
            # Get tutorial info
            tutorial = db.query(Tutorial).filter(Tutorial.tutorial_id == tutorial_id).first()
            if not tutorial:
                continue
            
            # Calculate average quiz score for this tutorial
            tutorial_progress = [p for p in progress_details if p["tutorial_id"] == tutorial_id]
            tutorial_quiz_scores = [p["quiz_score"] for p in tutorial_progress if p["quiz_score"] is not None]
            avg_tutorial_score = sum(tutorial_quiz_scores) / len(tutorial_quiz_scores) * 100 if tutorial_quiz_scores else None
            
            # Get last completed date for this tutorial
            tutorial_dates = [p["completed_at"] for p in tutorial_progress]
            last_tutorial_activity = max(tutorial_dates) if tutorial_dates else None
            
            progress_pct = (completed_count / total_modules * 100) if total_modules > 0 else 0.0
            
            tutorial_summaries.append({
                "tutorial_id": tutorial_id,
                "tutorial_title": tutorial.title,
                "tutorial_level": tutorial.level,
                "total_modules": total_modules,
                "completed_modules": completed_count,
                "progress_percentage": round(progress_pct, 2),
                "average_quiz_score": round(avg_tutorial_score, 2) if avg_tutorial_score is not None else None,
                "last_completed_at": last_tutorial_activity
            })
        
        # Sort by last completed date (most recent first)
        tutorial_summaries.sort(key=lambda x: x["last_completed_at"] or "", reverse=True)
    
    return {
        "user_id": user_id,
        "stats": stats,
        "progress": progress_details,
        "tutorials": tutorial_summaries
    }