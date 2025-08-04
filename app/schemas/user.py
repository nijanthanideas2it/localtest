"""
User schemas for request and response models.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.config import settings


class UserCreateRequest(BaseModel):
    """User creation request model."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=settings.PASSWORD_MIN_LENGTH, description="User password")
    first_name: str = Field(..., min_length=1, max_length=50, description="User first name")
    last_name: str = Field(..., min_length=1, max_length=50, description="User last name")
    role: str = Field(default="Developer", description="User role")
    hourly_rate: Optional[float] = Field(None, ge=0, description="User hourly rate")
    is_active: bool = Field(default=True, description="User active status")
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        """Validate user role."""
        allowed_roles = ["Admin", "Project Manager", "Team Lead", "Developer"]
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of: {', '.join(allowed_roles)}")
        return v


class UserUpdateRequest(BaseModel):
    """User update request model."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50, description="User first name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=50, description="User last name")
    role: Optional[str] = Field(None, description="User role")
    hourly_rate: Optional[float] = Field(None, ge=0, description="User hourly rate")
    is_active: Optional[bool] = Field(None, description="User active status")
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        """Validate user role."""
        if v is not None:
            allowed_roles = ["Admin", "Project Manager", "Team Lead", "Developer"]
            if v not in allowed_roles:
                raise ValueError(f"Role must be one of: {', '.join(allowed_roles)}")
        return v


class UserSkillRequest(BaseModel):
    """User skill request model."""
    skill_name: str = Field(..., min_length=1, max_length=100, description="Skill name")
    proficiency_level: str = Field(..., description="Proficiency level")
    
    @field_validator('proficiency_level')
    @classmethod
    def validate_proficiency_level(cls, v):
        """Validate proficiency level."""
        allowed_levels = ["Beginner", "Intermediate", "Advanced", "Expert"]
        if v not in allowed_levels:
            raise ValueError(f"Proficiency level must be one of: {', '.join(allowed_levels)}")
        return v


class UserSkillResponse(BaseModel):
    """User skill response model."""
    id: str
    skill_name: str
    proficiency_level: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    first_name: str
    last_name: str
    role: str
    is_active: bool
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        """Convert UUID objects to strings."""
        if v is None:
            return v
        # Handle UUID objects
        if hasattr(v, 'hex'):
            return str(v)
        # Handle UUID class instances
        elif hasattr(v, '__class__') and v.__class__.__name__ == 'UUID':
            return str(v)
        # Handle string UUIDs
        elif isinstance(v, str):
            return v
        # Handle any other UUID-like objects
        else:
            return str(v)
    
    @field_validator('role', mode='before')
    @classmethod
    def convert_role_format(cls, v):
        """Convert role format to match database."""
        # Map database roles to expected format
        role_mapping = {
            "ProjectManager": "ProjectManager",
            "Project Manager": "ProjectManager",
            "TeamLead": "TeamLead", 
            "Team Lead": "TeamLead",
            "Admin": "Admin",
            "Developer": "Developer"
        }
        return role_mapping.get(v, v)
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """User list response model."""
    id: str
    email: str
    first_name: str
    last_name: str
    role: str
    hourly_rate: Optional[float] = None
    is_active: bool
    created_at: datetime
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        """Convert UUID objects to strings."""
        if v is None:
            return v
        # Handle UUID objects
        if hasattr(v, 'hex'):
            return str(v)
        # Handle UUID class instances
        elif hasattr(v, '__class__') and v.__class__.__name__ == 'UUID':
            return str(v)
        # Handle string UUIDs
        elif isinstance(v, str):
            return v
        # Handle any other UUID-like objects
        else:
            return str(v)
    
    @field_validator('role', mode='before')
    @classmethod
    def convert_role_format(cls, v):
        """Convert role format for consistency."""
        if v is None:
            return v
        role_mapping = {
            "ProjectManager": "Project Manager",
            "Project Manager": "Project Manager", 
            "TeamLead": "Team Lead",
            "Team Lead": "TeamLead", 
            "TeamLead": "TeamLead",
            "Admin": "Admin",
            "Developer": "Developer"
        }
        return role_mapping.get(v, v)
    
    class Config:
        from_attributes = True


class PaginationInfo(BaseModel):
    """Pagination information model."""
    page: int
    limit: int
    total: int
    pages: int


class UserListResponseWrapper(BaseModel):
    """User list response wrapper with pagination."""
    success: bool = True
    data: List[UserListResponse]
    pagination: PaginationInfo
    message: str = "Users retrieved successfully"


class UserResponseWrapper(BaseModel):
    """User response wrapper."""
    success: bool = True
    data: UserResponse
    message: str = "User retrieved successfully"


class UserCreateResponseWrapper(BaseModel):
    """User creation response wrapper."""
    success: bool = True
    data: UserResponse
    message: str = "User created successfully"


class UserUpdateResponseWrapper(BaseModel):
    """User update response wrapper."""
    success: bool = True
    data: UserResponse
    message: str = "User updated successfully"


class UserDeleteResponseWrapper(BaseModel):
    """User deletion response wrapper."""
    success: bool = True
    message: str = "User deleted successfully"


class UserSkillResponseWrapper(BaseModel):
    """User skill response wrapper."""
    success: bool = True
    data: UserSkillResponse
    message: str = "Skill added successfully"


class UserQueryParams(BaseModel):
    """User query parameters for filtering and pagination."""
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")
    role: Optional[str] = Field(None, description="Filter by role")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    search: Optional[str] = Field(None, min_length=1, description="Search by name or email")
    
    @field_validator('role')
    @classmethod
    def validate_role_filter(cls, v):
        """Validate role filter."""
        if v is not None:
            allowed_roles = ["Admin", "Project Manager", "Team Lead", "Developer"]
            if v not in allowed_roles:
                raise ValueError(f"Role must be one of: {', '.join(allowed_roles)}")
        return v


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: str
    message: str 