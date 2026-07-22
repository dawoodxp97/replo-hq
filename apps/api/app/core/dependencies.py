"""Auth dependencies.

Async versions are the target; the sync `get_current_user` stays until the last
router is converted. Every router still importing it is unconverted work.
"""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from .. import models
from ..core import security
from ..db.session import get_async_db, get_db
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


# --- Sync (legacy, being removed) -------------------------------------------


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.User:
    """Legacy sync dependency. Use get_current_user_async in new code."""
    token_data = security.decode_access_token(token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(models.User).filter(models.User.email == token_data.email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
