"""
Application configuration settings.
This file contains only app-related settings to avoid circular imports.
"""
import os
from typing import List


def get_app_name() -> str:
    """Get application name."""
    return os.getenv("APP_NAME", "Project Management Dashboard API")


def get_app_version() -> str:
    """Get application version."""
    return os.getenv("VERSION", "1.0.0")


def get_debug() -> bool:
    """Get debug mode setting."""
    return os.getenv("DEBUG", "false").lower() == "true"


def get_host() -> str:
    """Get host address."""
    return os.getenv("HOST", "0.0.0.0")


def get_port() -> int:
    """Get port number."""
    return int(os.getenv("PORT", "8000"))


def get_allowed_hosts() -> List[str]:
    """Get allowed hosts for CORS."""
    hosts_str = os.getenv(
        "ALLOWED_HOSTS",
        '["http://localhost:3000","http://localhost:3001","http://localhost:3002","http://localhost:3003","http://localhost:3004","http://localhost:8080"]'
    )
    # Simple parsing - in production, use proper JSON parsing
    if hosts_str.startswith('[') and hosts_str.endswith(']'):
        # Remove brackets and split by comma
        content = hosts_str[1:-1]
        return [host.strip().strip('"') for host in content.split(',') if host.strip()]
    return ["http://localhost:3000"] 
