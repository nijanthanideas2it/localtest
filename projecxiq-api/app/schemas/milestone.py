"""
Milestone schemas for milestone management operations.
"""
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, UUID4

from app.schemas.user import UserResponse


class MilestoneCreateRequest(BaseModel):
    """Milestone creation request model."""
    name: str = Field(..., min_length=1, max_length=255, description="Milestone name")
    description: Optional[str] = Field(None, description="Milestone description")
    due_date: date = Field(..., description="Milestone due date")
    dependencies: Optional[List[UUID4]] = Field(default=[], description="List of prerequisite milestone IDs")

    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v):
        """Validate due date is not in the past."""
        if v < date.today():
            raise ValueError("Due date cannot be in the past")
        return v

    @field_validator('dependencies')
    @classmethod
    def validate_dependencies(cls, v):
        """Validate dependencies list."""
        if v is None:
            return []
        return v


class MilestoneUpdateRequest(BaseModel):
    """Milestone update request model."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Milestone name")
    description: Optional[str] = Field(None, description="Milestone description")
    due_date: Optional[date] = Field(None, description="Milestone due date")
    is_completed: Optional[bool] = Field(None, description="Whether milestone is completed")

    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v):
        """Validate due date is not in the past."""
        if v is not None and v < date.today():
            raise ValueError("Due date cannot be in the past")
        return v


class MilestoneDependencyRequest(BaseModel):
    """Milestone dependency request model."""
    prerequisite_milestone_id: UUID4 = Field(..., description="ID of the prerequisite milestone")


class MilestoneDependencyResponse(BaseModel):
    """Milestone dependency response model."""
    id: UUID4
    dependent_milestone_id: UUID4
    prerequisite_milestone_id: UUID4
    created_at: datetime

    class Config:
        from_attributes = True


class MilestoneResponse(BaseModel):
    """Milestone response model."""
    id: UUID4
    name: str
    description: Optional[str] = None
    project_id: UUID4
    due_date: date
    is_completed: bool
    completed_at: Optional[datetime] = None
    dependencies_count: int = 0
    completion_percentage: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MilestoneDetailResponse(BaseModel):
    """Milestone detail response model."""
    id: UUID4
    name: str
    description: Optional[str] = None
    project_id: UUID4
    due_date: date
    is_completed: bool
    completed_at: Optional[datetime] = None
    dependencies: List[MilestoneDependencyResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MilestoneListResponse(BaseModel):
    """Milestone list response model."""
    success: bool = True
    data: List[MilestoneResponse]
    message: str = "Milestones retrieved successfully"


class MilestoneCreateResponseWrapper(BaseModel):
    """Milestone creation response wrapper."""
    success: bool = True
    data: MilestoneDetailResponse
    message: str = "Milestone created successfully"


class MilestoneUpdateResponseWrapper(BaseModel):
    """Milestone update response wrapper."""
    success: bool = True
    data: MilestoneDetailResponse
    message: str = "Milestone updated successfully"


class MilestoneDeleteResponseWrapper(BaseModel):
    """Milestone deletion response wrapper."""
    success: bool = True
    message: str = "Milestone deleted successfully"


class MilestoneDetailResponseWrapper(BaseModel):
    """Milestone detail response wrapper."""
    success: bool = True
    data: MilestoneDetailResponse
    message: str = "Milestone retrieved successfully"


class MilestoneDependencyCreateResponseWrapper(BaseModel):
    """Milestone dependency creation response wrapper."""
    success: bool = True
    data: MilestoneDependencyResponse
    message: str = "Milestone dependency created successfully"


class MilestoneStatsResponse(BaseModel):
    """Milestone statistics response model."""
    total_milestones: int
    completed_milestones: int
    overdue_milestones: int
    upcoming_milestones: int
    completion_percentage: float
    average_completion_time_days: Optional[float] = None

    class Config:
        from_attributes = True


class MilestoneStatsWrapper(BaseModel):
    """Milestone statistics response wrapper."""
    success: bool = True
    data: MilestoneStatsResponse
    message: str = "Milestone statistics retrieved successfully" 