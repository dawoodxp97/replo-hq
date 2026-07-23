"""Dashboard schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from ..models.enums import RunStatus

# One completed module is treated as this much study time. A guess, and labelled
# as one — nothing measures actual time on page, so "learning hours" is a module
# count in disguise. Kept because the UI shows it; see the note in CLAUDE.md.
HOURS_PER_MODULE = 0.5


class DashboardStats(BaseModel):
    tutorials_generated: int
    learning_hours: float
    current_streak: int
    completed_tutorials: int
    total_hours_this_week: float
    # Echoed back so the client can tell which day boundary produced the streak.
    timezone: str


class ActivityCell(BaseModel):
    day: str
    hour: int
    value: int


class WeeklyActivityResponse(BaseModel):
    activities: list[ActivityCell]
    timezone: str


class TutorialStatusCounts(BaseModel):
    completed: int
    in_progress: int
    not_started: int


class TutorialStatusResponse(BaseModel):
    status: TutorialStatusCounts


class RecentActivityItem(BaseModel):
    instance_id: UUID
    repo_id: UUID | None = None
    repo_name: str
    repo_url: str
    status: RunStatus
    generation_progress: int
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    tutorial_id: UUID | None = None


class RecentActivityResponse(BaseModel):
    activities: list[RecentActivityItem]
