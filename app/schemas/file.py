"""
File schemas for file upload and management functionality.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from uuid import UUID

from app.schemas.user import UserResponse


class FileUploadRequest(BaseModel):
    """Request model for file upload."""
    description: Optional[str] = Field(None, description="File description")
    is_public: bool = Field(False, description="Whether the file is public")

    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        """Validate description length."""
        if v and len(v) > 1000:
            raise ValueError("Description cannot exceed 1000 characters")
        return v


class FileResponse(BaseModel):
    """Response model for file information."""
    id: UUID = Field(..., description="File ID")
    file_name: str = Field(..., description="File name")
    original_name: str = Field(..., description="Original file name")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="File MIME type")
    description: Optional[str] = Field(None, description="File description")
    is_public: bool = Field(..., description="Whether the file is public")
    is_deleted: bool = Field(..., description="Whether the file is deleted")
    file_extension: str = Field(..., description="File extension")
    is_image: bool = Field(..., description="Whether the file is an image")
    is_document: bool = Field(..., description="Whether the file is a document")
    is_archive: bool = Field(..., description="Whether the file is an archive")
    human_readable_size: str = Field(..., description="Human-readable file size")
    uploaded_by: UserResponse = Field(..., description="User who uploaded the file")
    created_at: datetime = Field(..., description="Upload timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class FileListResponse(BaseModel):
    """Response model for file list."""
    files: List[FileResponse] = Field(..., description="List of files")
    total_count: int = Field(..., description="Total number of files")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")


class FileUpdateRequest(BaseModel):
    """Request model for file updates."""
    description: Optional[str] = Field(None, description="File description")
    is_public: Optional[bool] = Field(None, description="Whether the file is public")

    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        """Validate description length."""
        if v and len(v) > 1000:
            raise ValueError("Description cannot exceed 1000 characters")
        return v


class FileUploadResponse(BaseModel):
    """Response model for file upload."""
    file: FileResponse = Field(..., description="Uploaded file information")
    download_url: str = Field(..., description="Download URL for the file")
    message: str = Field(..., description="Upload success message")


class FileDeleteResponse(BaseModel):
    """Response model for file deletion."""
    message: str = Field(..., description="Deletion success message")
    file_id: UUID = Field(..., description="Deleted file ID")


class FileFilterRequest(BaseModel):
    """Request model for file filtering."""
    mime_type: Optional[str] = Field(None, description="Filter by MIME type")
    uploaded_by: Optional[UUID] = Field(None, description="Filter by uploader")
    is_public: Optional[bool] = Field(None, description="Filter by public status")
    is_deleted: Optional[bool] = Field(False, description="Filter by deletion status")
    search: Optional[str] = Field(None, description="Search in file names and descriptions")
    date_from: Optional[datetime] = Field(None, description="Filter by upload date from")
    date_to: Optional[datetime] = Field(None, description="Filter by upload date to")

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


class FileStatsResponse(BaseModel):
    """Response model for file statistics."""
    total_files: int = Field(..., description="Total number of files")
    total_size: int = Field(..., description="Total size in bytes")
    human_readable_total_size: str = Field(..., description="Human-readable total size")
    files_by_type: dict = Field(..., description="Files grouped by MIME type")
    files_by_uploader: dict = Field(..., description="Files grouped by uploader")
    recent_uploads: List[FileResponse] = Field(..., description="Recently uploaded files") 