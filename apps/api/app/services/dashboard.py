"""Dashboard service.

## The N+1

Three of the four endpoints looped over every tutorial the user owned, running
two queries per iteration:

    for tutorial_id in tutorial_ids:
        total_modules   = db.query(count(Module))...      # query
        module_ids      = db.query(Module.module_id)...   # query
        completed       = db.query(count(UserProgress))...# query

`/stats` and `/tutorial-status` each did this, so loading the dashboard was
`O(tutorials)` round trips — twice. `/recent-activity` did the same per instance.
All four are now single queries.

## The timezone split-brain

Streaks and "this week" were computed by comparing a **Postgres-binned** date
against a **Python-process-local** one:

    func.date(UserProgress.completed_at)   # binned in Postgres's TimeZone
    datetime.now().date()                  # the API container's local date

Those are different clocks. If the container's TZ is not the database's, "today"
is never in the list and the streak silently reports 0 forever.

Both are also wrong for the user. Binning in UTC, two sessions at 18:00 and 20:00
UTC are one day — but for a reader in Asia/Kolkata they are 23:30 Monday and
01:30 Tuesday, two days of their life. Verified against Postgres:

    distinct days, UTC binning: 1
    distinct days, IST binning: 2

So every date boundary here is computed **in Postgres, in the caller's timezone**,
which arrives as an IANA name from the client
(`Intl.DateTimeFormat().resolvedOptions().timeZone`). Python does no date maths
against the database at all.
"""

import logging
from datetime import date, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import Date, Integer, cast, func, literal_column, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.exceptions import InvalidInputError
from ..models.enums import RunStatus
from ..models.modules import Module
from ..models.orchestration import TutorialExecution, TutorialInstance
from ..models.repositories import Repository
from ..models.tutorials import Tutorial
from ..models.user_progress import UserProgress
from ..schemas.dashboard import (
    HOURS_PER_MODULE,
    ActivityCell,
    DashboardStats,
    RecentActivityItem,
    TutorialStatusCounts,
)

logger = logging.getLogger(__name__)

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Matches services/tutorial.py. The old dashboard used 4 steps × 25% while the
# tutorial router used 5 × 20%, so the same running generation showed two
# different percentages depending on which screen you were looking at.
TOTAL_STEPS = 5


def resolve_timezone(name: str | None) -> str:
    """Validate an IANA timezone name, defaulting to UTC.

    Validated rather than interpolated: the value reaches an `AT TIME ZONE`
    clause, and while it is passed as a bind parameter, an unknown name makes
    Postgres raise mid-query rather than return a clear error.
    """
    if not name:
        return "UTC"
    try:
        ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise InvalidInputError(f"Unknown timezone: {name!r}") from exc
    return name


def _local_date(column, tz: str):
    """`completed_at` rendered as a calendar date in the caller's timezone."""
    return cast(func.timezone(tz, column), Date)


async def _local_today(db: AsyncSession, tz: str) -> date:
    """Today's date in the caller's timezone, **from Postgres**.

    Deliberately not `datetime.now().date()`: that is the API container's local
    date, which is what made the old streak comparison compare two different
    clocks.
    """
    return (await db.execute(select(cast(func.timezone(tz, func.now()), Date)))).scalar_one()


# --- Stats ------------------------------------------------------------------


async def _tutorial_status_counts(db: AsyncSession, user_id: UUID) -> TutorialStatusCounts:
    """Completed / in-progress / not-started, in one query.

    Per tutorial: total modules, and how many the user has completed. The outer
    query buckets those two numbers.

    A tutorial with **no modules** counts as not-started — the old `/stats`
    skipped it entirely while `/tutorial-status` counted it, so the two endpoints
    disagreed about how many tutorials the user had.
    """
    module_count = (
        select(func.count(Module.module_id))
        .where(Module.tutorial_id == Tutorial.tutorial_id)
        .correlate(Tutorial)
        .scalar_subquery()
    )
    completed_count = (
        select(func.count(UserProgress.progress_id))
        .select_from(UserProgress)
        .join(Module, UserProgress.module_id == Module.module_id)
        .where(
            Module.tutorial_id == Tutorial.tutorial_id,
            UserProgress.user_id == user_id,
        )
        .correlate(Tutorial)
        .scalar_subquery()
    )

    per_tutorial = (
        select(
            module_count.label("total"),
            completed_count.label("done"),
        )
        .select_from(Tutorial)
        .join(Repository, Tutorial.repo_id == Repository.repo_id)
        .where(Repository.user_id == user_id)
        .subquery()
    )

    total = literal_column("total")
    done = literal_column("done")

    row = (
        await db.execute(
            select(
                func.count().filter((total > 0) & (done >= total)).label("completed"),
                func.count().filter((done > 0) & (done < total)).label("in_progress"),
                func.count().filter((total == 0) | (done == 0)).label("not_started"),
            ).select_from(per_tutorial)
        )
    ).one()

    return TutorialStatusCounts(
        completed=row.completed,
        in_progress=row.in_progress,
        not_started=row.not_started,
    )


