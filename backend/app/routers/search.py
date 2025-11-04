# ./backend/app/routers/search.py
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from pydantic import BaseModel

from ..db.session import get_db
from ..core.dependencies import get_current_user
from .. import models
from ..models.repositories import Repository
from ..models.tutorials import Tutorial
from ..models.modules import Module
from ..models.quizzes import Quiz

router = APIRouter()

# --- Pydantic Models ---
class SearchEntityResponse(BaseModel):
    id: str
    label: str
    type: str  # 'repository' | 'tutorial' | 'module' | 'quiz'
    avatar: Optional[str] = None
    # For modules and quizzes, include parent tutorial_id for navigation
    tutorial_id: Optional[str] = None
    # For modules, include order_index to jump to specific module
    module_index: Optional[int] = None

# --- API Endpoints ---
@router.get("/entities", response_model=List[SearchEntityResponse])
async def search_entities(
    query: str = Query(..., min_length=1, description="Search query string"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search across all entities (repositories, tutorials, modules, quizzes).
    Returns a unified list of search results with metadata.
    Only searches entities accessible to the current user.
    """
    if not query or len(query.strip()) == 0:
        return []
    
    search_term = f"%{query.strip().lower()}%"
    results: List[SearchEntityResponse] = []
    
    # 1. Search Repositories (owned by user)
    repositories = db.query(Repository).filter(
        and_(
            Repository.user_id == current_user.user_id,
            or_(
                Repository.name.ilike(search_term),
                Repository.description.ilike(search_term),
                Repository.github_url.ilike(search_term)
            )
        )
    ).limit(10).all()
    
    for repo in repositories:
        results.append(SearchEntityResponse(
            id=str(repo.repo_id),
            label=repo.name or repo.github_url.split('/')[-1].replace('.git', ''),
            type="repository",
            avatar=None,
            tutorial_id=None,
            module_index=None
        ))
    
    # 2. Search Tutorials (from user's repositories)
    tutorials = db.query(Tutorial).join(
        Repository, Tutorial.repo_id == Repository.repo_id
    ).filter(
        and_(
            Repository.user_id == current_user.user_id,
            or_(
                Tutorial.title.ilike(search_term),
                Tutorial.overview.ilike(search_term),
                Tutorial.level.ilike(search_term)
            )
        )
    ).limit(10).all()
    
    for tutorial in tutorials:
        # Get repository name for better context
        repo = db.query(Repository).filter(Repository.repo_id == tutorial.repo_id).first()
        repo_name = repo.name if repo else None
        label = f"{tutorial.title}"
        if repo_name:
            label = f"{tutorial.title} ({repo_name})"
        
        results.append(SearchEntityResponse(
            id=str(tutorial.tutorial_id),
            label=label,
            type="tutorial",
            avatar=None,
            tutorial_id=None,
            module_index=None
        ))
    
    # 3. Search Modules (from user's tutorials)
    modules = db.query(Module).join(
        Tutorial, Module.tutorial_id == Tutorial.tutorial_id
    ).join(
        Repository, Tutorial.repo_id == Repository.repo_id
    ).filter(
        and_(
            Repository.user_id == current_user.user_id,
            or_(
                Module.title.ilike(search_term),
                Module.content_markdown.ilike(search_term),
                Module.file_path.ilike(search_term)
            )
        )
    ).order_by(Module.tutorial_id, Module.order_index).limit(20).all()
    
    # Get tutorials for modules to build labels
    tutorial_ids = list(set([m.tutorial_id for m in modules]))
    tutorials_map = {t.tutorial_id: t for t in db.query(Tutorial).filter(Tutorial.tutorial_id.in_(tutorial_ids)).all()}
    repos_map = {}
    for tutorial in tutorials_map.values():
        if tutorial.repo_id not in repos_map:
            repo = db.query(Repository).filter(Repository.repo_id == tutorial.repo_id).first()
            repos_map[tutorial.repo_id] = repo
    
    for module in modules:
        tutorial = tutorials_map.get(module.tutorial_id)
        if tutorial:
            repo = repos_map.get(tutorial.repo_id)
            repo_name = repo.name if repo else None
            label = f"{module.title}"
            if tutorial.title:
                label = f"{module.title} - {tutorial.title}"
            if repo_name:
                label = f"{module.title} - {tutorial.title} ({repo_name})"
        else:
            label = module.title
        
        results.append(SearchEntityResponse(
            id=str(module.module_id),
            label=label,
            type="module",
            avatar=None,
            tutorial_id=str(module.tutorial_id),
            module_index=module.order_index - 1  # Convert to 0-based index for frontend
        ))
    
    # 4. Search Quizzes (from user's modules)
    quizzes = db.query(Quiz).join(
        Module, Quiz.module_id == Module.module_id
    ).join(
        Tutorial, Module.tutorial_id == Tutorial.tutorial_id
    ).join(
        Repository, Tutorial.repo_id == Repository.repo_id
    ).filter(
        and_(
            Repository.user_id == current_user.user_id,
            Quiz.question_text.ilike(search_term)
        )
    ).limit(20).all()
    
    # Get modules and tutorials for quizzes to build labels
    module_ids = list(set([q.module_id for q in quizzes]))
    modules_map = {m.module_id: m for m in db.query(Module).filter(Module.module_id.in_(module_ids)).all()}
    quiz_tutorial_ids = list(set([m.tutorial_id for m in modules_map.values()]))
    quiz_tutorials_map = {t.tutorial_id: t for t in db.query(Tutorial).filter(Tutorial.tutorial_id.in_(quiz_tutorial_ids)).all()}
    quiz_repos_map = {}
    for tutorial in quiz_tutorials_map.values():
        if tutorial.repo_id not in quiz_repos_map:
            repo = db.query(Repository).filter(Repository.repo_id == tutorial.repo_id).first()
            quiz_repos_map[tutorial.repo_id] = repo
    
    for quiz in quizzes:
        module = modules_map.get(quiz.module_id)
        if module:
            tutorial = quiz_tutorials_map.get(module.tutorial_id)
            if tutorial:
                repo = quiz_repos_map.get(tutorial.repo_id)
                repo_name = repo.name if repo else None
                # Truncate question text for label
                question_preview = quiz.question_text[:50] + "..." if len(quiz.question_text) > 50 else quiz.question_text
                label = f"Quiz: {question_preview}"
                if module.title:
                    label = f"{question_preview} - {module.title}"
                if tutorial.title:
                    label = f"{question_preview} - {module.title} ({tutorial.title})"
                if repo_name:
                    label = f"{question_preview} - {module.title} ({repo_name})"
            else:
                question_preview = quiz.question_text[:50] + "..." if len(quiz.question_text) > 50 else quiz.question_text
                label = f"Quiz: {question_preview} - {module.title}"
        else:
            question_preview = quiz.question_text[:50] + "..." if len(quiz.question_text) > 50 else quiz.question_text
            label = f"Quiz: {question_preview}"
        
        results.append(SearchEntityResponse(
            id=str(quiz.quiz_id),
            label=label,
            type="quiz",
            avatar=None,
            tutorial_id=str(module.tutorial_id) if module else None,
            module_index=module.order_index - 1 if module else None  # Convert to 0-based index for frontend
        ))
    
    # Sort results by type priority: repository > tutorial > module > quiz
    type_priority = {"repository": 0, "tutorial": 1, "module": 2, "quiz": 3}
    results.sort(key=lambda x: (type_priority.get(x.type, 99), x.label.lower()))
    
    # Limit total results to 30
    return results[:30]
