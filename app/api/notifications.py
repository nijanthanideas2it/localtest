"""
Notification API endpoints for the Project Management Dashboard.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.db.database import AsyncSessionWrapper
from app.models.user import User
from app.services.notification_service import NotificationService
from app.schemas.notification import (
    NotificationCreateRequest,
    NotificationUpdateRequest,
    NotificationListResponse,
    NotificationCreateResponseWrapper,
    NotificationUpdateResponseWrapper,
    NotificationDeleteResponseWrapper,
    NotificationMarkAllReadResponseWrapper,
    NotificationFilterRequest,
    NotificationStatsResponse,
    NotificationResponse
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
async def get_notifications(
    page: Optional[int] = Query(1, ge=1, description="Page number"),
    limit: Optional[int] = Query(20, ge=1, le=100, description="Items per page"),
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    type: Optional[str] = Query(None, description="Filter by notification type"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get notifications for the current user with filtering and pagination.
    
    Args:
        page: Page number
        limit: Items per page
        is_read: Filter by read status
        type: Filter by notification type
        entity_type: Filter by entity type
        entity_id: Filter by entity ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of notifications with pagination
    """
    try:
        # Get notifications
        notifications, pagination_info = NotificationService.get_notifications(
            db.session,
            str(current_user.id),
            page=page,
            limit=limit,
            is_read=is_read,
            type=type,
            entity_type=entity_type,
            entity_id=entity_id
        )
        
        # Convert to response format
        notification_responses = []
        for notification in notifications:
            notification_response = NotificationResponse(
                id=notification.id,
                user_id=notification.user_id,
                type=notification.type,
                title=notification.title,
                message=notification.message,
                entity_type=notification.entity_type,
                entity_id=notification.entity_id,
                is_read=notification.is_read,
                read_at=notification.read_at,
                created_at=notification.created_at
            )
            notification_responses.append(notification_response)
        
        return NotificationListResponse(
            success=True,
            data=notification_responses,
            message="Notifications retrieved successfully",
            pagination=pagination_info
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve notifications: {str(e)}"
        )


@router.post("", response_model=NotificationCreateResponseWrapper, status_code=status.HTTP_201_CREATED)
async def create_notification(
    notification_data: NotificationCreateRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new notification.
    
    Args:
        notification_data: Notification creation data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Created notification details
    """
    try:
        # Create notification
        notification = NotificationService.create_notification(
            db.session,
            str(notification_data.user_id),
            notification_data.type,
            notification_data.title,
            notification_data.message,
            notification_data.entity_type,
            str(notification_data.entity_id) if notification_data.entity_id else None
        )
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create notification"
            )
        
        # Convert to response format
        notification_response = NotificationResponse(
            id=notification.id,
            user_id=notification.user_id,
            type=notification.type,
            title=notification.title,
            message=notification.message,
            entity_type=notification.entity_type,
            entity_id=notification.entity_id,
            is_read=notification.is_read,
            read_at=notification.read_at,
            created_at=notification.created_at
        )
        
        return NotificationCreateResponseWrapper(
            success=True,
            data=notification_response,
            message="Notification created successfully"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create notification: {str(e)}"
        )


@router.put("/{notification_id}/read", response_model=NotificationUpdateResponseWrapper)
async def mark_notification_read(
    notification_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark a notification as read.
    
    Args:
        notification_id: ID of the notification
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated notification details
    """
    try:
        # Mark notification as read
        notification = NotificationService.mark_notification_read(
            db.session,
            notification_id,
            str(current_user.id)
        )
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        # Convert to response format
        notification_response = NotificationResponse(
            id=notification.id,
            user_id=notification.user_id,
            type=notification.type,
            title=notification.title,
            message=notification.message,
            entity_type=notification.entity_type,
            entity_id=notification.entity_id,
            is_read=notification.is_read,
            read_at=notification.read_at,
            created_at=notification.created_at
        )
        
        return NotificationUpdateResponseWrapper(
            success=True,
            data=notification_response,
            message="Notification marked as read successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark notification as read: {str(e)}"
        )


@router.delete("/{notification_id}", response_model=NotificationDeleteResponseWrapper)
async def delete_notification(
    notification_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a notification.
    
    Args:
        notification_id: ID of the notification
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Deletion confirmation
    """
    try:
        # Delete notification
        success = NotificationService.delete_notification(
            db.session,
            notification_id,
            str(current_user.id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        return NotificationDeleteResponseWrapper(
            success=True,
            message="Notification deleted successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete notification: {str(e)}"
        )


@router.post("/mark-all-read", response_model=NotificationMarkAllReadResponseWrapper)
async def mark_all_notifications_read(
    filter_data: Optional[NotificationFilterRequest] = None,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark all notifications as read for the current user.
    
    Args:
        filter_data: Optional filter criteria
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Mark all read confirmation with count
    """
    try:
        # Mark all notifications as read
        updated_count = NotificationService.mark_all_notifications_read(
            db.session,
            str(current_user.id),
            type=filter_data.type if filter_data else None,
            entity_type=filter_data.entity_type if filter_data else None,
            entity_id=str(filter_data.entity_id) if filter_data and filter_data.entity_id else None
        )
        
        return NotificationMarkAllReadResponseWrapper(
            success=True,
            message=f"Marked {updated_count} notifications as read successfully",
            updated_count=updated_count
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark notifications as read: {str(e)}"
        )


@router.get("/stats", response_model=NotificationStatsResponse)
async def get_notification_stats(
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get notification statistics for the current user.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Notification statistics
    """
    try:
        # Get notification statistics
        stats = NotificationService.get_notification_stats(
            db.session,
            str(current_user.id)
        )
        
        return NotificationStatsResponse(
            success=True,
            data=stats,
            message="Notification statistics retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve notification statistics: {str(e)}"
        ) 