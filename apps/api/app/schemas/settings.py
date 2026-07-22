"""Settings schemas.

Two changes worth calling out.

**Enums instead of strings.** `default_difficulty_level` was `str` with a length
bound, so `"BEGINNER"` passed validation and then violated
`ck_user_settings_default_difficulty_level` — a 500. Same defect as the authoring
router's `level`, same fix.

**URLs are validated.** `website` and `profile_picture_url` were free strings
rendered by the client as a link and an `<img src>`. `javascript:alert(1)` in an
href is stored XSS in any UI that does not re-check, and the API should not be
relying on every client to do so.
"""

from datetime import datetime
from urllib.parse import urlparse
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..models.enums import TutorialLevel

# Matches the signup schema. It was 72 here — a bcrypt limit copied into an app
# that hashes with pbkdf2_sha256 — which meant a user who signed up with a
# 100-character password got a 422 on `current_password` and could never change
# it.
MAX_PASSWORD_LENGTH = 128
MIN_PASSWORD_LENGTH = 8

SAFE_URL_SCHEMES = frozenset({"http", "https"})


def _validate_display_url(value: str | None) -> str | None:
    """Reject anything that is not an ordinary web URL.

    `javascript:`, `data:` and `vbscript:` are the ones that matter — they
    execute when the value lands in an `href` or `src`.
    """
    if value is None or not value.strip():
        return None

    url = value.strip()
    parsed = urlparse(url)

    if parsed.scheme.lower() not in SAFE_URL_SCHEMES:
        raise ValueError("URL must start with http:// or https://")
    if not parsed.netloc:
        raise ValueError("URL is not valid.")
    return url


class ConnectedAccount(BaseModel):
    """**Read-only.** Server-managed, and no longer accepted on update.

    It was writable, so a user could assert any linked account they liked —
    including a GitHub identity they do not control. Nothing consumed it yet, but
    OAuth (docs/DECISIONS.md D10) will, and a user-writable claim about identity
    is a bad thing to inherit.
    """

    id: int
    name: str
    connected: bool
    username: str | None = None


class ProfileSettingsUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    bio: str | None = Field(default=None, max_length=2000)
    location: str | None = Field(default=None, max_length=200)
    website: str | None = Field(default=None, max_length=500)
    profile_picture_url: str | None = Field(default=None, max_length=1000)

    _check_website = field_validator("website")(_validate_display_url)
    _check_picture = field_validator("profile_picture_url")(_validate_display_url)


class ProfileSettingsResponse(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    bio: str | None = None
    location: str | None = None
    website: str | None = None
    profile_picture_url: str | None = None
    connected_accounts: list[ConnectedAccount] = Field(default_factory=list)


class NotificationSettingsUpdate(BaseModel):
    email_notifications_enabled: bool | None = None
    tutorial_completions: bool | None = None
    new_features: bool | None = None
    weekly_digest: bool | None = None
    browser_notifications: bool | None = None


class NotificationSettingsResponse(BaseModel):
    email_notifications_enabled: bool
    tutorial_completions: bool
    new_features: bool
    weekly_digest: bool
    browser_notifications: bool

    model_config = ConfigDict(from_attributes=True)


class AppearanceSettingsUpdate(BaseModel):
    language: str | None = Field(default=None, min_length=2, max_length=10)
    code_editor_theme: str | None = Field(default=None, min_length=1, max_length=50)


class AppearanceSettingsResponse(BaseModel):
    language: str
    code_editor_theme: str

    model_config = ConfigDict(from_attributes=True)


class LearningSettingsUpdate(BaseModel):
    default_difficulty_level: TutorialLevel | None = None
    daily_learning_goal: int | None = Field(default=None, ge=1, le=1440)
    auto_play_next_module: bool | None = None
    show_code_hints: bool | None = None
    quiz_mode: bool | None = None


class LearningSettingsResponse(BaseModel):
    default_difficulty_level: TutorialLevel
    daily_learning_goal: int
    auto_play_next_module: bool
    show_code_hints: bool
    quiz_mode: bool

    model_config = ConfigDict(from_attributes=True)


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=MAX_PASSWORD_LENGTH)
    new_password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)
    confirm_new_password: str = Field(min_length=1, max_length=MAX_PASSWORD_LENGTH)


class PasswordChangeResponse(BaseModel):
    message: str


class AccountDeleteRequest(BaseModel):
    """Deleting an account is irreversible and cascades to every tutorial the
    user owns, so it re-authenticates rather than trusting the bearer token
    alone. The old endpoint took no body at all."""

    current_password: str = Field(min_length=1, max_length=MAX_PASSWORD_LENGTH)


class UserSettingsResponse(BaseModel):
    user_id: UUID
    profile: ProfileSettingsResponse
    notifications: NotificationSettingsResponse
    appearance: AppearanceSettingsResponse
    learning: LearningSettingsResponse
    sessions_valid_from: datetime | None = None
