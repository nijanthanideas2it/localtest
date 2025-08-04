"""
Skills API endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import AsyncSessionWrapper, get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.services.user_service import UserService
from app.schemas.skills import (
    SkillRequest,
    SkillListResponse,
    SkillCreateResponseWrapper,
    SkillUpdateResponseWrapper,
    SkillDeleteResponseWrapper,
    ErrorResponse
)

router = APIRouter(prefix="/users", tags=["Skills Management"])


@router.get("/{user_id}/skills", response_model=SkillListResponse)
async def get_user_skills(
    user_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user skills.
    
    Args:
        user_id: User ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of user skills
        
    Raises:
        HTTPException: If user not found or access denied
    """
    try:
        # Check authorization: user can view own skills, admin/manager can view any
        if str(current_user.id) != user_id and current_user.role not in ["Admin", "Project Manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view skills for this user"
            )
        
        # Check if user exists
        user = UserService.get_user_by_id(db.session, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get user skills
        skills = UserService.get_user_skills(db.session, user_id)
        
        return SkillListResponse(
            success=True,
            data=skills,
            message="Skills retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/{user_id}/skills", response_model=SkillCreateResponseWrapper, status_code=status.HTTP_201_CREATED)
async def add_user_skill(
    user_id: str,
    skill_data: SkillRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add skill to user profile.
    
    Args:
        user_id: User ID
        skill_data: Skill data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Created skill information
        
    Raises:
        HTTPException: If skill addition fails
    """
    try:
        # Check authorization: user can add to own profile, admin/manager can add to any
        if str(current_user.id) != user_id and current_user.role not in ["Admin", "Project Manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to add skills to this user"
            )
        
        user_skill = UserService.add_user_skill(
            db.session, 
            user_id, 
            skill_data.skill_name, 
            skill_data.proficiency_level
        )
        
        if not user_skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return SkillCreateResponseWrapper(
            success=True,
            data=user_skill,
            message="Skill added successfully"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.put("/{user_id}/skills/{skill_id}", response_model=SkillUpdateResponseWrapper)
async def update_user_skill(
    user_id: str,
    skill_id: str,
    skill_data: SkillRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update user skill.
    
    Args:
        user_id: User ID
        skill_id: Skill ID
        skill_data: Skill data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated skill information
        
    Raises:
        HTTPException: If skill update fails
    """
    try:
        # Check authorization: user can update own skills, admin/manager can update any
        if str(current_user.id) != user_id and current_user.role not in ["Admin", "Project Manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update skills for this user"
            )
        
        user_skill = UserService.update_user_skill(
            db.session, 
            user_id, 
            skill_id, 
            skill_data.skill_name, 
            skill_data.proficiency_level
        )
        
        if not user_skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Skill not found"
            )
        
        return SkillUpdateResponseWrapper(
            success=True,
            data=user_skill,
            message="Skill updated successfully"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/{user_id}/skills/{skill_id}", response_model=SkillDeleteResponseWrapper)
async def delete_user_skill(
    user_id: str,
    skill_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete user skill.
    
    Args:
        user_id: User ID
        skill_id: Skill ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Deletion confirmation
        
    Raises:
        HTTPException: If skill deletion fails
    """
    try:
        # Check authorization: user can delete own skills, admin/manager can delete any
        if str(current_user.id) != user_id and current_user.role not in ["Admin", "Project Manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete skills for this user"
            )
        
        success = UserService.delete_user_skill(db.session, user_id, skill_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Skill not found"
            )
        
        return SkillDeleteResponseWrapper(
            success=True,
            message="Skill deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/me/skills", response_model=SkillListResponse)
async def get_current_user_skills(
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's skills.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of current user's skills
    """
    try:
        skills = UserService.get_user_skills(db.session, str(current_user.id))
        
        return SkillListResponse(
            success=True,
            data=skills,
            message="Skills retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        ) 