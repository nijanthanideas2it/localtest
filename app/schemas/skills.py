"""
Skills schemas for user skills management.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class SkillRequest(BaseModel):
    """Skill request model."""
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


class SkillResponse(BaseModel):
    """Skill response model."""
    id: str
    skill_name: str
    proficiency_level: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class SkillListResponse(BaseModel):
    """Skill list response model."""
    success: bool = True
    data: List[SkillResponse]
    message: str = "Skills retrieved successfully"


class SkillResponseWrapper(BaseModel):
    """Skill response wrapper."""
    success: bool = True
    data: SkillResponse
    message: str = "Skill operation completed successfully"


class SkillCreateResponseWrapper(BaseModel):
    """Skill creation response wrapper."""
    success: bool = True
    data: SkillResponse
    message: str = "Skill added successfully"


class SkillUpdateResponseWrapper(BaseModel):
    """Skill update response wrapper."""
    success: bool = True
    data: SkillResponse
    message: str = "Skill updated successfully"


class SkillDeleteResponseWrapper(BaseModel):
    """Skill deletion response wrapper."""
    success: bool = True
    message: str = "Skill deleted successfully"


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: str
    message: str 