# ./backend/app/routers/notification.py
from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime

from ..db.session import get_db
from ..core.dependencies import get_current_user
from .. import models
from .. import schemas

router = APIRouter()


@router.get("", response_model=schemas.NotificationListResponse)
def get_notifications(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """
    Get all notifications for the current user.
    Returns notifications ordered by created_at descending.
    """
    # Get notifications for current user
    notifications = (
        db.query(models.Notification)
        .filter(models.Notification.user_id == current_user.user_id)
        .order_by(desc(models.Notification.created_at))
        .limit(limit)
        .offset(offset)
        .all()
    )
    
    # Count unread notifications
    unread_count = (
        db.query(models.Notification)
        .filter(
            models.Notification.user_id == current_user.user_id,
            models.Notification.read == False,
        )
        .count()
    )
    
    # Convert to response format
    notification_responses = []
    for notification in notifications:
        notification_responses.append(
            schemas.NotificationResponse(
                id=str(notification.notification_id),
                title=notification.title,
                message=notification.message,
                type=notification.type,
                created_at=notification.created_at.isoformat(),
                read=notification.read,
                link=notification.link,
            )
        )
    
    return schemas.NotificationListResponse(
        notifications=notification_responses,
        unread_count=unread_count,
    )


@router.put("/{notification_id}/read", response_model=schemas.MarkAsReadResponse)
def mark_notification_as_read(
    notification_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mark a specific notification as read.
    """
    try:
        # Convert string notification_id to UUID
        try:
            notification_uuid = uuid.UUID(notification_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid notification ID format",
            )
        
        notification = (
            db.query(models.Notification)
            .filter(
                models.Notification.notification_id == notification_uuid,
                models.Notification.user_id == current_user.user_id,
            )
            .first()
        )
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found",
            )
        
        if not notification.read:
            notification.read = True
            notification.read_at = datetime.now()
            db.commit()
        
        return schemas.MarkAsReadResponse(
            success=True,
            message="Notification marked as read",
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark notification as read: {str(e)}",
        )


@router.put("/read-all", response_model=schemas.MarkAsReadResponse)
def mark_all_notifications_as_read(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mark all notifications for the current user as read.
    """
    try:
        updated_count = (
            db.query(models.Notification)
            .filter(
                models.Notification.user_id == current_user.user_id,
                models.Notification.read == False,
            )
            .update(
                {
                    models.Notification.read: True,
                    models.Notification.read_at: datetime.now(),
                },
                synchronize_session=False,
            )
        )
        
        db.commit()
        
        return schemas.MarkAsReadResponse(
            success=True,
            message=f"Marked {updated_count} notification(s) as read",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark all notifications as read: {str(e)}",
        )

