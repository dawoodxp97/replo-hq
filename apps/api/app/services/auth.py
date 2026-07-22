"""Authentication service.

Owns signup, login and refresh. Raises `AppError` subclasses, never
`HTTPException` — so the same code path works from a worker, a script or a test
with no HTTP involved.
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core import security
from ..core.exceptions import AuthenticationError, ConflictError
from ..models.user import User
from ..schemas.user import Token, UserCreate

logger = logging.getLogger(__name__)

# A real hash, verified against when no user matches, so a failed login costs the
# same time whether or not the address exists. See `authenticate`.
_DUMMY_HASH = security.get_password_hash("dummy-password-for-constant-time-compare")


def normalise_email(email: str) -> str:
    return email.strip().lower()


async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    """Register a new user. Email is already normalised by the schema."""
    existing = (
        await db.execute(select(User).where(User.email == user_in.email))
    ).scalar_one_or_none()

    if existing is not None:
        # Signup is one of the few places existence genuinely cannot be hidden —
        # the user must be told the address is taken. The mitigation is rate
        # limiting on this endpoint, not a vaguer message.
        raise ConflictError("That email is already registered.")

    user = User(
        email=user_in.email,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        hashed_password=security.get_password_hash(user_in.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate(db: AsyncSession, email: str, password: str) -> User:
    """Verify credentials and return the user.

    ## Timing

    The previous implementation was `if not user or not verify_password(...)`.
    Python short-circuits, so a request for a **non-existent** address skipped
    the KDF entirely and returned in microseconds, while an existing address paid
    the full pbkdf2 cost. That difference is measurable over the network and
    turns login into an email-enumeration oracle.

    Here the KDF always runs — against `_DUMMY_HASH` when there is no user, or no
    stored password — so all failures cost roughly the same.
    """
    email = normalise_email(email)
    user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()

    stored_hash = user.hashed_password if user is not None else None

    if stored_hash is None:
        # No such user, or an OAuth-only account with no password set. Burn the
        # same CPU, then fail identically.
        security.verify_password(password, _DUMMY_HASH)
        raise AuthenticationError("Incorrect email or password.")

    if not security.verify_password(password, stored_hash):
        raise AuthenticationError("Incorrect email or password.")

    if not user.is_active:
        raise AuthenticationError("This account has been deactivated.")

    # Transparently upgrade the hash if the configured scheme has moved on.
    try:
        if security.pwd_context.needs_update(stored_hash):
            user.hashed_password = security.get_password_hash(password)
            await db.commit()
            await db.refresh(user)
    except Exception:
        # Non-fatal: the user is authenticated either way. Logged rather than
        # swallowed silently — the original code was a bare `except: pass`, so a
        # permanently failing rehash would never have been noticed.
        logger.warning("Password hash upgrade failed for user %s", user.user_id, exc_info=True)

    return user


def issue_tokens(user: User) -> Token:
    return Token(
        access_token=security.create_access_token(data={"sub": user.email}),
        refresh_token=security.create_refresh_token(data={"sub": user.email}),
    )


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> tuple[User, Token]:
    """Exchange a refresh token for a new pair.

    `decode_refresh_token` rejects an access token presented here, because the
    two carry different `type` claims — without that check a leaked access token
    could be traded for a long-lived refresh token.

    Not yet implemented: refresh-token rotation with reuse detection. Tokens
    remain valid until they expire, so a stolen one is usable for its full
    lifetime. Tracked for the auth hardening pass; it needs a token store, which
    is a bigger change than this slice.

    The `sessions_valid_from` check below is the partial mitigation: a password
    change or "sign out everywhere" invalidates every outstanding refresh token
    at once. **This endpoint is the one that matters** — without the check here,
    revocation would expire the 30-minute access tokens and then hand out fresh
    ones for the next 30 days.
    """
    token_data = security.decode_refresh_token(refresh_token)
    if token_data is None:
        raise AuthenticationError("Invalid or expired refresh token.")

    user = (
        await db.execute(select(User).where(User.email == token_data.email))
    ).scalar_one_or_none()

    if user is None or not user.is_active:
        raise AuthenticationError("Invalid or expired refresh token.")

    if security.is_session_revoked(token_data, user.sessions_valid_from):
        raise AuthenticationError("Invalid or expired refresh token.")

    return user, issue_tokens(user)
