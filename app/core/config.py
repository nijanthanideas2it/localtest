"""
Authentication dependencies for FastAPI.
"""
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.db.database import AsyncSessionWrapper

from app.core.auth import AuthUtils, get_token_from_header, is_token_blacklisted
from app.db.database import get_db
from app.models.user import User


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSessionWrapper = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token.
    
    Args:
        authorization: The Authorization header
        db: Database session
        
    Returns:
        The current user
        
    Raises:
        HTTPException: If authentication fails
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        # Extract token from header
        token = get_token_from_header(authorization)
        
        # Check if token is blacklisted
        if is_token_blacklisted(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )
        
        # Verify and decode token
        payload = AuthUtils.verify_token(token, "access")
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Get user from database
        user = db.session.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current active user.
    
    Args:
        current_user: The current user from get_current_user
        
    Returns:
        The current active user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_user_optional(
    authorization: Optional[str] = Header(None),
    db: AsyncSessionWrapper = Depends(get_db)
) -> Optional[User]:
    """
    Get the current user if authenticated, otherwise return None.
    
    Args:
        authorization: The Authorization header
        db: Database session
        
    Returns:
        The current user if authenticated, None otherwise
    """
    if not authorization:
        return None
    
    try:
        return await get_current_user(authorization, db)
    except HTTPException:
        return None


def require_role(required_role: str):
    """
    Dependency factory to require a specific user role.
    
    Args:
        required_role: The required role
        
    Returns:
        Dependency function that checks user role
    """
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )
        return current_user
    
    return role_checker


def require_roles(required_roles: list[str]):
    """
    Dependency factory to require one of several user roles.
    
    Args:
        required_roles: List of acceptable roles
        
    Returns:
        Dependency function that checks user role
    """
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(required_roles)}"
            )
        return current_user
    
    return role_checker


# Common role dependencies
require_project_manager = require_role("ProjectManager")
require_admin = require_roles(["ProjectManager", "Executive"])
require_team_lead = require_roles(["ProjectManager", "TeamLead"])
require_any_manager = require_roles(["ProjectManager", "TeamLead", "Executive"]) 
