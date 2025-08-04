"""
Authentication utilities for JWT token handling and password security.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from app.core.auth_config import (
    get_secret_key,
    get_algorithm,
    get_access_token_expire_minutes,
    get_refresh_token_expire_days,
    get_password_min_length
)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthUtils:
    """Authentication utilities for JWT and password handling."""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain password against its hash.
        
        Args:
            plain_password: The plain text password
            hashed_password: The hashed password to verify against
            
        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: The plain text password to hash
            
        Returns:
            The hashed password
        """
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(
        data: dict, 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token.
        
        Args:
            data: The data to encode in the token
            expires_delta: Optional custom expiration time
            
        Returns:
            The encoded JWT token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=get_access_token_expire_minutes()
            )
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(
            to_encode, 
            get_secret_key(), 
            algorithm=get_algorithm()
        )
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(
        data: dict, 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT refresh token.
        
        Args:
            data: The data to encode in the token
            expires_delta: Optional custom expiration time
            
        Returns:
            The encoded JWT refresh token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                days=get_refresh_token_expire_days()
            )
        
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(
            to_encode, 
            get_secret_key(), 
            algorithm=get_algorithm()
        )
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> dict:
        """
        Verify and decode a JWT token.
        
        Args:
            token: The JWT token to verify
            token_type: The expected token type ("access" or "refresh")
            
        Returns:
            The decoded token payload
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token, 
                get_secret_key(), 
                algorithms=[get_algorithm()]
            )
            
            # Check token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            # Check if token is expired
            exp = payload.get("exp")
            if exp is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has no expiration"
                )
            
            if datetime.now(timezone.utc) > datetime.fromtimestamp(exp, tz=timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired"
                )
            
            return payload
            
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    @staticmethod
    def validate_password_strength(password: str) -> bool:
        """
        Validate password strength according to security requirements.
        
        Args:
            password: The password to validate
            
        Returns:
            True if password meets requirements, False otherwise
        """
        if len(password) < get_password_min_length():
            return False
        
        # Check for at least one uppercase letter
        if not any(c.isupper() for c in password):
            return False
        
        # Check for at least one lowercase letter
        if not any(c.islower() for c in password):
            return False
        
        # Check for at least one digit
        if not any(c.isdigit() for c in password):
            return False
        
        # Check for at least one special character
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            return False
        
        return True


# Global blacklist for revoked tokens (in production, use Redis)
token_blacklist = set()


def add_to_blacklist(token: str) -> None:
    """
    Add a token to the blacklist.
    
    Args:
        token: The token to blacklist
    """
    token_blacklist.add(token)


def is_token_blacklisted(token: str) -> bool:
    """
    Check if a token is blacklisted.
    
    Args:
        token: The token to check
        
    Returns:
        True if token is blacklisted, False otherwise
    """
    return token in token_blacklist


def get_token_from_header(authorization: str) -> str:
    """
    Extract token from Authorization header.
    
    Args:
        authorization: The Authorization header value
        
    Returns:
        The extracted token
        
    Raises:
        HTTPException: If Authorization header is invalid
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format"
        )
    
    return parts[1] 
