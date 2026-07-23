"""Dashboard endpoints.

Every date boundary here — streaks, "this week", the activity heatmap — depends
on the **caller's** timezone, which the client passes as an IANA name:

    Intl.DateTimeFormat().resolvedOptions().timeZone   // "Asia/Kolkata"

Omitted, it defaults to UTC. See services/dashboard.py for why the previous
implementation could not be correct for anyone outside the server's timezone.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.dependencies import get_current_user_async
from ..db.session import get_async_db
from ..models.user import User
from ..schemas.dashboard import (
    DashboardStats,
    RecentActivityResponse,
    TutorialStatusResponse,
    WeeklyActivityResponse,
)
from ..services import dashboard as dashboard_service

router = APIRouter()

MAX_RECENT_ACTIVITY = 50


def timezone_param(
    tz: str | None = Query(
        default=None,
        max_length=64,
        description="IANA timezone name, e.g. Asia/Kolkata. Defaults to UTC.",
    ),
) -> str:
    return dashboard_service.resolve_timezone(tz)


@router.get("/stats", response_model=DashboardStats)
async def get_stats(
    tz: str = Depends(timezone_param),
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    return await dashboard_service.get_stats(db, current_user.user_id, tz)


@router.get("/weekly-activity", response_model=WeeklyActivityResponse)
async def get_weekly_activity(
    tz: str = Depends(timezone_param),
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """Fixed 7×24 grid, zeros included."""
    activities = await dashboard_service.get_weekly_activity(db, current_user.user_id, tz)
    return WeeklyActivityResponse(activities=activities, timezone=tz)


@router.get("/tutorial-status", response_model=TutorialStatusResponse)
async def get_tutorial_status(
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """No timezone dependency — this is a count, not a date bucket."""
    return TutorialStatusResponse(
        status=await dashboard_service.get_tutorial_status(db, current_user.user_id)
    )


@router.get("/recent-activity", response_model=RecentActivityResponse)
async def get_recent_activity(
    limit: int = Query(default=10, ge=1, le=MAX_RECENT_ACTIVITY),
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """`limit` is capped. It was an unbounded `int` parameter feeding a loop that
    ran up to three queries per row."""
    activities = await dashboard_service.get_recent_activity(db, current_user.user_id, limit)
    return RecentActivityResponse(activities=activities)
