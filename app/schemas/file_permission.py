"""
File permission schemas for file access control operations.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator
from pydantic.types import UUID4

from app.schemas.user import UserResponse


class PermissionType(str, Enum):
    """Types of file permissions."""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class SharePermissionType(str, Enum):
    """Types of file share permissions."""
    READ = "read"
    WRITE = "write"


class FilePermissionRequest(BaseModel):
    """Request model for file permission operations."""
    user_id: UUID4 = Field(..., description="User ID to grant permission to")
    permission_type: PermissionType = Field(..., description="Type of permission to grant")
    expires_at: Optional[datetime] = Field(None, description="Permission expiration date")

    @field_validator('expires_at')
    @classmethod
    def validate_expires_at(cls, v):
        """Validate that expiration date is in the future."""
        if v and v <= datetime.now():
            raise ValueError("Expiration date must be in the future")
        return v


class FilePermissionResponse(BaseModel):
    """Response model for file permission information."""
    id: UUID4 = Field(..., description="Permission ID")
    file_id: UUID4 = Field(..., description="File ID")
    user: UserResponse = Field(..., description="User who has permission")
    permission_type: PermissionType = Field(..., description="Type of permission")
    granted_by: UserResponse = Field(..., description="User who granted the permission")
    expires_at: Optional[datetime] = Field(None, description="Permission expiration date")
    is_active: bool = Field(..., description="Whether the permission is active")
    is_expired: bool = Field(..., description="Whether the permission has expired")
    is_valid: bool = Field(..., description="Whether the permission is valid")
    created_at: datetime = Field(..., description="Permission creation timestamp")
    updated_at: datetime = Field(..., description="Permission update timestamp")

    class Config:
        from_attributes = True


class FilePermissionListResponse(BaseModel):
    """Response model for file permission list."""
    permissions: List[FilePermissionResponse] = Field(..., description="List of permissions")
    total_count: int = Field(..., description="Total number of permissions")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")


class FilePermissionUpdateRequest(BaseModel):
    """Request model for updating file permissions."""
    permission_type: Optional[PermissionType] = Field(None, description="New permission type")
    expires_at: Optional[datetime] = Field(None, description="New expiration date")
    is_active: Optional[bool] = Field(None, description="Whether to activate/deactivate permission")

    @field_validator('expires_at')
    @classmethod
    def validate_expires_at(cls, v):
        """Validate that expiration date is in the future."""
        if v and v <= datetime.now():
            raise ValueError("Expiration date must be in the future")
        return v


class FileShareRequest(BaseModel):
    """Request model for creating file shares."""
    permission_type: SharePermissionType = Field(SharePermissionType.READ, description="Type of permission for the share")
    max_downloads: Optional[int] = Field(None, ge=1, description="Maximum number of downloads (null for unlimited)")
    expires_at: Optional[datetime] = Field(None, description="Share expiration date")

    @field_validator('max_downloads')
    @classmethod
    def validate_max_downloads(cls, v):
        """Validate maximum downloads."""
        if v is not None and v < 1:
            raise ValueError("Maximum downloads must be at least 1")
        return v

    @field_validator('expires_at')
    @classmethod
    def validate_expires_at(cls, v):
        """Validate that expiration date is in the future."""
        if v and v <= datetime.now():
            raise ValueError("Expiration date must be in the future")
        return v


class FileShareResponse(BaseModel):
    """Response model for file share information."""
    id: UUID4 = Field(..., description="Share ID")
    file_id: UUID4 = Field(..., description="File ID")
    share_token: str = Field(..., description="Share token")
    permission_type: SharePermissionType = Field(..., description="Type of permission")
    max_downloads: Optional[int] = Field(None, description="Maximum number of downloads")
    download_count: int = Field(..., description="Current download count")
    expires_at: Optional[datetime] = Field(None, description="Share expiration date")
    is_active: bool = Field(..., description="Whether the share is active")
    is_expired: bool = Field(..., description="Whether the share has expired")
    is_download_limit_reached: bool = Field(..., description="Whether download limit is reached")
    is_valid: bool = Field(..., description="Whether the share is valid")
    share_url: str = Field(..., description="Share URL")
    created_by: UserResponse = Field(..., description="User who created the share")
    created_at: datetime = Field(..., description="Share creation timestamp")
    updated_at: datetime = Field(..., description="Share update timestamp")

    class Config:
        from_attributes = True


class FileShareListResponse(BaseModel):
    """Response model for file share list."""
    shares: List[FileShareResponse] = Field(..., description="List of shares")
    total_count: int = Field(..., description="Total number of shares")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")


class FileShareUpdateRequest(BaseModel):
    """Request model for updating file shares."""
    permission_type: Optional[SharePermissionType] = Field(None, description="New permission type")
    max_downloads: Optional[int] = Field(None, ge=1, description="New maximum downloads")
    expires_at: Optional[datetime] = Field(None, description="New expiration date")
    is_active: Optional[bool] = Field(None, description="Whether to activate/deactivate share")

    @field_validator('max_downloads')
    @classmethod
    def validate_max_downloads(cls, v):
        """Validate maximum downloads."""
        if v is not None and v < 1:
            raise ValueError("Maximum downloads must be at least 1")
        return v

    @field_validator('expires_at')
    @classmethod
    def validate_expires_at(cls, v):
        """Validate that expiration date is in the future."""
        if v and v <= datetime.now():
            raise ValueError("Expiration date must be in the future")
        return v


class FilePermissionStatsResponse(BaseModel):
    """Response model for file permission statistics."""
    total_permissions: int = Field(..., description="Total number of permissions")
    active_permissions: int = Field(..., description="Number of active permissions")
    expired_permissions: int = Field(..., description="Number of expired permissions")
    permissions_by_type: dict = Field(..., description="Permissions grouped by type")
    permissions_by_user: dict = Field(..., description="Permissions grouped by user")
    recent_permissions: List[FilePermissionResponse] = Field(..., description="Recently granted permissions")


class FileShareStatsResponse(BaseModel):
    """Response model for file share statistics."""
    total_shares: int = Field(..., description="Total number of shares")
    active_shares: int = Field(..., description="Number of active shares")
    expired_shares: int = Field(..., description="Number of expired shares")
    shares_by_type: dict = Field(..., description="Shares grouped by permission type")
    total_downloads: int = Field(..., description="Total downloads across all shares")
    recent_shares: List[FileShareResponse] = Field(..., description="Recently created shares")


class FileAccessResponse(BaseModel):
    """Response model for file access information."""
    file_id: UUID4 = Field(..., description="File ID")
    user_id: UUID4 = Field(..., description="User ID")
    has_access: bool = Field(..., description="Whether user has access to file")
    permission_type: Optional[PermissionType] = Field(None, description="User's permission type")
    is_owner: bool = Field(..., description="Whether user is the file owner")
    can_read: bool = Field(..., description="Whether user can read the file")
    can_write: bool = Field(..., description="Whether user can write to the file")
    can_delete: bool = Field(..., description="Whether user can delete the file")
    can_share: bool = Field(..., description="Whether user can share the file")
    can_manage_permissions: bool = Field(..., description="Whether user can manage file permissions") 