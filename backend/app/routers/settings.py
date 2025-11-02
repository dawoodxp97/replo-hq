# ./backend/app/routers/settings.py
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..core.dependencies import get_current_user
from ..db.session import get_db

router = APIRouter()


def get_or_create_user_settings(
    user: models.User,
    db: Session
) -> models.UserSettings:
    """
    Get user settings or create default settings if they don't exist.
    """
    if user.settings:
        return user.settings
    
    # Create default settings
    default_settings = models.UserSettings(
        user_id=user.user_id,
        email_notifications_enabled=True,
        tutorial_completions=True,
        new_features=True,
        weekly_digest=True,
        browser_notifications=True,
        language="en",
        code_editor_theme="github-dark",
        default_difficulty_level="beginner",
        daily_learning_goal=10,
        auto_play_next_module=True,
        show_code_hints=True,
        quiz_mode=True,
    )
    db.add(default_settings)
    db.commit()
    db.refresh(default_settings)
    return default_settings


# --- Profile Settings Endpoints ---
@router.get("/settings/profile", response_model=schemas.ProfileSettingsResponse)
def get_profile_settings(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's profile settings.
    """
    settings = get_or_create_user_settings(current_user, db)
    
    return {
        "first_name": settings.first_name,
        "last_name": settings.last_name,
        "email": current_user.email,
        "bio": settings.bio,
        "location": settings.location,
        "website": settings.website,
        "profile_picture_url": settings.profile_picture_url,
        "connected_accounts": settings.connected_accounts or [],
    }


@router.put("/settings/profile", response_model=schemas.ProfileSettingsResponse)
def update_profile_settings(
    profile_update: schemas.ProfileSettingsUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user's profile settings.
    """
    settings = get_or_create_user_settings(current_user, db)
    
    # Update fields if provided
    if profile_update.first_name is not None:
        settings.first_name = profile_update.first_name
    if profile_update.last_name is not None:
        settings.last_name = profile_update.last_name
    if profile_update.email is not None:
        # Update email in User model as well
        current_user.email = profile_update.email
    if profile_update.bio is not None:
        settings.bio = profile_update.bio
    if profile_update.location is not None:
        settings.location = profile_update.location
    if profile_update.website is not None:
        settings.website = profile_update.website
    if profile_update.profile_picture_url is not None:
        settings.profile_picture_url = profile_update.profile_picture_url
    if profile_update.connected_accounts is not None:
        # Convert Pydantic models to dicts for JSON storage
        settings.connected_accounts = [
            account.model_dump() for account in profile_update.connected_accounts
        ]
    
    db.commit()
    db.refresh(settings)
    db.refresh(current_user)
    
    return {
        "first_name": settings.first_name,
        "last_name": settings.last_name,
        "email": current_user.email,
        "bio": settings.bio,
        "location": settings.location,
        "website": settings.website,
        "profile_picture_url": settings.profile_picture_url,
        "connected_accounts": settings.connected_accounts or [],
    }


# --- Notification Settings Endpoints ---
@router.get("/settings/notifications", response_model=schemas.NotificationSettingsResponse)
def get_notification_settings(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's notification settings.
    """
    settings = get_or_create_user_settings(current_user, db)
    
    return {
        "email_notifications_enabled": settings.email_notifications_enabled,
        "tutorial_completions": settings.tutorial_completions,
        "new_features": settings.new_features,
        "weekly_digest": settings.weekly_digest,
        "browser_notifications": settings.browser_notifications,
    }


@router.put("/settings/notifications", response_model=schemas.NotificationSettingsResponse)
def update_notification_settings(
    notification_update: schemas.NotificationSettingsUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user's notification settings.
    """
    settings = get_or_create_user_settings(current_user, db)
    
    if notification_update.email_notifications_enabled is not None:
        settings.email_notifications_enabled = notification_update.email_notifications_enabled
    if notification_update.tutorial_completions is not None:
        settings.tutorial_completions = notification_update.tutorial_completions
    if notification_update.new_features is not None:
        settings.new_features = notification_update.new_features
    if notification_update.weekly_digest is not None:
        settings.weekly_digest = notification_update.weekly_digest
    if notification_update.browser_notifications is not None:
        settings.browser_notifications = notification_update.browser_notifications
    
    db.commit()
    db.refresh(settings)
    
    return {
        "email_notifications_enabled": settings.email_notifications_enabled,
        "tutorial_completions": settings.tutorial_completions,
        "new_features": settings.new_features,
        "weekly_digest": settings.weekly_digest,
        "browser_notifications": settings.browser_notifications,
    }


# --- Appearance Settings Endpoints ---
@router.get("/settings/appearance", response_model=schemas.AppearanceSettingsResponse)
def get_appearance_settings(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's appearance settings.
    """
    settings = get_or_create_user_settings(current_user, db)
    
    return {
        "language": settings.language,
        "code_editor_theme": settings.code_editor_theme,
    }


@router.put("/settings/appearance", response_model=schemas.AppearanceSettingsResponse)
def update_appearance_settings(
    appearance_update: schemas.AppearanceSettingsUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user's appearance settings.
    """
    settings = get_or_create_user_settings(current_user, db)
    
    if appearance_update.language is not None:
        settings.language = appearance_update.language
    if appearance_update.code_editor_theme is not None:
        settings.code_editor_theme = appearance_update.code_editor_theme
    
    db.commit()
    db.refresh(settings)
    
    return {
        "language": settings.language,
        "code_editor_theme": settings.code_editor_theme,
    }


# --- Learning Settings Endpoints ---
@router.get("/settings/learning", response_model=schemas.LearningSettingsResponse)
def get_learning_settings(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's learning settings.
    """
    settings = get_or_create_user_settings(current_user, db)
    
    return {
        "default_difficulty_level": settings.default_difficulty_level,
        "daily_learning_goal": settings.daily_learning_goal,
        "auto_play_next_module": settings.auto_play_next_module,
        "show_code_hints": settings.show_code_hints,
        "quiz_mode": settings.quiz_mode,
    }


@router.put("/settings/learning", response_model=schemas.LearningSettingsResponse)
def update_learning_settings(
    learning_update: schemas.LearningSettingsUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user's learning settings.
    """
    settings = get_or_create_user_settings(current_user, db)
    
    if learning_update.default_difficulty_level is not None:
        settings.default_difficulty_level = learning_update.default_difficulty_level
    if learning_update.daily_learning_goal is not None:
        settings.daily_learning_goal = learning_update.daily_learning_goal
    if learning_update.auto_play_next_module is not None:
        settings.auto_play_next_module = learning_update.auto_play_next_module
    if learning_update.show_code_hints is not None:
        settings.show_code_hints = learning_update.show_code_hints
    if learning_update.quiz_mode is not None:
        settings.quiz_mode = learning_update.quiz_mode
    
    db.commit()
    db.refresh(settings)
    
    return {
        "default_difficulty_level": settings.default_difficulty_level,
        "daily_learning_goal": settings.daily_learning_goal,
        "auto_play_next_module": settings.auto_play_next_module,
        "show_code_hints": settings.show_code_hints,
        "quiz_mode": settings.quiz_mode,
    }


# --- Security Settings Endpoints ---
@router.put("/settings/security/password", response_model=schemas.PasswordChangeResponse)
def change_password(
    password_change: schemas.PasswordChangeRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change user's password.
    Validates current password and updates to new password.
    """
    from ..core import security
    
    # Validate current password
    if not security.verify_password(password_change.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )
    
    # Validate new password matches confirmation
    if password_change.new_password != password_change.confirm_new_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="New password and confirmation do not match",
        )
    
    # Validate new password is different from current
    if password_change.current_password == password_change.new_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="New password must be different from current password",
        )
    
    # Update password
    current_user.hashed_password = security.get_password_hash(password_change.new_password)
    db.commit()
    db.refresh(current_user)
    
    return {"message": "Password updated successfully"}


@router.delete("/settings/security/account")
def delete_account(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete user account and all associated data.
    This is a destructive operation and should require additional confirmation in production.
    """
    # Delete user (this will cascade delete settings due to CASCADE on foreign key)
    db.delete(current_user)
    db.commit()
    
    return {"message": "Account deleted successfully"}


# --- Get All Settings (Optional convenience endpoint) ---
@router.get("/settings/all", response_model=schemas.UserSettingsResponse)
def get_all_settings(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all user settings at once.
    """
    settings = get_or_create_user_settings(current_user, db)
    
    return {
        "user_id": current_user.user_id,
        "profile": {
            "first_name": settings.first_name,
            "last_name": settings.last_name,
            "email": current_user.email,
            "bio": settings.bio,
            "location": settings.location,
            "website": settings.website,
            "profile_picture_url": settings.profile_picture_url,
            "connected_accounts": settings.connected_accounts or [],
        },
        "notifications": {
            "email_notifications_enabled": settings.email_notifications_enabled,
            "tutorial_completions": settings.tutorial_completions,
            "new_features": settings.new_features,
            "weekly_digest": settings.weekly_digest,
            "browser_notifications": settings.browser_notifications,
        },
        "appearance": {
            "language": settings.language,
            "code_editor_theme": settings.code_editor_theme,
        },
        "learning": {
            "default_difficulty_level": settings.default_difficulty_level,
            "daily_learning_goal": settings.daily_learning_goal,
            "auto_play_next_module": settings.auto_play_next_module,
            "show_code_hints": settings.show_code_hints,
            "quiz_mode": settings.quiz_mode,
        },
    }
