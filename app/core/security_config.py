"""
Security configuration settings.
This file contains only security-related settings to avoid circular imports.
"""
import os
from typing import List


def get_rate_limit_enabled() -> bool:
    """Get rate limiting enabled setting."""
    return os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"


def get_rate_limit_requests_per_minute() -> int:
    """Get rate limit requests per minute."""
    return int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "60"))


def get_rate_limit_requests_per_hour() -> int:
    """Get rate limit requests per hour."""
    return int(os.getenv("RATE_LIMIT_REQUESTS_PER_HOUR", "1000"))


def get_rate_limit_burst_size() -> int:
    """Get rate limit burst size."""
    return int(os.getenv("RATE_LIMIT_BURST_SIZE", "10"))


def get_security_headers_enabled() -> bool:
    """Get security headers enabled setting."""
    return os.getenv("SECURITY_HEADERS_ENABLED", "true").lower() == "true"


def get_content_security_policy() -> str:
    """Get content security policy."""
    return os.getenv(
        "CONTENT_SECURITY_POLICY",
        "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; font-src 'self' https://cdn.jsdelivr.net; img-src 'self' data: https:;"
    )


def get_strict_transport_security() -> str:
    """Get strict transport security header."""
    return os.getenv("STRICT_TRANSPORT_SECURITY", "max-age=31536000; includeSubDomains")


def get_x_frame_options() -> str:
    """Get X-Frame-Options header."""
    return os.getenv("X_FRAME_OPTIONS", "DENY")


def get_x_content_type_options() -> str:
    """Get X-Content-Type-Options header."""
    return os.getenv("X_CONTENT_TYPE_OPTIONS", "nosniff")


def get_x_xss_protection() -> str:
    """Get X-XSS-Protection header."""
    return os.getenv("X_XSS_PROTECTION", "1; mode=block")


def get_referrer_policy() -> str:
    """Get Referrer-Policy header."""
    return os.getenv("REFERRER_POLICY", "strict-origin-when-cross-origin")


def get_input_sanitization_enabled() -> bool:
    """Get input sanitization enabled setting."""
    return os.getenv("INPUT_SANITIZATION_ENABLED", "true").lower() == "true"


def get_max_request_size() -> int:
    """Get maximum request size in bytes."""
    return int(os.getenv("MAX_REQUEST_SIZE", str(10 * 1024 * 1024)))  # 10MB


def get_max_header_size() -> int:
    """Get maximum header size in bytes."""
    return int(os.getenv("MAX_HEADER_SIZE", "8192"))


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
