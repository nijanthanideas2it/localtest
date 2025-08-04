"""
Profile schemas for user profile management.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.schemas.user import UserSkillResponse


class ProfileUpdateRequest(BaseModel):
    """Profile update request model."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50, description="User first name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=50, description="User last name")
    hourly_rate: Optional[float] = Field(None, ge=0, description="User hourly rate")
    bio: Optional[str] = Field(None, max_length=500, description="User bio")
    phone: Optional[str] = Field(None, max_length=20, description="User phone number")
    location: Optional[str] = Field(None, max_length=100, description="User location")
    website: Optional[str] = Field(None, max_length=200, description="User website")
    linkedin: Optional[str] = Field(None, max_length=200, description="LinkedIn profile URL")
    github: Optional[str] = Field(None, max_length=200, description="GitHub profile URL")
    twitter: Optional[str] = Field(None, max_length=200, description="Twitter profile URL")


class ProfileResponse(BaseModel):
    """Profile response model."""
    id: str
    email: str
    first_name: str
    last_name: str
    role: str
    hourly_rate: Optional[float] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    twitter: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    skills: Optional[List[UserSkillResponse]] = []
    
    class Config:
        from_attributes = True


class AvatarUploadResponse(BaseModel):
    """Avatar upload response model."""
    success: bool = True
    data: dict
    message: str = "Avatar uploaded successfully"


class ProfileUpdateResponse(BaseModel):
    """Profile update response model."""
    success: bool = True
    data: ProfileResponse
    message: str = "Profile updated successfully"


class ProfileResponseWrapper(BaseModel):
    """Profile response wrapper."""
    success: bool = True
    data: ProfileResponse
    message: str = "Profile retrieved successfully"


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: str
    message: str 