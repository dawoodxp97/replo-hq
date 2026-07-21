"""Repository service."""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.exceptions import InvalidInputError
from ..core.ownership import get_owned_repository
from ..core.pagination import PageParams, paginate
from ..models.enums import RepositoryStatus
from ..models.repositories import Repository
from ..models.tutorials import Tutorial
from ..utils import repo_utils

logger = logging.getLogger(__name__)


async def add_repository(db: AsyncSession, user_id: UUID, raw_url: str) -> Repository:
    """Add a repository to a user's account, or return their existing one.

    ## The bug this replaces

    The old handler looked up the repo by URL **with no user filter**:

        db.query(Repository).filter(Repository.github_url == url).first()

    and, on a hit, returned that row — including its `repo_id` — to whoever
    asked. Under the old global-unique constraint that row belonged to whichever
    user added it first, so any user submitting an already-known URL received
    another account's repository id, and every subsequent call using that id
    operated on a stranger's data.

    Removing the global unique constraint in the tenancy fix made this *more*
    reachable, since the query can now match any of several users' rows
    arbitrarily. The lookup below is scoped by `user_id`.
    """
    url = repo_utils.normalise_repo_url(raw_url)

    existing = (
        await db.execute(
            select(Repository).where(
                Repository.user_id == user_id,
                Repository.github_url == url,
            )
        )
    ).scalar_one_or_none()

    if existing is not None:
        return existing

    repo = Repository(
        user_id=user_id,
        github_url=url,
        name=repo_utils.repo_name_from_url(url),
        status=RepositoryStatus.PENDING,
    )
    db.add(repo)
    await db.commit()
    await db.refresh(repo)
    return repo


async def list_repositories(
    db: AsyncSession, user_id: UUID, params: PageParams
) -> tuple[list[Repository], int]:
    stmt = (
        select(Repository)
        .where(Repository.user_id == user_id)
        .order_by(Repository.created_at.desc())
    )
    rows, total = await paginate(db, stmt, params)
    return list(rows), total


async def get_repository_detail(
    db: AsyncSession, repo_id: UUID, user_id: UUID
) -> tuple[Repository, list[Tutorial]]:
    repo = await get_owned_repository(db, repo_id, user_id)

    tutorials = (
        (
            await db.execute(
                select(Tutorial)
                .where(Tutorial.repo_id == repo_id)
                .order_by(Tutorial.generated_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return repo, list(tutorials)


async def delete_repository(db: AsyncSession, repo_id: UUID, user_id: UUID) -> None:
    """Delete a repository and its clone.

    Tutorials cascade via the FK. The on-disk clone does not, and nothing used to
    remove it — so deleting a repo left its working tree under `/tmp` forever.
    """
    repo = await get_owned_repository(db, repo_id, user_id)
    await db.delete(repo)
    await db.commit()
    await repo_utils.remove_clone(repo_id)


async def get_file_tree(db: AsyncSession, repo_id: UUID, user_id: UUID) -> list[dict]:
    """Return the working-tree listing, cloning on demand if absent.

    Cloning inside a GET is not ideal — it can take a minute on first call. It
    stays for now because the frontend depends on it; moving it behind an
    explicit "prepare" job belongs with the Phase 3 pipeline work. It is at least
    no longer able to block the event loop while it happens.
    """
    repo = await get_owned_repository(db, repo_id, user_id)
    path = await repo_utils.clone_repository(repo.github_url, repo_id)
    return repo_utils.build_file_tree(path)


async def get_file_content(
    db: AsyncSession, repo_id: UUID, user_id: UUID, file_path: str
) -> tuple[str, int]:
    repo = await get_owned_repository(db, repo_id, user_id)

    path = repo_utils.get_repo_path(repo_id)
    if not path.exists():
        path = await repo_utils.clone_repository(repo.github_url, repo_id)

    # read_file resolves the path and raises if it escapes the clone root.
    return repo_utils.read_file(path, file_path)


async def set_status(db: AsyncSession, repo_id: UUID, status: RepositoryStatus) -> None:
    """Update status from the pipeline. No ownership check — the caller is the
    worker acting on its own job, not a user request."""
    repo = (
        await db.execute(select(Repository).where(Repository.repo_id == repo_id))
    ).scalar_one_or_none()
    if repo is None:
        raise InvalidInputError("Repository not found.")
    repo.status = status
    await db.commit()
