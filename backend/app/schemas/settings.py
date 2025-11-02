# ./backend/app/schemas/settings.py
from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


# Connected Account Schema
class ConnectedAccount(BaseModel):
    id: int
    name: str
    connected: bool
    username: Optional[str] = None


# Profile Settings Schemas
class ProfileSettingsUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    profile_picture_url: Optional[str] = None
    connected_accounts: Optional[List[ConnectedAccount]] = None


class ProfileSettingsResponse(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    profile_picture_url: Optional[str] = None
    connected_accounts: Optional[List[ConnectedAccount]] = None


# Notification Settings Schemas
class NotificationSettingsUpdate(BaseModel):
    email_notifications_enabled: Optional[bool] = None
    tutorial_completions: Optional[bool] = None
    new_features: Optional[bool] = None
    weekly_digest: Optional[bool] = None
    browser_notifications: Optional[bool] = None


class NotificationSettingsResponse(BaseModel):
    email_notifications_enabled: bool
    tutorial_completions: bool
    new_features: bool
    weekly_digest: bool
    browser_notifications: bool


# Appearance Settings Schemas
class AppearanceSettingsUpdate(BaseModel):
    language: Optional[str] = Field(None, min_length=2, max_length=10)
    code_editor_theme: Optional[str] = Field(None, min_length=1, max_length=50)


class AppearanceSettingsResponse(BaseModel):
    language: str
    code_editor_theme: str


# Learning Settings Schemas
class LearningSettingsUpdate(BaseModel):
    default_difficulty_level: Optional[str] = Field(None, min_length=1, max_length=20)
    daily_learning_goal: Optional[int] = Field(None, ge=1, le=1440)  # 1 minute to 24 hours
    auto_play_next_module: Optional[bool] = None
    show_code_hints: Optional[bool] = None
    quiz_mode: Optional[bool] = None


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
    profile: Optional[ProfileSettingsResponse] = None
    notifications: Optional[NotificationSettingsResponse] = None
    appearance: Optional[AppearanceSettingsResponse] = None
    learning: Optional[LearningSettingsResponse] = None
