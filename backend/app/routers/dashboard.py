import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, case, func, or_
from sqlalchemy.orm import Session
from sqlalchemy.sql import extract

from .. import models
from ..core.dependencies import get_current_user
from ..db.session import get_db
from ..models.modules import Module
from ..models.repositories import Repository
from ..models.tutorial_generation import TutorialGeneration
from ..models.tutorials import Tutorial
from ..models.user_progress import UserProgress

router = APIRouter()
class DashboardStatsResponse(BaseModel):
    tutorials_generated: int
    learning_hours: float
    current_streak: int
    completed_tutorials: int
    total_hours_this_week: float

class WeeklyActivityData(BaseModel):
    day: str
    hour: int
    value: int

class WeeklyActivityResponse(BaseModel):
    activities: List[WeeklyActivityData]

class TutorialStatusData(BaseModel):
    completed: int
    in_progress: int
    not_started: int

class TutorialStatusResponse(BaseModel):
    status: TutorialStatusData

class RecentActivityItem(BaseModel):
    repo_id: uuid.UUID
    repo_name: str
    repo_url: str
    status: str
    generation_progress: Optional[int] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str
    tutorial_id: Optional[uuid.UUID] = None

class RecentActivityResponse(BaseModel):
    activities: List[RecentActivityItem]

# --- Helper Functions ---
def calculate_streak(user_id: uuid.UUID, db: Session) -> int:
    """Calculate the current learning streak in days."""
    # Get all completed modules with their completion dates
    completed_modules = db.query(
        func.date(UserProgress.completed_at).label('completion_date')
    ).filter(
        UserProgress.user_id == user_id
    ).distinct().order_by(
        func.date(UserProgress.completed_at).desc()
    ).all()
    
    if not completed_modules:
        return 0
    
    # Convert to list of dates
    dates = [row.completion_date for row in completed_modules]
    
    # Check if today or yesterday is in the list
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    # Start counting from today or yesterday
    if today in dates:
        current_date = today
    elif yesterday in dates:
        current_date = yesterday
    else:
        # If no activity in last 2 days, streak is broken
        return 0
    
    streak = 0
    check_date = current_date
    
    # Count consecutive days
    while check_date in dates:
        streak += 1
        check_date -= timedelta(days=1)
    
    return streak

def get_learning_hours(user_id: uuid.UUID, db: Session) -> float:
    """Calculate total learning hours based on completed modules."""
    # Estimate: Each module takes ~30 minutes = 0.5 hours
    completed_count = db.query(func.count(UserProgress.progress_id)).filter(
        UserProgress.user_id == user_id
    ).scalar() or 0
    
    return round(completed_count * 0.5, 1)

def get_weekly_hours(user_id: uuid.UUID, db: Session) -> float:
    """Calculate learning hours for the current week."""
    # Get start of week (Monday)
    today = datetime.now().date()
    days_since_monday = today.weekday()
    week_start = today - timedelta(days=days_since_monday)
    week_start_datetime = datetime.combine(week_start, datetime.min.time())
    
    # Count modules completed this week
    completed_count = db.query(func.count(UserProgress.progress_id)).filter(
        UserProgress.user_id == user_id,
        UserProgress.completed_at >= week_start_datetime
    ).scalar() or 0
    
    return round(completed_count * 0.5, 1)

