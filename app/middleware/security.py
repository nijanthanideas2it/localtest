"""
Security middleware for rate limiting, security headers, and input sanitization.
"""
import time
import logging
import re
from typing import Dict, Any, Optional, Callable
from collections import defaultdict
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import RequestResponseEndpoint
from starlette.types import ASGIApp

from app.core.config import settings
from app.core.security import SecurityUtils

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.rate_limit_store: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.cleanup_interval = 60  # Clean up every 60 seconds
        self.last_cleanup = time.time()
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process request with rate limiting."""
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        # Get client identifier
        client_id = self._get_client_identifier(request)
        
        # Check rate limits
        if not self._check_rate_limit(client_id, request.url.path):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": self._get_retry_after(client_id)
                },
                headers={"Retry-After": str(self._get_retry_after(client_id))}
            )
        
        # Clean up old entries periodically
        self._cleanup_old_entries()
        
        return await call_next(request)
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get client identifier for rate limiting."""
        # Try to get real IP from headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _check_rate_limit(self, client_id: str, path: str) -> bool:
        """Check if request is within rate limits."""
        now = time.time()
        key = f"{client_id}:{path}"
        
        # Get current limits
        minute_limit = settings.RATE_LIMIT_REQUESTS_PER_MINUTE
        hour_limit = settings.RATE_LIMIT_REQUESTS_PER_HOUR
        burst_limit = settings.RATE_LIMIT_BURST_SIZE
        
        # Initialize client data if not exists
        if key not in self.rate_limit_store:
            self.rate_limit_store[key] = {
                "requests": [],
                "last_request": now
            }
        
        client_data = self.rate_limit_store[key]
        
        # Remove old requests (older than 1 hour)
        client_data["requests"] = [
            req_time for req_time in client_data["requests"]
            if now - req_time < 3600
        ]
        
        # Check burst limit
        recent_requests = [
            req_time for req_time in client_data["requests"]
            if now - req_time < 1  # Last second
        ]
        
        if len(recent_requests) >= burst_limit:
            return False
        
        # Check minute limit
        minute_requests = [
            req_time for req_time in client_data["requests"]
            if now - req_time < 60  # Last minute
        ]
        
        if len(minute_requests) >= minute_limit:
            return False
        
        # Check hour limit
        if len(client_data["requests"]) >= hour_limit:
            return False
        
        # Add current request
        client_data["requests"].append(now)
        client_data["last_request"] = now
        
        return True
    
    def _get_retry_after(self, client_id: str) -> int:
        """Get retry after time in seconds."""
        return 60  # Default to 1 minute
    
    def _cleanup_old_entries(self):
        """Clean up old rate limit entries."""
        now = time.time()
        if now - self.last_cleanup < self.cleanup_interval:
            return
        
        # Remove entries older than 1 hour
        keys_to_remove = []
        for key, client_data in self.rate_limit_store.items():
            if now - client_data["last_request"] > 3600:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.rate_limit_store[key]
        
        self.last_cleanup = now


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Security headers middleware."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process request with security headers."""
        response = await call_next(request)
        
        if not settings.SECURITY_HEADERS_ENABLED:
            return response
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = settings.X_CONTENT_TYPE_OPTIONS
        response.headers["X-Frame-Options"] = settings.X_FRAME_OPTIONS
        response.headers["X-XSS-Protection"] = settings.X_XSS_PROTECTION
        response.headers["Referrer-Policy"] = settings.REFERRER_POLICY
        
        # Add HSTS header (only for HTTPS)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = settings.STRICT_TRANSPORT_SECURITY
        
        # Add Content Security Policy
        response.headers["Content-Security-Policy"] = settings.CONTENT_SECURITY_POLICY
        
        # Add additional security headers
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        
        return response


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """Input sanitization middleware."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process request with input sanitization."""
        if not settings.INPUT_SANITIZATION_ENABLED:
            return await call_next(request)
        
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > settings.MAX_REQUEST_SIZE:
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={"detail": "Request too large"}
                    )
            except ValueError:
                pass
        
        # Check header size
        total_header_size = sum(
            len(name) + len(value) for name, value in request.headers.items()
        )
        if total_header_size > settings.MAX_HEADER_SIZE:
            return JSONResponse(
                status_code=status.HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE,
                content={"detail": "Request headers too large"}
            )
        
        # Sanitize query parameters
        sanitized_query_params = {}
        for key, value in request.query_params.items():
            sanitized_key = SecurityUtils.sanitize_input(key)
            sanitized_value = SecurityUtils.sanitize_input(value)
            sanitized_query_params[sanitized_key] = sanitized_value
        
        # Create new request with sanitized query params
        request.scope["query_string"] = b"&".join(
            f"{k}={v}".encode() for k, v in sanitized_query_params.items()
        )
        
        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Request logging middleware for security monitoring."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process request with logging."""
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {self._get_client_ip(request)} "
            f"User-Agent: {request.headers.get('user-agent', 'Unknown')}"
        )
        
        try:
            response = await call_next(request)
            
            # Log response
            process_time = time.time() - start_time
            logger.info(
                f"Response: {response.status_code} "
                f"for {request.method} {request.url.path} "
                f"took {process_time:.3f}s"
            )
            
            return response
            
        except Exception as e:
            # Log errors
            logger.error(
                f"Error processing {request.method} {request.url.path}: {str(e)}"
            )
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        if request.client:
            return request.client.host
        
        return "unknown"


