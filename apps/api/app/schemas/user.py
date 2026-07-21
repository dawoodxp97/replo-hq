from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# 128 rather than the old 72. The 72-byte cap was a **bcrypt** limit, but this
# app hashes with pbkdf2_sha256, which has no such restriction — it was copied
# from a bcrypt config and was never doing anything. A bound still exists so a
# multi-megabyte password can't be used to burn CPU in the KDF.
MAX_PASSWORD_LENGTH = 128
MIN_PASSWORD_LENGTH = 8


class UserPublic(BaseModel):
    """A user as returned to that user. Never includes password material."""

    user_id: UUID
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    is_active: bool = True
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    email: EmailStr
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)

    @field_validator("email")
    @classmethod
    def _normalise_email(cls, v: str) -> str:
        """Lowercase and trim.

        Without this, `Foo@example.com` and `foo@example.com` become two separate
        accounts, and only the exact casing typed at signup can log in. Email
        local-parts are technically case-sensitive; no mainstream provider treats
        them that way and no user expects it.
        """
        return v.strip().lower()


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenWithUser(Token):
    """Login/refresh response. Bundling the user saves the client an immediate
    follow-up request just to render a header."""

    user: UserPublic
