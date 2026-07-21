"""Centralised ownership resolution.

Previously every endpoint re-derived "is this row mine?" inline, each joining
back through `Repository.user_id` in its own way. That is a data leak with a
single forgotten `.filter()` — and a forgotten filter looks exactly like correct
code in review, because nothing is visibly missing.

Every access to a user-owned object goes through a function here. There is then
one place to audit, and one place to fix.

## Why these raise NotFound, never PermissionDenied

"Exists but is not yours" and "does not exist" return the **same** 404. A 403
confirms the id is real, which turns a sequential or guessable id into an
enumeration oracle: an attacker walks ids and learns exactly which ones exist.

`PermissionDeniedError` remains correct for operations on objects the caller can
legitimately see — a role or plan check — but never for ownership.

## Ownership chains

Nothing except `Repository` stores `user_id` directly, so ownership is derived:

    Repository  → user_id
    Tutorial    → Repository.user_id
    Module      → Tutorial → Repository.user_id
    Quiz        → Module → Tutorial → Repository.user_id
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.enums import TutorialVisibility
from ..models.modules import Module
from ..models.quizzes import Quiz
from ..models.repositories import Repository
from ..models.tutorials import Tutorial
from .exceptions import NotFoundError


async def get_owned_repository(db: AsyncSession, repo_id: UUID, user_id: UUID) -> Repository:
    repo = (
        await db.execute(
            select(Repository).where(
                Repository.repo_id == repo_id,
                Repository.user_id == user_id,
            )
        )
    ).scalar_one_or_none()

    if repo is None:
        raise NotFoundError("Repository not found.")
    return repo


async def get_owned_tutorial(db: AsyncSession, tutorial_id: UUID, user_id: UUID) -> Tutorial:
    tutorial = (
        await db.execute(
            select(Tutorial)
            .join(Repository, Tutorial.repo_id == Repository.repo_id)
            .where(
                Tutorial.tutorial_id == tutorial_id,
                Repository.user_id == user_id,
            )
        )
    ).scalar_one_or_none()

    if tutorial is None:
        raise NotFoundError("Tutorial not found.")
    return tutorial


async def get_readable_tutorial(
    db: AsyncSession,
    tutorial_id: UUID,
    user_id: UUID | None,
) -> Tutorial:
    """Fetch a tutorial the caller is allowed to *read*.

    Wider than `get_owned_tutorial`: public and unlisted tutorials are readable
    by anyone, including anonymous callers (`user_id=None`). This is what backs
    the public `/t/{slug}` pages — see docs/DECISIONS.md D8.

    Unlisted behaves like public here on purpose: "unlisted" means absent from
    /explore and the sitemap, not access-controlled. Anyone with the link can
    read it.
    """
    stmt = select(Tutorial).join(Repository, Tutorial.repo_id == Repository.repo_id)

    public_states = (TutorialVisibility.PUBLIC, TutorialVisibility.UNLISTED)

    if user_id is None:
        stmt = stmt.where(
            Tutorial.tutorial_id == tutorial_id,
            Tutorial.visibility.in_(public_states),
        )
    else:
        stmt = stmt.where(
            Tutorial.tutorial_id == tutorial_id,
            (Repository.user_id == user_id) | Tutorial.visibility.in_(public_states),
        )

    tutorial = (await db.execute(stmt)).scalar_one_or_none()
    if tutorial is None:
        raise NotFoundError("Tutorial not found.")
    return tutorial


async def get_owned_module(db: AsyncSession, module_id: UUID, user_id: UUID) -> Module:
    module = (
        await db.execute(
            select(Module)
            .join(Tutorial, Module.tutorial_id == Tutorial.tutorial_id)
            .join(Repository, Tutorial.repo_id == Repository.repo_id)
            .where(
                Module.module_id == module_id,
                Repository.user_id == user_id,
            )
        )
    ).scalar_one_or_none()

    if module is None:
        raise NotFoundError("Module not found.")
    return module


_READABLE = (TutorialVisibility.PUBLIC, TutorialVisibility.UNLISTED)


async def get_readable_module(db: AsyncSession, module_id: UUID, user_id: UUID) -> Module:
    """A module the caller may *read* — theirs, or one in a published tutorial.

    Progress needs this rather than `get_owned_module`. Reading a public tutorial
    and recording completion against it is the normal case once /explore exists,
    and ownership would reject every one of those writes.

    It is still a check: `POST /progress/complete_module` previously took a bare
    `module_id` and inserted a row with **no validation at all**, so any user
    could record progress against modules of other users' private tutorials — and
    `GET /progress` joins Module and Tutorial, so those titles came straight back
    in the response. A write endpoint turned into a read of private data.
    """
    module = (
        await db.execute(
            select(Module)
            .join(Tutorial, Module.tutorial_id == Tutorial.tutorial_id)
            .join(Repository, Tutorial.repo_id == Repository.repo_id)
            .where(
                Module.module_id == module_id,
                (Repository.user_id == user_id) | Tutorial.visibility.in_(_READABLE),
            )
        )
    ).scalar_one_or_none()

    if module is None:
        raise NotFoundError("Module not found.")
    return module


async def get_readable_quiz(db: AsyncSession, quiz_id: UUID, user_id: UUID) -> Quiz:
    """As `get_readable_module`, one level down. Backs quiz submission."""
    quiz = (
        await db.execute(
            select(Quiz)
            .join(Module, Quiz.module_id == Module.module_id)
            .join(Tutorial, Module.tutorial_id == Tutorial.tutorial_id)
            .join(Repository, Tutorial.repo_id == Repository.repo_id)
            .where(
                Quiz.quiz_id == quiz_id,
                (Repository.user_id == user_id) | Tutorial.visibility.in_(_READABLE),
            )
        )
    ).scalar_one_or_none()

    if quiz is None:
        raise NotFoundError("Quiz not found.")
    return quiz


async def get_owned_quiz(db: AsyncSession, quiz_id: UUID, user_id: UUID) -> Quiz:
    quiz = (
        await db.execute(
            select(Quiz)
            .join(Module, Quiz.module_id == Module.module_id)
            .join(Tutorial, Module.tutorial_id == Tutorial.tutorial_id)
            .join(Repository, Tutorial.repo_id == Repository.repo_id)
            .where(
                Quiz.quiz_id == quiz_id,
                Repository.user_id == user_id,
            )
        )
    ).scalar_one_or_none()

    if quiz is None:
        raise NotFoundError("Quiz not found.")
    return quiz


def owned_tutorials_stmt(user_id: UUID):
    """Base SELECT for "tutorials this user owns".

    Returned as a statement rather than results so callers can add filters,
    ordering and pagination without re-deriving the ownership join — which is
    where the filter tends to get dropped.
    """
    return (
        select(Tutorial)
        .join(Repository, Tutorial.repo_id == Repository.repo_id)
        .where(Repository.user_id == user_id)
    )
