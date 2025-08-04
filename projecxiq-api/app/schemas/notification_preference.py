"""
Notification Preference schemas for the Project Management Dashboard API.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from pydantic.types import UUID4


class NotificationPreferenceCreateRequest(BaseModel):
    """Notification preference creation request model."""
    notification_type: str = Field(..., description="Type of notification")
    email_enabled: bool = Field(True, description="Enable email notifications")
    push_enabled: bool = Field(True, description="Enable push notifications")
    in_app_enabled: bool = Field(True, description="Enable in-app notifications")

    @field_validator('notification_type')
    @classmethod
    def validate_notification_type(cls, v):
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


class NotificationPreferenceUpdateRequest(BaseModel):
    """Notification preference update request model."""
    email_enabled: Optional[bool] = Field(None, description="Enable email notifications")
    push_enabled: Optional[bool] = Field(None, description="Enable push notifications")
    in_app_enabled: Optional[bool] = Field(None, description="Enable in-app notifications")

    @field_validator('email_enabled', 'push_enabled', 'in_app_enabled')
    @classmethod
    def validate_boolean_fields(cls, v):
        """Validate boolean fields."""
        if v is not None:
            return bool(v)
        return v


class NotificationPreferenceResponse(BaseModel):
    """Notification preference response model."""
    id: UUID4
    user_id: UUID4
    notification_type: str
    email_enabled: bool
    push_enabled: bool
    in_app_enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationPreferenceListResponse(BaseModel):
    """Notification preference list response model."""
    success: bool
    data: List[NotificationPreferenceResponse]
    message: str


class NotificationPreferenceCreateResponseWrapper(BaseModel):
    """Notification preference creation response wrapper."""
    success: bool
    data: NotificationPreferenceResponse
    message: str


class NotificationPreferenceUpdateResponseWrapper(BaseModel):
    """Notification preference update response wrapper."""
    success: bool
    data: NotificationPreferenceResponse
    message: str


class NotificationPreferenceDeleteResponseWrapper(BaseModel):
    """Notification preference deletion response wrapper."""
    success: bool
    message: str


class NotificationPreferenceBulkUpdateRequest(BaseModel):
    """Notification preference bulk update request model."""
    preferences: List[NotificationPreferenceCreateRequest] = Field(..., description="List of notification preferences")

    @field_validator('preferences')
    @classmethod
    def validate_preferences(cls, v):
        """Validate preferences list."""
        if not v:
            raise ValueError("Preferences list cannot be empty")
        if len(v) > 20:
            raise ValueError("Cannot update more than 20 preferences at once")
        
        # Check for duplicate notification types
        types = [pref.notification_type for pref in v]
        if len(types) != len(set(types)):
            raise ValueError("Duplicate notification types are not allowed")
        
        return v


class NotificationPreferenceBulkUpdateResponseWrapper(BaseModel):
    """Notification preference bulk update response wrapper."""
    success: bool
    data: List[NotificationPreferenceResponse]
    message: str
    updated_count: int


class NotificationPreferenceStatsResponse(BaseModel):
    """Notification preference statistics response model."""
    success: bool
    data: Dict[str, Any]
    message: str 