"""
Notification schemas for the Project Management Dashboard API.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from pydantic.types import UUID4


class NotificationCreateRequest(BaseModel):
    """Notification creation request model."""
    user_id: UUID4 = Field(..., description="ID of the user to notify")
    type: str = Field(..., min_length=1, max_length=50, description="Type of notification")
    title: str = Field(..., min_length=1, max_length=255, description="Notification title")
    message: str = Field(..., min_length=1, max_length=5000, description="Notification message")
    entity_type: Optional[str] = Field(None, max_length=20, description="Type of related entity")
    entity_id: Optional[UUID4] = Field(None, description="ID of related entity")

    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        """Validate notification type."""
        if not v or not v.strip():
            raise ValueError("Notification type cannot be empty")
        # Check for common notification types
        allowed_types = [
            'task_assigned', 'task_completed', 'task_overdue', 'task_updated',
            'project_created', 'project_updated', 'project_completed',
            'comment_added', 'mention_added', 'time_entry_approved', 'time_entry_rejected',
            'milestone_reached', 'deadline_approaching', 'system_alert'
        ]
        if v not in allowed_types:
            raise ValueError(f"Notification type '{v}' is not allowed")
        return v.strip()

    @field_validator('entity_type')
    @classmethod
    def validate_entity_type(cls, v):
        """Validate entity type."""
        if v is not None:
            if not v.strip():
                raise ValueError("Entity type cannot be empty if provided")
            allowed_entity_types = ['Project', 'Task', 'Milestone', 'Comment', 'TimeEntry']
            if v not in allowed_entity_types:
                raise ValueError(f"Entity type '{v}' is not allowed")
            return v.strip()
        return v

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """Validate notification title."""
        if not v or not v.strip():
            raise ValueError("Notification title cannot be empty")
        return v.strip()

    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        """Validate notification message."""
        if not v or not v.strip():
            raise ValueError("Notification message cannot be empty")
        return v.strip()


class NotificationUpdateRequest(BaseModel):
    """Notification update request model."""
    is_read: bool = Field(..., description="Read status of the notification")

    @field_validator('is_read')
    @classmethod
    def validate_is_read(cls, v):
        """Validate read status."""
        return bool(v)


class NotificationResponse(BaseModel):
    """Notification response model."""
    id: UUID4
    user_id: UUID4
    type: str
    title: str
    message: str
    entity_type: Optional[str]
    entity_id: Optional[UUID4]
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Notification list response model."""
    success: bool
    data: List[NotificationResponse]
    message: str
    pagination: Optional[dict] = None


class NotificationCreateResponseWrapper(BaseModel):
    """Notification creation response wrapper."""
    success: bool
    data: NotificationResponse
    message: str


class NotificationUpdateResponseWrapper(BaseModel):
    """Notification update response wrapper."""
    success: bool
    data: NotificationResponse
    message: str


class NotificationDeleteResponseWrapper(BaseModel):
    """Notification deletion response wrapper."""
    success: bool
    message: str


class NotificationMarkAllReadResponseWrapper(BaseModel):
    """Notification mark all read response wrapper."""
    success: bool
    message: str
    updated_count: int


class NotificationFilterRequest(BaseModel):
    """Notification filter request model."""
    type: Optional[str] = Field(None, description="Filter by notification type")
    is_read: Optional[bool] = Field(None, description="Filter by read status")
    entity_type: Optional[str] = Field(None, description="Filter by entity type")
    entity_id: Optional[UUID4] = Field(None, description="Filter by entity ID")
    created_after: Optional[datetime] = Field(None, description="Filter by creation date (after)")
    created_before: Optional[datetime] = Field(None, description="Filter by creation date (before)")
    page: Optional[int] = Field(1, ge=1, description="Page number")
    limit: Optional[int] = Field(20, ge=1, le=100, description="Items per page")

    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        """Validate notification type filter."""
        if v is not None:
            if not v.strip():
                raise ValueError("Notification type cannot be empty if provided")
            allowed_types = [
                'task_assigned', 'task_completed', 'task_overdue', 'task_updated',
                'project_created', 'project_updated', 'project_completed',
                'comment_added', 'mention_added', 'time_entry_approved', 'time_entry_rejected',
                'milestone_reached', 'deadline_approaching', 'system_alert'
            ]
            if v not in allowed_types:
                raise ValueError(f"Notification type '{v}' is not allowed")
            return v.strip()
        return v

    @field_validator('entity_type')
    @classmethod
    def validate_entity_type(cls, v):
        """Validate entity type filter."""
        if v is not None:
            if not v.strip():
                raise ValueError("Entity type cannot be empty if provided")
            allowed_entity_types = ['Project', 'Task', 'Milestone', 'Comment', 'TimeEntry']
            if v not in allowed_entity_types:
                raise ValueError(f"Entity type '{v}' is not allowed")
            return v.strip()
        return v

    @field_validator('created_before')
    @classmethod
    def validate_date_range(cls, v, values):
        """Validate date range."""
        if v is not None and 'created_after' in values and values['created_after'] is not None:
            if v <= values['created_after']:
                raise ValueError("Created before date must be after created after date")
        return v


class NotificationStatsResponse(BaseModel):
    """Notification statistics response model."""
    success: bool
    data: Dict[str, Any]
    message: str 