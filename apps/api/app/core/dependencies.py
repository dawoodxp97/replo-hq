"""Auth dependencies.

Fully async. The sync `get_current_user` was removed once the last router
converted — it had no callers left and a lingering sync auth dependency is a
footgun: a new endpoint could grab it and silently reintroduce blocking DB IO on
the event loop.

The sync **session** (`SessionLocal`) still exists in `db/session.py` for the ARQ
worker and orchestrator, which are Phase 3's conversion.
"""

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models
from ..core import security
from ..db.session import get_async_db
from .exceptions import AuthenticationError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/user/login")
# auto_error=False so a missing token yields None instead of a 401 — that is what
# makes optional authentication possible on public endpoints.
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/user/login", auto_error=False)


# --- Async (target) ---------------------------------------------------------


async def get_current_user_async(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_db),
) -> models.User:
    token_data = security.decode_access_token(token)
    if token_data is None:
        raise AuthenticationError("Could not validate credentials.")

    user = (
        await db.execute(select(models.User).where(models.User.email == token_data.email))
    ).scalar_one_or_none()

    if user is None:
        # Same message as an invalid token: distinguishing "bad token" from
        # "valid token, no such user" tells an attacker which emails exist.
        raise AuthenticationError("Could not validate credentials.")

    if not user.is_active:
        raise AuthenticationError("This account has been deactivated.")

    if security.is_session_revoked(token_data, user.sessions_valid_from):
        raise AuthenticationError("This session has expired. Please sign in again.")

    return user


async def get_optional_user(
    token: str | None = Depends(optional_oauth2_scheme),
    db: AsyncSession = Depends(get_async_db),
) -> models.User | None:
    """Resolve the caller if authenticated, else None. Never raises.

    Backs endpoints that serve both audiences — a public tutorial page renders
    for anonymous visitors, and shows owner controls when the owner happens to be
    signed in. An invalid or expired token is treated as anonymous rather than an
    error, so a stale token in a browser tab still renders the public view.
    """
    if not token:
        return None

    token_data = security.decode_access_token(token)
    if token_data is None:
        return None

    user = (
        await db.execute(select(models.User).where(models.User.email == token_data.email))
    ).scalar_one_or_none()

    if user is None or not user.is_active:
        return None
    if security.is_session_revoked(token_data, user.sessions_valid_from):
        return None
    return user


def get_request_id(request: Request) -> str:
    """The current request id, for handlers that want to echo it."""
    return getattr(request.state, "request_id", "-")