class SecurityMiddleware:
    """Combined security middleware."""
    
    def __init__(self, app: ASGIApp):
        self.app = app
        self.rate_limit_middleware = RateLimitMiddleware(app)
        self.security_headers_middleware = SecurityHeadersMiddleware(app)
        self.input_sanitization_middleware = InputSanitizationMiddleware(app)
        self.request_logging_middleware = RequestLoggingMiddleware(app)
    
    async def __call__(self, scope, receive, send):
        """Apply all security middleware."""
        # Create a chain of middleware
        app = self.request_logging_middleware
        app = InputSanitizationMiddleware(app)
        app = SecurityHeadersMiddleware(app)
        app = RateLimitMiddleware(app)
        
        return await app(scope, receive, send)


def create_security_middleware(app: ASGIApp) -> ASGIApp:
    """Create and configure security middleware."""
    # Add rate limiting
    if settings.RATE_LIMIT_ENABLED:
        app.add_middleware(RateLimitMiddleware)
    
    # Add security headers
    if settings.SECURITY_HEADERS_ENABLED:
        app.add_middleware(SecurityHeadersMiddleware)
    
    # Add input sanitization
    if settings.INPUT_SANITIZATION_ENABLED:
        app.add_middleware(InputSanitizationMiddleware)
    
    # Add request logging
    app.add_middleware(RequestLoggingMiddleware)
    
    return app


class SecurityUtils:
    """Security utilities for middleware."""
    
    @staticmethod
    def is_suspicious_request(request: Request) -> bool:
        """Check if request is suspicious."""
        # Check for common attack patterns
        suspicious_patterns = [
            r"<script",
            r"javascript:",
            r"on\w+\s*=",
            r"union\s+select",
            r"drop\s+table",
            r"exec\s*\(",
            r"eval\s*\(",
            r"document\.cookie",
            r"window\.location",
        ]
        
        # Check URL
        url_str = str(request.url)
        for pattern in suspicious_patterns:
            if re.search(pattern, url_str, re.IGNORECASE):
                return True
        
        # Check headers
        for header_name, header_value in request.headers.items():
            if any(re.search(pattern, header_value, re.IGNORECASE) for pattern in suspicious_patterns):
                return True
        
        # Check query parameters
        for param_name, param_value in request.query_params.items():
            if any(re.search(pattern, param_value, re.IGNORECASE) for pattern in suspicious_patterns):
                return True
        
        return False
    
    @staticmethod
    def get_request_fingerprint(request: Request) -> str:
        """Get unique fingerprint for request."""
        components = [
            request.method,
            request.url.path,
            request.headers.get("user-agent", ""),
            request.headers.get("accept", ""),
            request.headers.get("accept-language", ""),
        ]
        return SecurityUtils.hash_data(":".join(components))[0]
    
    @staticmethod
    def hash_data(data: str) -> tuple[str, str]:
        """Hash data for fingerprinting."""
        from app.core.security import SecurityUtils as CoreSecurityUtils
        return CoreSecurityUtils.hash_data(data) 