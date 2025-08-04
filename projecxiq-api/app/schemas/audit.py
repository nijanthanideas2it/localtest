"""
Audit log schemas for audit logging functionality.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from uuid import UUID

from app.schemas.user import UserResponse


class AuditLogResponse(BaseModel):
    """Response model for audit log information."""
    id: UUID = Field(..., description="Audit log ID")
    user_id: Optional[UUID] = Field(None, description="User ID who performed the action")
    user: Optional[UserResponse] = Field(None, description="User who performed the action")
    action: str = Field(..., description="Action performed")
    entity_type: Optional[str] = Field(None, description="Type of entity affected")
    entity_id: Optional[UUID] = Field(None, description="ID of entity affected")
    old_values: Optional[Dict[str, Any]] = Field(None, description="Previous values before change")
    new_values: Optional[Dict[str, Any]] = Field(None, description="New values after change")
    ip_address: Optional[str] = Field(None, description="IP address of the user")
    user_agent: Optional[str] = Field(None, description="User agent string")
    created_at: datetime = Field(..., description="Timestamp when the action occurred")

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Response model for audit log list."""
    logs: List[AuditLogResponse] = Field(..., description="List of audit logs")
    total_count: int = Field(..., description="Total number of audit logs")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")


class AuditLogFilterRequest(BaseModel):
    """Request model for audit log filtering."""
    user_id: Optional[UUID] = Field(None, description="Filter by user ID")
    action: Optional[str] = Field(None, description="Filter by action type")
    entity_type: Optional[str] = Field(None, description="Filter by entity type")
    entity_id: Optional[UUID] = Field(None, description="Filter by entity ID")
    ip_address: Optional[str] = Field(None, description="Filter by IP address")
    date_from: Optional[datetime] = Field(None, description="Filter by date from")
    date_to: Optional[datetime] = Field(None, description="Filter by date to")
    search: Optional[str] = Field(None, description="Search in action descriptions")

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

    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        """Validate action length."""
        if v and len(v) > 100:
            raise ValueError("Action cannot exceed 100 characters")
        return v

    @field_validator('entity_type')
    @classmethod
    def validate_entity_type(cls, v):
        """Validate entity type length."""
        if v and len(v) > 50:
            raise ValueError("Entity type cannot exceed 50 characters")
        return v


class AuditLogStatsResponse(BaseModel):
    """Response model for audit log statistics."""
    total_logs: int = Field(..., description="Total number of audit logs")
    logs_by_action: Dict[str, int] = Field(..., description="Logs grouped by action")
    logs_by_user: Dict[str, int] = Field(..., description="Logs grouped by user")
    logs_by_entity_type: Dict[str, int] = Field(..., description="Logs grouped by entity type")
    logs_by_date: Dict[str, int] = Field(..., description="Logs grouped by date")
    recent_activity: List[AuditLogResponse] = Field(..., description="Recent audit logs")
    top_actions: List[Dict[str, Any]] = Field(..., description="Most common actions")
    top_users: List[Dict[str, Any]] = Field(..., description="Most active users")


class AuditLogExportRequest(BaseModel):
    """Request model for audit log export."""
    format: str = Field("json", description="Export format (json, csv)")
    filter_request: Optional[AuditLogFilterRequest] = Field(None, description="Filter criteria")
    include_details: bool = Field(True, description="Whether to include detailed information")

    @field_validator('format')
    @classmethod
    def validate_format(cls, v):
        """Validate export format."""
        if v not in ['json', 'csv']:
            raise ValueError("Format must be 'json' or 'csv'")
        return v


class AuditLogSummaryResponse(BaseModel):
    """Response model for audit log summary."""
    total_logs: int = Field(..., description="Total number of audit logs")
    unique_users: int = Field(..., description="Number of unique users")
    unique_actions: int = Field(..., description="Number of unique actions")
    unique_entities: int = Field(..., description="Number of unique entities")
    date_range: Dict[str, datetime] = Field(..., description="Date range of logs")
    most_common_actions: List[Dict[str, Any]] = Field(..., description="Most common actions")
    most_active_users: List[Dict[str, Any]] = Field(..., description="Most active users")
    recent_trends: Dict[str, Any] = Field(..., description="Recent activity trends")


class AuditLogComparisonResponse(BaseModel):
    """Response model for audit log comparison."""
    period1: Dict[str, Any] = Field(..., description="First period statistics")
    period2: Dict[str, Any] = Field(..., description="Second period statistics")
    changes: Dict[str, Any] = Field(..., description="Changes between periods")
    percentage_changes: Dict[str, float] = Field(..., description="Percentage changes")


class AuditLogAlertRequest(BaseModel):
    """Request model for audit log alerts."""
    alert_type: str = Field(..., description="Type of alert")
    conditions: Dict[str, Any] = Field(..., description="Alert conditions")
    enabled: bool = Field(True, description="Whether the alert is enabled")
    notification_email: Optional[str] = Field(None, description="Email for notifications")

    @field_validator('alert_type')
    @classmethod
    def validate_alert_type(cls, v):
        """Validate alert type."""
        valid_types = ['failed_login', 'suspicious_activity', 'data_export', 'admin_action']
        if v not in valid_types:
            raise ValueError(f"Alert type must be one of: {', '.join(valid_types)}")
        return v

    @field_validator('notification_email')
    @classmethod
    def validate_email(cls, v):
        """Validate email format."""
        if v and '@' not in v:
            raise ValueError("Invalid email format")
        return v 