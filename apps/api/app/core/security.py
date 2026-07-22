from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from .config import settings

# Previously: os.environ.get("SECRET_KEY", "a_very_secret_key_fallback") — while
# .env defined JWT_SECRET_KEY. Every token was signed with the public fallback.
SECRET_KEY = settings.jwt_secret_key.get_secret_value()
ALGORITHM = settings.jwt_algorithm

# Was 7 days access / 1 day refresh — inverted, which made refresh pointless.
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = settings.refresh_token_expire_days

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password, scheme="pbkdf2_sha256")


class TokenData(BaseModel):
    email: str | None = None
    # Issued-at, as an aware UTC datetime. Carried so a token can be checked
    # against `User.sessions_valid_from` — that comparison is the only thing that
    # can revoke an already-issued JWT, which is otherwise valid until it expires
    # no matter what happens to the account.
    issued_at: datetime | None = None


def _encode(data: dict, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(UTC)
    to_encode = {
        **data,
        "iat": now,
        # Millisecond issue time, alongside the standard second-granularity
        # `iat`. Revocation compares against this — see is_session_revoked for
        # why whole seconds are not precise enough to be correct in both
        # directions.
        "iat_ms": int(now.timestamp() * 1000),
        "exp": now + expires_delta,
        "type": token_type,
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    return _encode(data, "access", expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))


def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    return _encode(data, "refresh", expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))


def _decode(token: str, expected_type: str) -> TokenData | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

    if payload.get("type") != expected_type:
        return None

    email: str | None = payload.get("sub")
    if email is None:
        return None

    # Prefer the millisecond claim; fall back to standard `iat` for tokens
    # minted before it existed.
    raw_ms = payload.get("iat_ms")
    if raw_ms is not None:
        issued_at = datetime.fromtimestamp(raw_ms / 1000, tz=UTC)
    else:
        raw_iat = payload.get("iat")
        issued_at = datetime.fromtimestamp(raw_iat, tz=UTC) if raw_iat is not None else None

    return TokenData(email=email, issued_at=issued_at)


def decode_access_token(token: str) -> TokenData | None:
    return _decode(token, "access")


def decode_refresh_token(token: str) -> TokenData | None:
    return _decode(token, "refresh")


def is_session_revoked(token_data: TokenData, sessions_valid_from: datetime | None) -> bool:
    """True when this token predates the account's revocation point.

    A token minted before the last password change (or "sign out everywhere") is
    rejected even though its signature and expiry are perfectly valid.

    A token with no `iat` is treated as revoked once a cutoff exists: those are
    tokens issued before this mechanism shipped, and the safe reading of "I can't
    tell when this was issued" is to make the user sign in again.

    ## Why tokens carry a millisecond `iat_ms`

    Standard JWT `iat` is whole seconds, which is too coarse in **both**
    directions and each failure was caught by test:

    - Comparing at full precision locks the user out: the token issued by the
      login right after a password change is stamped `iat = 10` against a cutoff
      of `10.5`, so `10 < 10.5` rejects the credentials they were just handed.
      Every request after the change returned 401.
    - Flooring the cutoff to the second fixes that but lets a token issued at
      `10.1` — genuinely *before* a revocation at `10.5` — survive, because it
      also stamps `iat = 10`. Revocation silently failed to revoke.

    A millisecond claim removes the window rather than choosing which end to be
    wrong at. The residual is one millisecond, which is not a window anyone can
    aim at.
    """
    if sessions_valid_from is None:
        return False
    if token_data.issued_at is None:
        return True
    return token_data.issued_at < sessions_valid_from
