"""
Team schemas for project team management operations.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, UUID4

from app.schemas.user import UserResponse


class TeamMemberRoleUpdateRequest(BaseModel):
    """Team member role update request model."""
    role: str = Field(..., min_length=1, max_length=50, description="New role in the project")
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        """Validate role is not empty."""
        if not v.strip():
            raise ValueError("Role cannot be empty")
        return v.strip()


class TeamMemberDetailResponse(BaseModel):
    """Team member detail response model."""
    id: UUID4
    user_id: UUID4
    role: str
    joined_at: datetime
    left_at: Optional[datetime] = None
    user: Optional[UserResponse] = None
    
    class Config:
        from_attributes = True


class TeamListResponse(BaseModel):
    """Team list response model."""
    success: bool = True
    data: List[TeamMemberDetailResponse]
    message: str = "Team members retrieved successfully"


class TeamMemberUpdateResponse(BaseModel):
    """Team member update response model."""
    success: bool = True
    data: TeamMemberDetailResponse
    message: str = "Team member updated successfully"


class TeamMemberAddResponse(BaseModel):
    """Team member add response model."""
    success: bool = True
    data: TeamMemberDetailResponse
    message: str = "Team member added successfully"


class TeamMemberRemoveResponse(BaseModel):
    """Team member remove response model."""
    success: bool = True
    message: str = "Team member removed successfully"


class TeamStatsResponse(BaseModel):
    """Team statistics response model."""
    total_members: int
    active_members: int
    inactive_members: int
    roles_distribution: dict
    average_tenure_days: Optional[float] = None
    
    class Config:
        from_attributes = True


class TeamStatsWrapper(BaseModel):
    """Team statistics response wrapper."""
    success: bool = True
    data: TeamStatsResponse
    message: str = "Team statistics retrieved successfully" 