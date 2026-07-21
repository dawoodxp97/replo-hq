# ./backend/app/schemas/settings.py
from uuid import UUID

from pydantic import BaseModel, Field


# Connected Account Schema
class ConnectedAccount(BaseModel):
    id: int
    name: str
    connected: bool
    username: str | None = None


# Profile Settings Schemas
class ProfileSettingsUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    bio: str | None = None
    location: str | None = None
    website: str | None = None
    profile_picture_url: str | None = None
    connected_accounts: list[ConnectedAccount] | None = None


class ProfileSettingsResponse(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    bio: str | None = None
    location: str | None = None
    website: str | None = None
    profile_picture_url: str | None = None
    connected_accounts: list[ConnectedAccount] | None = None


# Notification Settings Schemas
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


# Appearance Settings Schemas
class AppearanceSettingsUpdate(BaseModel):
    language: str | None = Field(None, min_length=2, max_length=10)
    code_editor_theme: str | None = Field(None, min_length=1, max_length=50)


class AppearanceSettingsResponse(BaseModel):
    language: str
    code_editor_theme: str


# Learning Settings Schemas
class LearningSettingsUpdate(BaseModel):
    default_difficulty_level: str | None = Field(None, min_length=1, max_length=20)
    daily_learning_goal: int | None = Field(None, ge=1, le=1440)  # 1 minute to 24 hours
    auto_play_next_module: bool | None = None
    show_code_hints: bool | None = None
    quiz_mode: bool | None = None


class LearningSettingsResponse(BaseModel):
    default_difficulty_level: str
    daily_learning_goal: int
    auto_play_next_module: bool
    show_code_hints: bool
    quiz_mode: bool


# Security Settings Schemas
class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=8, max_length=72)
    new_password: str = Field(min_length=8, max_length=72)
    confirm_new_password: str = Field(min_length=8, max_length=72)


class PasswordChangeResponse(BaseModel):
    message: str


# Combined Settings Response (for getting all settings at once)
class UserSettingsResponse(BaseModel):
    user_id: UUID
    profile: ProfileSettingsResponse | None = None
    notifications: NotificationSettingsResponse | None = None
    appearance: AppearanceSettingsResponse | None = None
    learning: LearningSettingsResponse | None = None
