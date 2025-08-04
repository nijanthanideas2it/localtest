"""
Authentication schemas for request and response models.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator, Field

from app.core.config import settings


class UserLoginRequest(BaseModel):
    """User login request model."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")


class UserRegisterRequest(BaseModel):
    """User registration request model."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=settings.PASSWORD_MIN_LENGTH, description="User password")
    first_name: str = Field(..., min_length=1, max_length=50, description="User first name")
    last_name: str = Field(..., min_length=1, max_length=50, description="User last name")
    role: str = Field(default="Developer", description="User role")
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        """Validate user role."""
        allowed_roles = ["Admin", "Project Manager", "Team Lead", "Developer"]
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of: {', '.join(allowed_roles)}")
        return v


class TokenRefreshRequest(BaseModel):
    """Token refresh request model."""
    refresh_token: str = Field(..., description="Refresh token")


class ForgotPasswordRequest(BaseModel):
    """Forgot password request model."""
    email: EmailStr = Field(..., description="User email address")


class ResetPasswordRequest(BaseModel):
    """Reset password request model."""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=settings.PASSWORD_MIN_LENGTH, description="New password")


class ChangePasswordRequest(BaseModel):
    """Change password request model."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=settings.PASSWORD_MIN_LENGTH, description="New password")


class EmailVerificationRequest(BaseModel):
    """Email verification request model."""
    token: str = Field(..., description="Email verification token")


class ResendVerificationRequest(BaseModel):
    """Resend email verification request model."""
    email: EmailStr = Field(..., description="User email address")


class SessionInfo(BaseModel):
    """Session information model."""
    session_id: str
    created_at: datetime
    last_activity: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_current: bool = False


class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    first_name: str
    last_name: str
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: UserResponse


class TokenRefreshResponse(BaseModel):
    """Token refresh response model."""
    access_token: str
    token_type: str
    expires_in: int


class LoginResponse(BaseModel):
    """Login response model."""
    success: bool = True
    data: TokenResponse
    message: str = "Login successful"


class RegisterResponse(BaseModel):
    """Register response model."""
    success: bool = True
    data: dict
    message: str = "User registered successfully"


class RefreshResponse(BaseModel):
    """Refresh response model."""
    success: bool = True
    data: TokenRefreshResponse
    message: str = "Token refreshed successfully"


class LogoutResponse(BaseModel):
    """Logout response model."""
    success: bool = True
    message: str = "Logout successful"


class ForgotPasswordResponse(BaseModel):
    """Forgot password response model."""
    success: bool = True
    message: str = "Password reset email sent successfully"


class ResetPasswordResponse(BaseModel):
    """Reset password response model."""
    success: bool = True
    message: str = "Password reset successfully"


class ChangePasswordResponse(BaseModel):
    """Change password response model."""
    success: bool = True
    message: str = "Password changed successfully"


class EmailVerificationResponse(BaseModel):
    """Email verification response model."""
    success: bool = True
    message: str = "Email verified successfully"


class ResendVerificationResponse(BaseModel):
    """Resend verification response model."""
    success: bool = True
    message: str = "Verification email sent successfully"


class SessionsResponse(BaseModel):
    """Sessions response model."""
    success: bool = True
    data: List[SessionInfo]
    message: str = "Sessions retrieved successfully"


class RevokeSessionResponse(BaseModel):
    """Revoke session response model."""
    success: bool = True
    message: str = "Session revoked successfully"


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: str
    message: str 