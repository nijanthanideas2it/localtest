"""
WebSocket authentication utilities.
"""
from typing import Optional
from fastapi import WebSocket, HTTPException, status
from jose import jwt
from datetime import datetime, timezone

from app.core.auth import AuthUtils
from app.models.user import User


async def get_current_user_websocket(token: str) -> Optional[User]:
    """
    Get current user from WebSocket token.
    
    Args:
        token: JWT token from WebSocket connection
        
    Returns:
        User object if token is valid, None otherwise
    """
    try:
        # Decode the JWT token
        payload = AuthUtils.verify_token(token, "access")
        user_id: str = payload.get("sub")
        
        if user_id is None:
            return None
        
        # Fetch the user from the database
        from app.db.database import get_db
        from app.core.auth import is_token_blacklisted
        
        # Check if token is blacklisted
        if is_token_blacklisted(token):
            return None
        
        # Get database session
        db = get_db()
        
        # Query user from database
        user = db.session.query(User).filter(User.id == user_id).first()
        
        if user is None or not user.is_active:
            return None
        
        return user
        
    except Exception:
        return None
    except Exception:
        return None


async def validate_websocket_connection(websocket: WebSocket) -> Optional[str]:
    """
    Validate WebSocket connection and return user ID.
    
    Args:
        websocket: WebSocket connection
        
    Returns:
        User ID if connection is valid, None otherwise
    """
    try:
        # Get token from query parameters
        token = websocket.query_params.get("token")
        
        if not token:
            return None
        
        # Validate token and get user
        user = await get_current_user_websocket(token)
        
        if user is None:
            return None
        
        return str(user.id)
        
    except Exception:
        return None


async def authenticate_websocket(websocket: WebSocket) -> str:
    """
    Authenticate WebSocket connection and return user ID.
    
    Args:
        websocket: WebSocket connection
        
    Returns:
        User ID if authentication successful
        
    Raises:
        HTTPException: If authentication fails
    """
    user_id = await validate_websocket_connection(websocket)
    
    if user_id is None:
        await websocket.send_text('{"type": "error", "error": "Authentication failed"}')
        await websocket.close()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="WebSocket authentication failed"
        )
    
    return user_id 
