# ./backend/app/core/notification_service.py
"""
Notification service for creating and managing user notifications.
"""
from typing import Optional, Union
from sqlalchemy.orm import Session
from datetime import datetime
import json
import uuid

from ..models import Notification, UserSettings


def create_notification(
    db: Session,
    user_id: Union[str, uuid.UUID],
    title: str,
    message: str,
    notification_type: str = "default",
    link: Optional[str] = None,
    metadata: Optional[dict] = None,
    check_settings: bool = True,
) -> Optional[Notification]:
    """
    Create a notification for a user.
    
    Args:
        db: Database session
        user_id: UUID of the user (can be string or UUID object)
        title: Notification title
        message: Notification message
        notification_type: Type of notification (success, info, warning, default)
        link: Optional link to navigate to when clicking the notification
        metadata: Optional metadata dictionary (will be stored as JSON)
        check_settings: If True, check user notification settings before creating
        
    Returns:
        Created Notification object or None if skipped
    """
    # Convert user_id to UUID if it's a string
    if isinstance(user_id, str):
        try:
            user_id_uuid = uuid.UUID(user_id)
        except ValueError:
            raise ValueError(f"Invalid user_id format: {user_id}")
    else:
        user_id_uuid = user_id
    
    # Check user notification settings if requested
    if check_settings:
        settings = db.query(UserSettings).filter(
            UserSettings.user_id == user_id_uuid
        ).first()
        
        if settings and not settings.browser_notifications:
            # User has disabled browser notifications, skip creation
            return None
    
    # Create notification
    notification = Notification(
        user_id=user_id_uuid,
        title=title,
        message=message,
        type=notification_type,
        link=link,
        notification_data=json.dumps(metadata) if metadata else None,
    )
    
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    return notification


def create_tutorial_generation_notification(
    db: Session,
    user_id: Union[str, uuid.UUID],
    repo_name: str,
    tutorial_id: Optional[str] = None,
    success: bool = True,
    error_message: Optional[str] = None,
) -> Optional[Notification]:
    """
    Create a notification for tutorial generation completion or failure.
    
    Args:
        db: Database session
        user_id: UUID of the user
        repo_name: Name of the repository
        tutorial_id: UUID of the tutorial (if successful)
        success: Whether generation was successful
        error_message: Error message if generation failed
        
    Returns:
        Created Notification object or None if skipped
    """
    if success:
        title = "Tutorial Generation Completed"
        message = f"Your tutorial for '{repo_name}' has been generated successfully!"
        notification_type = "success"
        link = f"/tutorial/{tutorial_id}" if tutorial_id else None
        metadata = {
            "tutorial_id": tutorial_id,
            "repo_name": repo_name,
            "event": "tutorial_generation_completed",
        }
    else:
        title = "Tutorial Generation Failed"
        message = f"Tutorial generation for '{repo_name}' failed. {error_message or 'Please try again.'}"
        notification_type = "warning"
        link = None
        metadata = {
            "repo_name": repo_name,
            "event": "tutorial_generation_failed",
            "error": error_message,
        }
    
    return create_notification(
        db=db,
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link,
        metadata=metadata,
        check_settings=True,
    )

