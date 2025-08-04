"""
File version schemas for file versioning functionality.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from uuid import UUID

from app.schemas.user import UserResponse


class FileVersionRequest(BaseModel):
    """Request model for file version operations."""
    change_description: Optional[str] = Field(None, description="Description of changes in this version")

    @field_validator('change_description')
    @classmethod
    def validate_change_description(cls, v):
        """Validate change description length."""
        if v and len(v) > 1000:
            raise ValueError("Change description cannot exceed 1000 characters")
        return v


class FileVersionResponse(BaseModel):
    """Response model for file version information."""
    id: UUID = Field(..., description="Version ID")
    file_id: UUID = Field(..., description="File ID")
    version_number: str = Field(..., description="Version number")
    file_name: str = Field(..., description="File name")
    original_name: str = Field(..., description="Original file name")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="File MIME type")
    description: Optional[str] = Field(None, description="File description")
    change_description: Optional[str] = Field(None, description="Description of changes")
    is_current: bool = Field(..., description="Whether this is the current version")
    file_extension: str = Field(..., description="File extension")
    is_image: bool = Field(..., description="Whether the file is an image")
    is_document: bool = Field(..., description="Whether the file is a document")
    is_archive: bool = Field(..., description="Whether the file is an archive")
    human_readable_size: str = Field(..., description="Human-readable file size")
    created_by: UserResponse = Field(..., description="User who created this version")
    created_at: datetime = Field(..., description="Version creation timestamp")
    updated_at: datetime = Field(..., description="Version update timestamp")

    class Config:
        from_attributes = True


class FileVersionListResponse(BaseModel):
    """Response model for file version list."""
    versions: List[FileVersionResponse] = Field(..., description="List of file versions")
    total_count: int = Field(..., description="Total number of versions")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")
    current_version: Optional[FileVersionResponse] = Field(None, description="Current version")


class FileVersionCreateResponse(BaseModel):
    """Response model for file version creation."""
    version: FileVersionResponse = Field(..., description="Created version information")
    message: str = Field(..., description="Creation success message")
    download_url: str = Field(..., description="Download URL for the version")


class FileVersionRollbackResponse(BaseModel):
    """Response model for file version rollback."""
    message: str = Field(..., description="Rollback success message")
    current_version: FileVersionResponse = Field(..., description="New current version")
    previous_version: FileVersionResponse = Field(..., description="Previous current version")


class FileVersionStatsResponse(BaseModel):
    """Response model for file version statistics."""
    total_versions: int = Field(..., description="Total number of versions")
    current_version_number: str = Field(..., description="Current version number")
    first_version_date: datetime = Field(..., description="Date of first version")
    last_version_date: datetime = Field(..., description="Date of last version")
    versions_by_creator: dict = Field(..., description="Versions grouped by creator")
    total_size_all_versions: int = Field(..., description="Total size of all versions")
    human_readable_total_size: str = Field(..., description="Human-readable total size")


class FileVersionComparisonResponse(BaseModel):
    """Response model for file version comparison."""
    version1: FileVersionResponse = Field(..., description="First version for comparison")
    version2: FileVersionResponse = Field(..., description="Second version for comparison")
    differences: dict = Field(..., description="Differences between versions")
    size_change: int = Field(..., description="Size change in bytes")
    size_change_percentage: float = Field(..., description="Size change percentage")
    time_between_versions: str = Field(..., description="Time between versions")


class FileVersionFilterRequest(BaseModel):
    """Request model for file version filtering."""
    version_number: Optional[str] = Field(None, description="Filter by version number")
    created_by: Optional[UUID] = Field(None, description="Filter by creator")
    is_current: Optional[bool] = Field(None, description="Filter by current version status")
    date_from: Optional[datetime] = Field(None, description="Filter by creation date from")
    date_to: Optional[datetime] = Field(None, description="Filter by creation date to")
    search: Optional[str] = Field(None, description="Search in change descriptions")

    @field_validator('search')
    @classmethod
    def validate_search(cls, v):
        """Validate search term length."""
        if v and len(v) > 100:
            raise ValueError("Search term cannot exceed 100 characters")
        return v

    @field_validator('date_to')
    @classmethod
    def validate_date_range(cls, v, values):
        """Validate date range."""
        if v and 'date_from' in values and values['date_from']:
            if v < values['date_from']:
                raise ValueError("End date must be after start date")
        return v


class FileVersionHistoryResponse(BaseModel):
    """Response model for file version history."""
    file_id: UUID = Field(..., description="File ID")
    file_name: str = Field(..., description="Current file name")
    total_versions: int = Field(..., description="Total number of versions")
    current_version: FileVersionResponse = Field(..., description="Current version")
    version_history: List[FileVersionResponse] = Field(..., description="Version history")
    can_rollback: bool = Field(..., description="Whether rollback is possible")
    rollback_options: List[FileVersionResponse] = Field(..., description="Available rollback versions") 