async def _current_streak(db: AsyncSession, user_id: UUID, tz: str, today: date) -> int:
    """Consecutive days of activity ending today or yesterday, in the caller's tz.

    Gaps-and-islands, done in SQL. `date - row_number()` is constant across a run
    of consecutive dates and changes at every gap, so grouping by it yields the
    runs; the most recent group's size is the current streak.

    The alternative — pulling every distinct active day into Python and walking
    backwards — is what the old code did. It grows with account age and needs a
    bound to stay honest; this does not.
    """
    days = (
        select(func.distinct(_local_date(UserProgress.completed_at, tz)).label("d"))
        .where(UserProgress.user_id == user_id)
        .subquery()
    )

    d = literal_column("d")
    islands = (
        select(
            d,
            (d - cast(func.row_number().over(order_by=d), Integer)).label("island"),
        )
        .select_from(days)
        .subquery()
    )

    island = literal_column("island")
    latest = (
        await db.execute(
            select(
                func.max(literal_column("d")).label("last_day"),
                func.count().label("length"),
            )
            .select_from(islands)
            .group_by(island)
            .order_by(func.max(literal_column("d")).desc())
            .limit(1)
        )
    ).one_or_none()

    if latest is None or latest.last_day is None:
        return 0

    # Yesterday still counts: a streak should not be reported as broken at 00:01
    # simply because the user has not studied yet today.
    if latest.last_day < today - timedelta(days=1):
        return 0

    return latest.length


async def get_stats(db: AsyncSession, user_id: UUID, tz: str) -> DashboardStats:
    counts = await _tutorial_status_counts(db, user_id)

    repos_with_tutorials = (
        await db.execute(
            select(func.count(func.distinct(Repository.repo_id)))
            .select_from(Repository)
            .join(Tutorial, Repository.repo_id == Tutorial.repo_id)
            .where(Repository.user_id == user_id)
        )
    ).scalar_one()

    today = await _local_today(db, tz)
    week_start = today - timedelta(days=today.weekday())

    totals = (
        await db.execute(
            select(
                func.count(UserProgress.progress_id).label("all_time"),
                func.count(UserProgress.progress_id)
                .filter(_local_date(UserProgress.completed_at, tz) >= week_start)
                .label("this_week"),
            ).where(UserProgress.user_id == user_id)
        )
    ).one()

    return DashboardStats(
        tutorials_generated=repos_with_tutorials,
        learning_hours=round(totals.all_time * HOURS_PER_MODULE, 1),
        current_streak=await _current_streak(db, user_id, tz, today),
        completed_tutorials=counts.completed,
        total_hours_this_week=round(totals.this_week * HOURS_PER_MODULE, 1),
        timezone=tz,
    )


async def get_tutorial_status(db: AsyncSession, user_id: UUID) -> TutorialStatusCounts:
    return await _tutorial_status_counts(db, user_id)


# --- Weekly activity --------------------------------------------------------


async def get_weekly_activity(db: AsyncSession, user_id: UUID, tz: str) -> list[ActivityCell]:
    """The 7×24 heatmap, aggregated in Postgres.

    The old version fetched every progress row for the week and counted them in
    a Python loop. Both the day-of-week and the hour were read off a datetime
    whose timezone was whatever the driver returned, so a reader in IST saw their
    late-evening sessions land on the wrong day *and* the wrong hour.

    The full 168 cells are always returned, zeros included: it is a fixed-size
    grid, and a client should not have to synthesise the empty ones.
    """
    local = func.timezone(tz, UserProgress.completed_at)
    today = await _local_today(db, tz)
    week_start = today - timedelta(days=today.weekday())

    rows = (
        await db.execute(
            select(
                # ISO day-of-week: Monday=1. `dow` would be Sunday=0 and shift
                # the whole grid by a day.
                cast(func.extract("isodow", local), Integer).label("dow"),
                cast(func.extract("hour", local), Integer).label("hour"),
                func.count().label("value"),
            )
            .where(
                UserProgress.user_id == user_id,
                _local_date(UserProgress.completed_at, tz) >= week_start,
            )
            .group_by("dow", "hour")
        )
    ).all()

    counts = {(r.dow, r.hour): r.value for r in rows}

    return [
        ActivityCell(day=name, hour=hour, value=counts.get((index + 1, hour), 0))
        for index, name in enumerate(DAY_NAMES)
        for hour in range(24)
    ]


