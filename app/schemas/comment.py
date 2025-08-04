"""
Comment schemas for the Project Management Dashboard.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, UUID4

from app.schemas.user import UserResponse


class CommentCreateRequest(BaseModel):
    """Comment creation request model."""
    content: str = Field(..., min_length=1, max_length=5000, description="Comment content")
    entity_type: str = Field(..., description="Type of entity (Project, Task, Milestone)")
    entity_id: UUID4 = Field(..., description="ID of the entity being commented on")
    parent_comment_id: Optional[UUID4] = Field(None, description="Parent comment ID for threaded comments")

    @field_validator('entity_type')
    @classmethod
    def validate_entity_type(cls, v):
        """Validate entity type is valid."""
        valid_types = ['Project', 'Task', 'Milestone']
        if v not in valid_types:
            raise ValueError(f"Entity type must be one of: {', '.join(valid_types)}")
        return v

    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        """Validate content is not empty and within limits."""
        if not v or not v.strip():
            raise ValueError("Comment content cannot be empty")
        if len(v.strip()) > 5000:
            raise ValueError("Comment content cannot exceed 5000 characters")
        return v.strip()


class CommentUpdateRequest(BaseModel):
    """Comment update request model."""
    content: str = Field(..., min_length=1, max_length=5000, description="Updated comment content")

    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        """Validate content is not empty and within limits."""
        if not v or not v.strip():
            raise ValueError("Comment content cannot be empty")
        if len(v.strip()) > 5000:
            raise ValueError("Comment content cannot exceed 5000 characters")
        return v.strip()


class CommentResponse(BaseModel):
    """Comment response model."""
    id: UUID4
    content: str
    author_id: UUID4
    entity_type: str
    entity_id: UUID4
    parent_comment_id: Optional[UUID4]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CommentDetailResponse(BaseModel):
    """Comment detail response model with related data."""
    id: UUID4
    content: str
    author_id: UUID4
    entity_type: str
    entity_id: UUID4
    parent_comment_id: Optional[UUID4]
    created_at: datetime
    updated_at: datetime
    author: UserResponse
    replies_count: int = 0
    mentions_count: int = 0
    attachments_count: int = 0

    class Config:
        from_attributes = True


class CommentListResponse(BaseModel):
    """Comment list response model."""
    success: bool
    data: List[CommentDetailResponse]
    message: str
    pagination: Optional[dict] = None


class CommentCreateResponseWrapper(BaseModel):
    """Comment creation response wrapper."""
    success: bool
    data: CommentDetailResponse
    message: str


class CommentUpdateResponseWrapper(BaseModel):
    """Comment update response wrapper."""
    success: bool
    data: CommentDetailResponse
    message: str


class CommentDeleteResponseWrapper(BaseModel):
    """Comment deletion response wrapper."""
    success: bool
    message: str


class CommentDetailResponseWrapper(BaseModel):
    """Comment detail response wrapper."""
    success: bool
    data: CommentDetailResponse
    message: str


class CommentFilterRequest(BaseModel):
    """Comment filter request model."""
    entity_type: Optional[str] = Field(None, description="Filter by entity type")
    entity_id: Optional[UUID4] = Field(None, description="Filter by entity ID")
    author_id: Optional[UUID4] = Field(None, description="Filter by author ID")
    parent_comment_id: Optional[UUID4] = Field(None, description="Filter by parent comment ID")
    include_replies: Optional[bool] = Field(True, description="Include replies in results")
    page: Optional[int] = Field(1, ge=1, description="Page number")
    limit: Optional[int] = Field(20, ge=1, le=100, description="Items per page")

    @field_validator('entity_type')
    @classmethod
    def validate_entity_type(cls, v):
        """Validate entity type is valid."""
        if v is not None:
            valid_types = ['Project', 'Task', 'Milestone']
            if v not in valid_types:
                raise ValueError(f"Entity type must be one of: {', '.join(valid_types)}")
        return v


class CommentSearchRequest(BaseModel):
    """Comment search request model."""
    query: str = Field(..., min_length=1, max_length=100, description="Search query")
    entity_type: Optional[str] = Field(None, description="Filter by entity type")
    entity_id: Optional[UUID4] = Field(None, description="Filter by entity ID")
    author_id: Optional[UUID4] = Field(None, description="Filter by author ID")
    page: Optional[int] = Field(1, ge=1, description="Page number")
    limit: Optional[int] = Field(20, ge=1, le=100, description="Items per page")

    @field_validator('query')
    @classmethod
    def validate_query(cls, v):
        """Validate search query."""
        if not v or not v.strip():
            raise ValueError("Search query cannot be empty")
        return v.strip()

    @field_validator('entity_type')
    @classmethod
    def validate_entity_type(cls, v):
        """Validate entity type is valid."""
        if v is not None:
            valid_types = ['Project', 'Task', 'Milestone']
            if v not in valid_types:
                raise ValueError(f"Entity type must be one of: {', '.join(valid_types)}")
        return v


class CommentThreadResponse(BaseModel):
    """Comment thread response model for threaded discussions."""
    success: bool
    data: List[CommentDetailResponse]
    message: str
    pagination: Optional[dict] = None
    thread_info: Dict[str, Any] = {
        "total_comments": 0,
        "total_replies": 0,
        "max_depth": 0
    }


class CommentMentionCreateRequest(BaseModel):
    """Comment mention creation request model."""
    mentioned_user_id: UUID4 = Field(..., description="ID of the user to mention")

    @field_validator('mentioned_user_id')
    @classmethod
    def validate_mentioned_user_id(cls, v):
        """Validate mentioned user ID is not empty."""
        if not v:
            raise ValueError("Mentioned user ID cannot be empty")
        return v


class CommentMentionResponse(BaseModel):
    """Comment mention response model."""
    id: UUID4
    comment_id: UUID4
    mentioned_user_id: UUID4
    created_at: datetime
    mentioned_user: UserResponse

    class Config:
        from_attributes = True


class CommentMentionListResponse(BaseModel):
    """Comment mention list response model."""
    success: bool
    data: List[CommentMentionResponse]
    message: str
    pagination: Optional[dict] = None


class CommentMentionCreateResponseWrapper(BaseModel):
    """Comment mention creation response wrapper."""
    success: bool
    data: CommentMentionResponse
    message: str


class CommentMentionDeleteResponseWrapper(BaseModel):
    """Comment mention deletion response wrapper."""
    success: bool
    message: str


class UserMentionsResponse(BaseModel):
    """User mentions response model."""
    success: bool
    data: List[CommentMentionResponse]
    message: str
    pagination: Optional[dict] = None


class CommentAttachmentCreateRequest(BaseModel):
    """Comment attachment creation request model."""
    file_name: str = Field(..., min_length=1, max_length=255, description="Name of the file")
    file_size: int = Field(..., gt=0, le=10485760, description="Size of the file in bytes (max 10MB)")
    mime_type: str = Field(..., min_length=1, max_length=100, description="MIME type of the file")

    @field_validator('file_name')
    @classmethod
    def validate_file_name(cls, v):
        """Validate file name."""
        if not v or not v.strip():
            raise ValueError("File name cannot be empty")
        # Check for invalid characters
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        if any(char in v for char in invalid_chars):
            raise ValueError("File name contains invalid characters")
        return v.strip()

    @field_validator('mime_type')
    @classmethod
    def validate_mime_type(cls, v):
        """Validate MIME type."""
        if not v or not v.strip():
            raise ValueError("MIME type cannot be empty")
        # Check for common allowed file types
        allowed_types = [
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/plain', 'text/csv', 'application/zip', 'application/x-zip-compressed'
        ]
        if v not in allowed_types:
            raise ValueError(f"MIME type {v} is not allowed")
        return v.strip()


class CommentAttachmentResponse(BaseModel):
    """Comment attachment response model."""
    id: UUID4
    comment_id: UUID4
    file_name: str
    file_size: int
    mime_type: str
    file_path: str
    created_at: datetime

    class Config:
        from_attributes = True


class CommentAttachmentListResponse(BaseModel):
    """Comment attachment list response model."""
    success: bool
    data: List[CommentAttachmentResponse]
    message: str
    pagination: Optional[dict] = None


class CommentAttachmentCreateResponseWrapper(BaseModel):
    """Comment attachment creation response wrapper."""
    success: bool
    data: CommentAttachmentResponse
    message: str


class CommentAttachmentDeleteResponseWrapper(BaseModel):
    """Comment attachment deletion response wrapper."""
    success: bool
    message: str 