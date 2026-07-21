"""Progress schemas.

Previously eight inline models in `routers/progress.py`, several declaring
`completed_at: str` with `.isoformat()` called by hand at every construction
site.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from ..models.enums import TutorialLevel


class ProgressUpdate(BaseModel):
    module_id: UUID


class QuizSubmit(BaseModel):
    quiz_id: UUID
    submitted_answer: str


class ProgressResponse(BaseModel):
    progress_id: UUID
    module_id: UUID
    completed_at: datetime
    quiz_score: int | None = None

    model_config = ConfigDict(from_attributes=True)


class QuizResult(BaseModel):
    """Returned after an attempt.

    `correct_answer` is included **here and only here**. Revealing it in response
    to a submission is the point of the feature; revealing it in the quiz body
    beforehand is the leak (see `schemas/tutorial.py::QuizOption`).
    """

    is_correct: bool
    correct_answer: str | None = None
    module_id: UUID


class ModuleProgressDetail(BaseModel):
    progress_id: UUID
    module_id: UUID
    module_title: str
    module_order_index: int
    tutorial_id: UUID
    tutorial_title: str
    tutorial_level: TutorialLevel
    completed_at: datetime
    quiz_score: int | None = None


class TutorialProgressSummary(BaseModel):
    tutorial_id: UUID
    tutorial_title: str
    tutorial_level: TutorialLevel
    total_modules: int
    completed_modules: int
    progress_percentage: float
    average_quiz_score: float | None = None
    last_completed_at: datetime | None = None


class UserProgressStats(BaseModel):
    total_modules_completed: int
    total_quizzes_attempted: int
    total_quizzes_correct: int
    average_quiz_score: float
    total_tutorials_with_progress: int
    last_activity_at: datetime | None = None