# --- Recent activity --------------------------------------------------------


async def get_recent_activity(
    db: AsyncSession, user_id: UUID, limit: int
) -> list[RecentActivityItem]:
    """Recent generations, one query.

    The old version ran a repository lookup, a tutorial lookup and sometimes an
    execution lookup **per instance** — up to 3N queries for an N-row list whose
    `limit` was an uncapped query parameter, so `?limit=100000` was 300,000
    round trips.
    """
    # LATERAL, not a plain join. A repository can own several tutorials, and
    # joining them directly would emit one row per tutorial — silently turning a
    # 10-item activity list into 30 duplicated entries. `LIMIT 1` inside the
    # lateral keeps it one row per instance.
    latest_execution = (
        select(
            TutorialExecution.current_step_order.label("current_step_order"),
            TutorialExecution.error_message.label("error_message"),
        )
        .where(TutorialExecution.tutorial_instance_id == TutorialInstance.id)
        .order_by(TutorialExecution.started_at.desc())
        .limit(1)
        .correlate(TutorialInstance)
        .lateral("latest_execution")
    )

    latest_tutorial = (
        select(Tutorial.tutorial_id.label("tutorial_id"))
        .where(Tutorial.repo_id == Repository.repo_id)
        .order_by(Tutorial.generated_at.desc())
        .limit(1)
        .correlate(Repository)
        .lateral("latest_tutorial")
    )

    # TutorialInstance stores a raw URL with no FK to Repository, so the join
    # back is by URL. Both sides are normalised through
    # repo_utils.normalise_repo_url, which is what makes that match reliable.
    stmt = (
        select(
            TutorialInstance,
            Repository.repo_id,
            Repository.name.label("repo_name"),
            latest_tutorial.c.tutorial_id,
            latest_execution.c.current_step_order,
            latest_execution.c.error_message,
        )
        .select_from(TutorialInstance)
        .outerjoin(
            Repository,
            (Repository.github_url == TutorialInstance.repo_url)
            & (Repository.user_id == TutorialInstance.user_id),
        )
        # LATERAL joins carry their correlation in the subquery, so the ON
        # clause is vacuous — SQLAlchemy still requires one.
        .outerjoin(latest_tutorial, text("true"))
        .outerjoin(latest_execution, text("true"))
        .where(TutorialInstance.user_id == user_id)
        .order_by(TutorialInstance.created_at.desc())
        .limit(limit)
    )

    rows = (await db.execute(stmt)).all()

    activities = []
    for row in rows:
        instance = row.TutorialInstance
        progress = _progress_for(instance.status, row.current_step_order)

        activities.append(
            RecentActivityItem(
                instance_id=instance.id,
                repo_id=row.repo_id,
                repo_name=row.repo_name or instance.repo_url.rstrip("/").split("/")[-1],
                repo_url=instance.repo_url,
                status=instance.status,
                generation_progress=progress,
                # Surfaced at last: the old response hardcoded None with a
                # "Simplify for now" comment, so a failed generation showed as
                # failed with no reason anywhere in the UI.
                error_message=row.error_message,
                created_at=instance.created_at,
                updated_at=instance.updated_at or instance.created_at,
                tutorial_id=row.tutorial_id,
            )
        )
    return activities


def _progress_for(status: RunStatus, current_step_order: int | None) -> int:
    if status == RunStatus.COMPLETED:
        return 100
    if status == RunStatus.RUNNING and current_step_order:
        # Capped below 100 while running: the run is not done until the instance
        # says so, and showing 100% mid-flight reads as a hang.
        return min(int(current_step_order / TOTAL_STEPS * 100), 90)
    return 0
