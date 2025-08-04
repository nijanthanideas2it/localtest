"""
Authentication configuration settings.
This file contains only auth-related settings to avoid circular imports.
"""
import os
from typing import Optional


def get_secret_key() -> str:
    """Get secret key from environment variable or use default."""
    return os.getenv(
        "SECRET_KEY",
        "your-secret-key-change-in-production"
    )


def get_algorithm() -> str:
    """Get JWT algorithm from environment variable."""
    return os.getenv("ALGORITHM", "HS256")


def get_access_token_expire_minutes() -> int:
    """Get access token expiration time in minutes."""
    return int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


def get_refresh_token_expire_days() -> int:
    """Get refresh token expiration time in days."""
    return int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


def get_password_min_length() -> int:
    """Get minimum password length."""
    return int(os.getenv("PASSWORD_MIN_LENGTH", "8")) 