# --- API Endpoints ---
@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics for the current user."""
    user_id = current_user.user_id
    
    # Tutorials generated: Count distinct repositories with tutorials
    tutorials_generated = db.query(func.count(func.distinct(Repository.repo_id))).join(
        Tutorial, Repository.repo_id == Tutorial.repo_id
    ).filter(
        Repository.user_id == user_id
    ).scalar() or 0
    
    # Learning hours (total)
    learning_hours = get_learning_hours(user_id, db)
    
    # Current streak
    current_streak = calculate_streak(user_id, db)
    
    # Completed tutorials: Count tutorials where user completed all modules
    # Get all tutorials for user
    user_tutorials = db.query(Tutorial.tutorial_id).join(
        Repository, Tutorial.repo_id == Repository.repo_id
    ).filter(
        Repository.user_id == user_id
    ).all()
    
    tutorial_ids = [t.tutorial_id for t in user_tutorials]
    
    if not tutorial_ids:
        completed_tutorials = 0
    else:
        # For each tutorial, check if all modules are completed
        completed_count = 0
        for tutorial_id in tutorial_ids:
            # Get total modules in tutorial
            total_modules = db.query(func.count(Module.module_id)).filter(
                Module.tutorial_id == tutorial_id
            ).scalar() or 0
            
            if total_modules == 0:
                continue
            
            # Get completed modules for this tutorial
            module_ids = db.query(Module.module_id).filter(
                Module.tutorial_id == tutorial_id
            ).all()
            module_ids_list = [m.module_id for m in module_ids]
            
            if not module_ids_list:
                continue
            
            completed_modules = db.query(func.count(UserProgress.progress_id)).filter(
                UserProgress.user_id == user_id,
                UserProgress.module_id.in_(module_ids_list)
            ).scalar() or 0
            
            if completed_modules == total_modules:
                completed_count += 1
        
        completed_tutorials = completed_count
    
    # Total hours this week
    total_hours_this_week = get_weekly_hours(user_id, db)
    
    return {
        "tutorials_generated": tutorials_generated,
        "learning_hours": learning_hours,
        "current_streak": current_streak,
        "completed_tutorials": completed_tutorials,
        "total_hours_this_week": total_hours_this_week
    }

@router.get("/weekly-activity", response_model=WeeklyActivityResponse)
def get_weekly_activity(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get weekly activity data (per day/hour)."""
    user_id = current_user.user_id
    
    # Get start of week (Monday)
    today = datetime.now().date()
    days_since_monday = today.weekday()
    week_start = today - timedelta(days=days_since_monday)
    week_start_datetime = datetime.combine(week_start, datetime.min.time())
    
    # Get all progress entries this week
    progress_entries = db.query(UserProgress).filter(
        UserProgress.user_id == user_id,
        UserProgress.completed_at >= week_start_datetime
    ).all()
    
    # Initialize activity map: {day: {hour: count}}
    activity_map = {}
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    for entry in progress_entries:
        completed_at = entry.completed_at
        day_name = days[completed_at.weekday()]
        hour = completed_at.hour
        
        if day_name not in activity_map:
            activity_map[day_name] = {}
        if hour not in activity_map[day_name]:
            activity_map[day_name][hour] = 0
        
        activity_map[day_name][hour] += 1
    
    # Convert to list format
    activities = []
    for day in days:
        for hour in range(24):
            value = activity_map.get(day, {}).get(hour, 0)
            activities.append({
                "day": day,
                "hour": hour,
                "value": value
            })
    
    return {"activities": activities}

@router.get("/tutorial-status", response_model=TutorialStatusResponse)
def get_tutorial_status(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get tutorial status breakdown (completed, in progress, not started)."""
    user_id = current_user.user_id
    
    # Get all tutorials for user
    user_tutorials = db.query(Tutorial.tutorial_id).join(
        Repository, Tutorial.repo_id == Repository.repo_id
    ).filter(
        Repository.user_id == user_id
    ).all()
    
    tutorial_ids = [t.tutorial_id for t in user_tutorials]
    
    completed = 0
    in_progress = 0
    not_started = 0
    
    for tutorial_id in tutorial_ids:
        # Get total modules in tutorial
        total_modules = db.query(func.count(Module.module_id)).filter(
            Module.tutorial_id == tutorial_id
        ).scalar() or 0
        
        if total_modules == 0:
            not_started += 1
            continue
        
        # Get completed modules for this tutorial
        module_ids = db.query(Module.module_id).filter(
            Module.tutorial_id == tutorial_id
        ).all()
        module_ids_list = [m.module_id for m in module_ids]
        
        if not module_ids_list:
            not_started += 1
            continue
        
        completed_modules = db.query(func.count(UserProgress.progress_id)).filter(
            UserProgress.user_id == user_id,
            UserProgress.module_id.in_(module_ids_list)
        ).scalar() or 0
        
        if completed_modules == 0:
            not_started += 1
        elif completed_modules == total_modules:
            completed += 1
        else:
            in_progress += 1
    
    return {
        "status": {
            "completed": completed,
            "in_progress": in_progress,
            "not_started": not_started
        }
    }

@router.get("/recent-activity", response_model=RecentActivityResponse)
def get_recent_activity(
    limit: int = 10,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recent repository activity (generations) with their status."""
    user_id = current_user.user_id
    
    # Get recent tutorial generations ordered by creation date
    recent_generations = db.query(TutorialGeneration).filter(
        TutorialGeneration.user_id == user_id
    ).order_by(
        TutorialGeneration.created_at.desc()
    ).limit(limit).all()
    
    activities = []
    for gen in recent_generations:
        # Get repository info
        repo = db.query(Repository).filter(
            Repository.repo_id == gen.repo_id
        ).first()
        
        if not repo:
            continue
        
        activities.append({
            "repo_id": gen.repo_id,
            "repo_name": repo.name or gen.repo_url.split('/')[-1],
            "repo_url": gen.repo_url,
            "status": gen.status,
            "generation_progress": gen.generation_progress,
            "error_message": gen.error_message,
            "created_at": gen.created_at.isoformat(),
            "updated_at": gen.updated_at.isoformat() if gen.updated_at else gen.created_at.isoformat(),
            "tutorial_id": gen.tutorial_id
        })
    
    return {"activities": activities}
