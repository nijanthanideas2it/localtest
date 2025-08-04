"""
Notification Preferences API endpoints for the Project Management Dashboard.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.db.database import AsyncSessionWrapper
from app.models.user import User
from app.services.notification_preference_service import NotificationPreferenceService
from app.schemas.notification_preference import (
    NotificationPreferenceCreateRequest,
    NotificationPreferenceUpdateRequest,
    NotificationPreferenceListResponse,
    NotificationPreferenceCreateResponseWrapper,
    NotificationPreferenceUpdateResponseWrapper,
    NotificationPreferenceDeleteResponseWrapper,
    NotificationPreferenceBulkUpdateRequest,
    NotificationPreferenceBulkUpdateResponseWrapper,
    NotificationPreferenceStatsResponse,
    NotificationPreferenceResponse
)

router = APIRouter(prefix="/users/{user_id}/notification-preferences", tags=["notification-preferences"])


@router.get("", response_model=NotificationPreferenceListResponse)
async def get_notification_preferences(
    user_id: str = Path(..., description="ID of the user"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get notification preferences for a user.
    
    Args:
        user_id: ID of the user
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of notification preferences
    """
    try:
        # Check authorization - users can only view their own preferences
        if str(current_user.id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own notification preferences"
            )
        
        # Get notification preferences
        preferences = NotificationPreferenceService.get_notification_preferences(
            db.session,
            user_id
        )
        
        # Convert to response format
        preference_responses = []
        for preference in preferences:
            preference_response = NotificationPreferenceResponse(
                id=preference.id,
                user_id=preference.user_id,
                notification_type=preference.notification_type,
                email_enabled=preference.email_enabled,
                push_enabled=preference.push_enabled,
                in_app_enabled=preference.in_app_enabled,
                created_at=preference.created_at,
                updated_at=preference.updated_at
            )
            preference_responses.append(preference_response)
        
        return NotificationPreferenceListResponse(
            success=True,
            data=preference_responses,
            message="Notification preferences retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve notification preferences: {str(e)}"
        )


