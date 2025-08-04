"""
Profile API endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.db.database import AsyncSessionWrapper, get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.services.user_service import UserService
from app.services.file_service import FileService
from app.schemas.profile import (
    ProfileUpdateRequest,
    ProfileResponseWrapper,
    ProfileUpdateResponse,
    AvatarUploadResponse,
    ErrorResponse
)

router = APIRouter(prefix="/users", tags=["Profile Management"])


@router.get("/{user_id}/profile", response_model=ProfileResponseWrapper)
async def get_user_profile(
    user_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user profile by ID.
    
    Args:
        user_id: User ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        User profile information
        
    Raises:
        HTTPException: If user not found or access denied
    """
    try:
        # Check authorization: user can view own profile, admin/manager can view any
        if str(current_user.id) != user_id and current_user.role not in ["Admin", "Project Manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this profile"
            )
        
        user = UserService.get_user_with_skills(db.session, user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return ProfileResponseWrapper(
            success=True,
            data=user,
            message="Profile retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.put("/{user_id}/profile", response_model=ProfileUpdateResponse)
async def update_user_profile(
    user_id: str,
    profile_data: ProfileUpdateRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update user profile.
    
    Args:
        user_id: User ID
        profile_data: Profile update data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated profile information
        
    Raises:
        HTTPException: If update fails or access denied
    """
    try:
        # Check authorization: user can update own profile, admin can update any
        if str(current_user.id) != user_id and current_user.role != "Admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this profile"
            )
        
        updated_user = UserService.update_user_profile(db.session, user_id, profile_data)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return ProfileUpdateResponse(
            success=True,
            data=updated_user,
            message="Profile updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/{user_id}/avatar", response_model=AvatarUploadResponse)
async def upload_user_avatar(
    user_id: str,
    file: UploadFile = File(...),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload user avatar.
    
    Args:
        user_id: User ID
        file: Avatar image file
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Avatar upload confirmation
        
    Raises:
        HTTPException: If upload fails or access denied
    """
    try:
        # Check authorization: user can upload own avatar, admin can upload for any
        if str(current_user.id) != user_id and current_user.role != "Admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to upload avatar for this user"
            )
        
        # Save avatar file
        avatar_path = await FileService.save_avatar(file, user_id)
        
        # Update user avatar URL
        updated_user = UserService.update_user_avatar(db.session, user_id, avatar_path)
        
        if not updated_user:
            # Clean up uploaded file if user not found
            FileService.delete_avatar(avatar_path)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return AvatarUploadResponse(
            success=True,
            data={
                "avatar_url": avatar_path,
                "file_name": file.filename,
                "file_size": file.size,
                "content_type": file.content_type
            },
            message="Avatar uploaded successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/{user_id}/avatar")
async def delete_user_avatar(
    user_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete user avatar.
    
    Args:
        user_id: User ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Deletion confirmation
        
    Raises:
        HTTPException: If deletion fails or access denied
    """
    try:
        # Check authorization: user can delete own avatar, admin can delete any
        if str(current_user.id) != user_id and current_user.role != "Admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete avatar for this user"
            )
        
        user = UserService.get_user_by_id(db.session, user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not user.avatar_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User has no avatar to delete"
            )
        
        # Delete avatar file
        FileService.delete_avatar(user.avatar_url)
        
        # Update user to remove avatar URL
        user.avatar_url = None
        user.updated_at = datetime.now(timezone.utc)
        await db.commit()
        
        return {
            "success": True,
            "message": "Avatar deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/me/profile", response_model=ProfileResponseWrapper)
async def get_current_user_profile(
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's profile.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Current user's profile information
    """
    try:
        user = UserService.get_user_with_skills(db.session, str(current_user.id))
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return ProfileResponseWrapper(
            success=True,
            data=user,
            message="Profile retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.put("/me/profile", response_model=ProfileUpdateResponse)
async def update_current_user_profile(
    profile_data: ProfileUpdateRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update current user's profile.
    
    Args:
        profile_data: Profile update data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated profile information
    """
    try:
        updated_user = UserService.update_user_profile(
            db.session, 
            str(current_user.id), 
            profile_data
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return ProfileUpdateResponse(
            success=True,
            data=updated_user,
            message="Profile updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        ) 