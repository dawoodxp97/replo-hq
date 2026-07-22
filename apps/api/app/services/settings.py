"""Settings service."""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..core import security
from ..core.exceptions import AuthenticationError, InvalidInputError
from ..models.repositories import Repository
from ..models.user import User
from ..models.user_settings import UserSettings
from ..schemas.settings import (
    AppearanceSettingsUpdate,
    LearningSettingsUpdate,
    NotificationSettingsUpdate,
    ProfileSettingsUpdate,
)
from ..utils import repo_utils

logger = logging.getLogger(__name__)

# Fields on User rather than UserSettings.
_USER_FIELDS = {"first_name", "last_name"}


async def get_or_create_settings(db: AsyncSession, user_id: UUID) -> UserSettings:
    """Fetch a user's settings row, creating it on first access.

    Two problems with the old version:

    **It lazy-loaded `user.settings`.** That works under the sync session and
    raises `MissingGreenlet` under the async one — a relationship access cannot
    emit IO from async context. Every settings endpoint would have failed at the
    first line on conversion.

    **It raced.** Check-then-insert against a UNIQUE `user_id`, so two concurrent
    requests from the same user — trivially, a settings page issuing four
    requests at once on first load — collided into an `IntegrityError`. Same
    defect and same fix as the progress slice.
    """
    existing = (
        await db.execute(select(UserSettings).where(UserSettings.user_id == user_id))
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    # Column defaults supply every value; nothing needs listing here.
    await db.execute(
        pg_insert(UserSettings)
        .values(user_id=user_id)
        .on_conflict_do_nothing(index_elements=["user_id"])
    )
    await db.commit()

    return (
        await db.execute(select(UserSettings).where(UserSettings.user_id == user_id))
    ).scalar_one()


async def update_profile(db: AsyncSession, user: User, body: ProfileSettingsUpdate) -> UserSettings:
    """`exclude_unset` so an omitted field is left alone and an explicit `null`
    clears it. The old `if x is not None` chain made those two indistinguishable,
    so a bio could be set but never removed."""
    settings = await get_or_create_settings(db, user.user_id)

    for field, value in body.model_dump(exclude_unset=True).items():
        target = user if field in _USER_FIELDS else settings
        setattr(target, field, value)

    await db.commit()
    await db.refresh(settings)
    await db.refresh(user)
    return settings


async def _update_settings_fields(db: AsyncSession, user_id: UUID, body) -> UserSettings:
    settings = await get_or_create_settings(db, user_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(settings, field, value)
    await db.commit()
    await db.refresh(settings)
    return settings


async def update_notifications(
    db: AsyncSession, user_id: UUID, body: NotificationSettingsUpdate
) -> UserSettings:
    return await _update_settings_fields(db, user_id, body)


async def update_appearance(
    db: AsyncSession, user_id: UUID, body: AppearanceSettingsUpdate
) -> UserSettings:
    return await _update_settings_fields(db, user_id, body)


async def update_learning(
    db: AsyncSession, user_id: UUID, body: LearningSettingsUpdate
) -> UserSettings:
    return await _update_settings_fields(db, user_id, body)


# --- Security ---------------------------------------------------------------


def _require_password(user: User, password: str) -> None:
    """Re-authenticate for a sensitive operation.

    `hashed_password` is nullable — an OAuth user has none. `verify_password`
    happens to return False rather than raising on `None`, so the old code gave
    such a user "Current password is incorrect", which is both wrong and
    unactionable. They are told what is actually true instead.
    """
    if user.hashed_password is None:
        raise InvalidInputError(
            "This account signs in with a connected provider and has no password set."
        )

    if not security.verify_password(password, user.hashed_password):
        raise AuthenticationError("Current password is incorrect.")


async def change_password(
    db: AsyncSession, user: User, current: str, new: str, confirm: str
) -> None:
    """Change the password and revoke every existing session.

    The revocation is the part that was missing. Access tokens live 30 minutes
    and refresh tokens 30 days, so before this a password change left an
    attacker holding a stolen refresh token with a month of continued access —
    while the user believed they had just locked them out.
    """
    _require_password(user, current)

    if new != confirm:
        raise InvalidInputError("New password and confirmation do not match.")
    if new == current:
        raise InvalidInputError("New password must be different from the current one.")

    user.hashed_password = security.get_password_hash(new)
    user.sessions_valid_from = datetime.now(UTC)
    await db.commit()

    logger.info("Password changed for user %s; all sessions revoked", user.user_id)


async def revoke_sessions(db: AsyncSession, user: User) -> datetime:
    """Sign out everywhere. Also the containment action for a leaked token."""
    cutoff = datetime.now(UTC)
    user.sessions_valid_from = cutoff
    await db.commit()
    logger.info("Sessions revoked for user %s", user.user_id)
    return cutoff


async def delete_account(db: AsyncSession, user: User, current_password: str) -> None:
    """Delete the account and everything cascading from it.

    Irreversible: repositories, tutorials, modules, quizzes, progress, settings,
    notifications and stored credentials all go with it via FK cascade. The old
    endpoint did this on a bare `DELETE` with no body — a bearer token alone was
    enough, and its own docstring admitted it "should require additional
    confirmation in production".

    On-disk clones do **not** cascade. They are removed here because "delete my
    account" that leaves the user's source code on our disk is a deletion in name
    only.
    """
    _require_password(user, current_password)

    user_id = user.user_id
    repo_ids = list(
        (await db.execute(select(Repository.repo_id).where(Repository.user_id == user_id)))
        .scalars()
        .all()
    )

    await db.delete(user)
    await db.commit()

    for repo_id in repo_ids:
        await repo_utils.remove_clone(repo_id)

    logger.info("Account %s deleted (%d clones removed)", user_id, len(repo_ids))
