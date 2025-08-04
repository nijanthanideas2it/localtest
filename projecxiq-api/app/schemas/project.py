"""
Project schemas for project management operations.
"""
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, UUID4

from app.schemas.user import UserResponse


class TeamMemberRequest(BaseModel):
    """Team member request model."""
    user_id: UUID4 = Field(..., description="User ID")
    role: str = Field(..., min_length=1, max_length=50, description="Role in the project")


class ProjectCreateRequest(BaseModel):
    """Project creation request model."""
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    start_date: date = Field(..., description="Project start date")
    end_date: Optional[date] = Field(None, description="Project end date")
    budget: Optional[Decimal] = Field(None, ge=0, description="Project budget")
    manager_id: UUID4 = Field(..., description="Project manager ID")
    team_members: Optional[List[TeamMemberRequest]] = Field(default=[], description="Initial team members")

    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v, info):
        """Validate end date is after start date."""
        if v and 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError("End date must be after start date")
        return v

    @field_validator('team_members')
    @classmethod
    def validate_team_members(cls, v):
        """Validate team members list."""
        if v is None:
            return []
        return v


class ProjectUpdateRequest(BaseModel):
    """Project update request model."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    start_date: Optional[date] = Field(None, description="Project start date")
    end_date: Optional[date] = Field(None, description="Project end date")
    budget: Optional[Decimal] = Field(None, ge=0, description="Project budget")
    status: Optional[str] = Field(None, description="Project status")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Validate project status."""
        if v is not None:
            allowed_statuses = ["Draft", "Active", "OnHold", "Completed", "Cancelled"]
            if v not in allowed_statuses:
                raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
        return v

    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v, info):
        """Validate end date is after start date."""
        if v and 'start_date' in info.data and info.data['start_date'] and v <= info.data['start_date']:
            raise ValueError("End date must be after start date")
        return v


class TeamMemberResponse(BaseModel):
    """Team member response model."""
    user_id: str
    role: str
    joined_at: datetime
    left_at: Optional[datetime] = None
    user: Optional[UserResponse] = None

    @field_validator('user_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        """Convert UUID objects to strings."""
        if hasattr(v, 'hex'):
            return str(v)
        return v

    class Config:
        from_attributes = True


class ProjectResponse(BaseModel):
    """Project response model."""
    id: str
    name: str
    description: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    budget: Optional[Decimal] = None
    actual_cost: Optional[Decimal] = None
    status: str
    manager_id: str
    manager: Optional[UserResponse] = None
    team_members: List[TeamMemberResponse] = []
    created_at: datetime
    updated_at: datetime

    @field_validator('id', 'manager_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        """Convert UUID objects to strings."""
        if hasattr(v, 'hex'):
            return str(v)
        return v

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """Project list response model."""
    id: str
    name: str
    description: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    budget: Optional[Decimal] = None
    actual_cost: Optional[Decimal] = None
    status: str
    manager: Optional[UserResponse] = None
    team_size: int = 0
    progress_percentage: Optional[Decimal] = None
    created_at: datetime

    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        """Convert UUID objects to strings."""
        if hasattr(v, 'hex'):
            return str(v)
        return v

    class Config:
        from_attributes = True


class ProjectQueryParams(BaseModel):
    """Project query parameters for filtering and pagination."""
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")
    status: Optional[str] = Field(None, description="Filter by status")
    manager_id: Optional[UUID4] = Field(None, description="Filter by manager")
    search: Optional[str] = Field(None, description="Search by name")
    my_projects: Optional[bool] = Field(None, description="Show only user's projects")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Validate status filter."""
        if v is not None:
            allowed_statuses = ["Draft", "Active", "OnHold", "Completed", "Cancelled"]
            if v not in allowed_statuses:
                raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
        return v


class ProjectCreateResponseWrapper(BaseModel):
    """Project creation response wrapper."""
    success: bool = True
    data: ProjectResponse
    message: str = "Project created successfully"


class ProjectUpdateResponseWrapper(BaseModel):
    """Project update response wrapper."""
    success: bool = True
    data: ProjectResponse
    message: str = "Project updated successfully"


class ProjectDeleteResponseWrapper(BaseModel):
    """Project deletion response wrapper."""
    success: bool = True
    message: str = "Project deleted successfully"


class ProjectListResponseWrapper(BaseModel):
    """Project list response wrapper."""
    success: bool = True
    data: List[ProjectListResponse]
    pagination: Dict[str, Any]
    message: str = "Projects retrieved successfully"


class ProjectResponseWrapper(BaseModel):
    """Project response wrapper."""
    success: bool = True
    data: ProjectResponse
    message: str = "Project retrieved successfully" 