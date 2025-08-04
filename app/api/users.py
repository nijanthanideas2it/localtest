"""
User API endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.database import AsyncSessionWrapper, get_db
from app.core.dependencies import get_current_user, require_admin, require_roles
from app.models.user import User
from app.services.user_service import UserService
from app.schemas.user import (
    UserCreateRequest,
    UserUpdateRequest,
    UserSkillRequest,
    UserQueryParams,
    UserListResponse,
    UserListResponseWrapper,
    UserResponseWrapper,
    UserCreateResponseWrapper,
    UserUpdateResponseWrapper,
    UserDeleteResponseWrapper,
    UserSkillResponseWrapper,
    ErrorResponse,
    PaginationInfo
)
from app.schemas.comment import UserMentionsResponse, CommentMentionResponse
from app.services.comment_service import CommentService
from app.schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/assignable", response_model=UserListResponseWrapper)
async def get_assignable_users(
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of users that can be assigned to tasks.
    This endpoint is accessible to all authenticated users.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of assignable users
        
    Raises:
        HTTPException: If access denied or other errors
    """
    try:
        # Get users with developer roles that can be assigned to tasks
        users = UserService.get_assignable_users(db.session)
        
        # Convert to response models
        user_list = [UserListResponse.from_orm(user) for user in users]
        
        # Create pagination info for all results (no pagination for assignable users)
        pagination_info = PaginationInfo(
            page=1,
            limit=len(user_list),
            total=len(user_list),
            pages=1
        )
        
        return UserListResponseWrapper(
            success=True,
            data=user_list,
            pagination=pagination_info,
            message="Assignable users retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("", response_model=UserListResponseWrapper)
async def get_users(
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "Project Manager"]))
):
    """
    Get paginated list of users with filtering.
    
    Args:
        page: Page number
        limit: Items per page
        role: Filter by role
        is_active: Filter by active status
        search: Search by name or email
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Paginated list of users
        
    Raises:
        HTTPException: If access denied or other errors
    """
    try:
        # Build query parameters
        query_params = UserQueryParams(
            page=page,
            limit=limit,
            role=role,
            is_active=is_active,
            search=search
        )
        
        # Get users with pagination
        users, total_count = UserService.get_users_with_pagination(
            db.session, query_params
        )
        
        # Calculate pagination info
        pagination_info = UserService.calculate_pagination_info(
            total_count, page, limit
        )
        
        # Convert to response models
        user_list = [UserListResponse.from_orm(user) for user in users]
        
        return UserListResponseWrapper(
            success=True,
            data=user_list,
            pagination=pagination_info,
            message="Users retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserResponseWrapper)
async def get_user(
    user_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin", "Project Manager"]))
):
    """
    Get specific user by ID.
    
    Args:
        user_id: User ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        User information
        
    Raises:
        HTTPException: If user not found or access denied
    """
    try:
        user = UserService.get_user_with_skills(db.session, user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponseWrapper(
            success=True,
            data=UserResponse.from_orm(user),
            message="User retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("", response_model=UserCreateResponseWrapper, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreateRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Create a new user (admin only).
    
    Args:
        user_data: User creation data
        db: Database session
        current_user: Current authenticated user (admin)
        
    Returns:
        Created user information
        
    Raises:
        HTTPException: If creation fails or access denied
    """
    try:
        new_user = UserService.create_user(db.session, user_data)
        
        return UserCreateResponseWrapper(
            success=True,
            data=UserResponse.from_orm(new_user),
            message="User created successfully"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.put("/{user_id}", response_model=UserUpdateResponseWrapper)
async def update_user(
    user_id: str,
    update_data: UserUpdateRequest,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Update user information (admin only).
    
    Args:
        user_id: User ID
        update_data: Update data
        db: Database session
        current_user: Current authenticated user (admin)
        
    Returns:
        Updated user information
        
    Raises:
        HTTPException: If update fails or access denied
    """
    try:
        updated_user = UserService.update_user(db.session, user_id, update_data)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserUpdateResponseWrapper(
            success=True,
            data=UserResponse.from_orm(updated_user),
            message="User updated successfully"
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


@router.delete("/{user_id}", response_model=UserDeleteResponseWrapper)
async def delete_user(
    user_id: str,
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Delete user (admin only).
    
    Args:
        user_id: User ID
        db: Database session
        current_user: Current authenticated user (admin)
        
    Returns:
        Deletion confirmation
        
    Raises:
        HTTPException: If deletion fails or access denied
    """
    try:
        success = UserService.delete_user(db.session, user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserDeleteResponseWrapper(
            success=True,
            message="User deleted successfully"
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


@router.post("/{user_id}/skills", response_model=UserSkillResponseWrapper, status_code=status.HTTP_201_CREATED)
async def add_user_skill(
    user_id: str,
    skill_data: UserSkillRequest,
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
        
        return UserSkillResponseWrapper(
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


@router.put("/{user_id}/skills/{skill_id}", response_model=UserSkillResponseWrapper)
async def update_user_skill(
    user_id: str,
    skill_id: str,
    skill_data: UserSkillRequest,
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
        
        return UserSkillResponseWrapper(
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


@router.delete("/{user_id}/skills/{skill_id}", response_model=UserDeleteResponseWrapper)
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
        
        return UserDeleteResponseWrapper(
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


@router.get("/{user_id}/mentions", response_model=UserMentionsResponse)
async def get_user_mentions(
    user_id: str,
    page: Optional[int] = Query(1, ge=1, description="Page number"),
    limit: Optional[int] = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSessionWrapper = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all mentions for a specific user.
    
    Args:
        user_id: User ID
        page: Page number
        limit: Items per page
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of mentions with pagination
    """
    try:
        # Check authorization: user can view own mentions, admin/manager can view any
        if str(current_user.id) != user_id and current_user.role not in ["Admin", "Project Manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view mentions for this user"
            )
        
        # Get mentions
        mentions, pagination_info = CommentService.get_user_mentions(
            db.session,
            user_id,
            page=page,
            limit=limit
        )
        
        # Convert to response format
        mention_responses = []
        for mention in mentions:
            mention_response = CommentMentionResponse(
                id=mention.id,
                comment_id=mention.comment_id,
                mentioned_user_id=mention.mentioned_user_id,
                created_at=mention.created_at,
                mentioned_user=UserResponse(
                    id=mention.mentioned_user.id,
                    email=mention.mentioned_user.email,
                    first_name=mention.mentioned_user.first_name,
                    last_name=mention.mentioned_user.last_name,
                    role=mention.mentioned_user.role,
                    is_active=mention.mentioned_user.is_active,
                    created_at=mention.mentioned_user.created_at,
                    updated_at=mention.mentioned_user.updated_at
                )
            )
            mention_responses.append(mention_response)
        
        return UserMentionsResponse(
            success=True,
            data=mention_responses,
            message="User mentions retrieved successfully",
            pagination=pagination_info
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user mentions: {str(e)}"
        ) 