@router.post("", response_model=NotificationPreferenceCreateResponseWrapper, status_code=status.HTTP_201_CREATED)
async def create_notification_preference(
    preference_data: NotificationPreferenceCreateRequest,
    user_id: str = Path(..., description="ID of the user"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new notification preference.
    
    Args:
        preference_data: Notification preference creation data
        user_id: ID of the user
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Created notification preference details
    """
    try:
        # Check authorization - users can only create their own preferences
        if str(current_user.id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create your own notification preferences"
            )
        
        # Create notification preference
        preference = NotificationPreferenceService.create_notification_preference(
            db.session,
            user_id,
            preference_data.notification_type,
            preference_data.email_enabled,
            preference_data.push_enabled,
            preference_data.in_app_enabled
        )
        
        if not preference:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create notification preference"
            )
        
        # Convert to response format
        preference_response = NotificationPreferenceResponse(
            id=preference.id,
            user_id=preference.user_id,
            notification_type=preference.notification_type,
            email_enabled=preference.email_enabled,
            push_enabled=preference.push_enabled,
            in_app_enabled=preference.in_app_enabled,
            created_at=preference.created_at,
            updated_at=preference.updated_at
        )
        
        return NotificationPreferenceCreateResponseWrapper(
            success=True,
            data=preference_response,
            message="Notification preference created successfully"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create notification preference: {str(e)}"
        )


@router.put("/{notification_type}", response_model=NotificationPreferenceUpdateResponseWrapper)
async def update_notification_preference(
    preference_data: NotificationPreferenceUpdateRequest,
    user_id: str = Path(..., description="ID of the user"),
    notification_type: str = Path(..., description="Type of notification"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a notification preference.
    
    Args:
        preference_data: Notification preference update data
        user_id: ID of the user
        notification_type: Type of notification
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated notification preference details
    """
    try:
        # Check authorization - users can only update their own preferences
        if str(current_user.id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own notification preferences"
            )
        
        # Update notification preference
        preference = NotificationPreferenceService.update_notification_preference(
            db.session,
            user_id,
            notification_type,
            preference_data.email_enabled,
            preference_data.push_enabled,
            preference_data.in_app_enabled
        )
        
        if not preference:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification preference not found"
            )
        
        # Convert to response format
        preference_response = NotificationPreferenceResponse(
            id=preference.id,
            user_id=preference.user_id,
            notification_type=preference.notification_type,
            email_enabled=preference.email_enabled,
            push_enabled=preference.push_enabled,
            in_app_enabled=preference.in_app_enabled,
            created_at=preference.created_at,
            updated_at=preference.updated_at
        )
        
        return NotificationPreferenceUpdateResponseWrapper(
            success=True,
            data=preference_response,
            message="Notification preference updated successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update notification preference: {str(e)}"
        )


@router.delete("/{notification_type}", response_model=NotificationPreferenceDeleteResponseWrapper)
async def delete_notification_preference(
    user_id: str = Path(..., description="ID of the user"),
    notification_type: str = Path(..., description="Type of notification"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a notification preference.
    
    Args:
        user_id: ID of the user
        notification_type: Type of notification
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Deletion confirmation
    """
    try:
        # Check authorization - users can only delete their own preferences
        if str(current_user.id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own notification preferences"
            )
        
        # Delete notification preference
        success = NotificationPreferenceService.delete_notification_preference(
            db.session,
            user_id,
            notification_type
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification preference not found"
            )
        
        return NotificationPreferenceDeleteResponseWrapper(
            success=True,
            message="Notification preference deleted successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete notification preference: {str(e)}"
        )


@router.post("/bulk-update", response_model=NotificationPreferenceBulkUpdateResponseWrapper)
async def bulk_update_notification_preferences(
    bulk_data: NotificationPreferenceBulkUpdateRequest,
    user_id: str = Path(..., description="ID of the user"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bulk update notification preferences.
    
    Args:
        bulk_data: Bulk update data
        user_id: ID of the user
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Bulk update confirmation with updated preferences
    """
    try:
        # Check authorization - users can only update their own preferences
        if str(current_user.id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own notification preferences"
            )
        
        # Convert to list of dictionaries
        preferences_data = []
        for pref in bulk_data.preferences:
            preferences_data.append({
                'notification_type': pref.notification_type,
                'email_enabled': pref.email_enabled,
                'push_enabled': pref.push_enabled,
                'in_app_enabled': pref.in_app_enabled
            })
        
        # Bulk update notification preferences
        updated_preferences = NotificationPreferenceService.bulk_update_notification_preferences(
            db.session,
            user_id,
            preferences_data
        )
        
        # Convert to response format
        preference_responses = []
        for preference in updated_preferences:
            preference_response = NotificationPreferenceResponse(
                id=preference.id,
                user_id=preference.user_id,
                notification_type=preference.notification_type,
                email_enabled=preference.email_enabled,
                push_enabled=preference.push_enabled,
                in_app_enabled=preference.in_app_enabled,
                created_at=preference.created_at,
                updated_at=preference.updated_at
            )
            preference_responses.append(preference_response)
        
        return NotificationPreferenceBulkUpdateResponseWrapper(
            success=True,
            data=preference_responses,
            message=f"Successfully updated {len(updated_preferences)} notification preferences",
            updated_count=len(updated_preferences)
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk update notification preferences: {str(e)}"
        )


@router.post("/create-defaults", response_model=NotificationPreferenceListResponse)
async def create_default_notification_preferences(
    user_id: str = Path(..., description="ID of the user"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create default notification preferences for a user.
    
    Args:
        user_id: ID of the user
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of created notification preferences
    """
    try:
        # Check authorization - users can only create their own preferences
        if str(current_user.id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create your own notification preferences"
            )
        
        # Create default notification preferences
        created_preferences = NotificationPreferenceService.create_default_preferences(
            db.session,
            user_id
        )
        
        # Convert to response format
        preference_responses = []
        for preference in created_preferences:
            preference_response = NotificationPreferenceResponse(
                id=preference.id,
                user_id=preference.user_id,
                notification_type=preference.notification_type,
                email_enabled=preference.email_enabled,
                push_enabled=preference.push_enabled,
                in_app_enabled=preference.in_app_enabled,
                created_at=preference.created_at,
                updated_at=preference.updated_at
            )
            preference_responses.append(preference_response)
        
        return NotificationPreferenceListResponse(
            success=True,
            data=preference_responses,
            message=f"Successfully created {len(created_preferences)} default notification preferences"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create default notification preferences: {str(e)}"
        )


@router.get("/stats", response_model=NotificationPreferenceStatsResponse)
async def get_notification_preference_stats(
    user_id: str = Path(..., description="ID of the user"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get notification preference statistics for a user.
    
    Args:
        user_id: ID of the user
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Notification preference statistics
    """
    try:
        # Check authorization - users can only view their own stats
        if str(current_user.id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own notification preference statistics"
            )
        
        # Get notification preference statistics
        stats = NotificationPreferenceService.get_notification_preference_stats(
            db.session,
            user_id
        )
        
        return NotificationPreferenceStatsResponse(
            success=True,
            data=stats,
            message="Notification preference statistics retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve notification preference statistics: {str(e)}"
        ) 