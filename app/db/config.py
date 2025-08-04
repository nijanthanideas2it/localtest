"""
Database configuration settings.
This file contains only database-related settings to avoid circular imports.
"""
import os
from typing import Optional


def get_database_url() -> str:
    """Get database URL from environment variable or use default."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://project_management_eaoe_user:EnNCBCl069GPZUOHFrAZBN9qO2NzNhCv@dpg-d285ofc9c44c73a3ng5g-a.oregon-postgres.render.com/project_management_eaoe"
    )


def get_database_echo() -> bool:
    """Get database echo setting from environment variable."""
    return os.getenv("DATABASE_ECHO", "false").lower() == "true" 
