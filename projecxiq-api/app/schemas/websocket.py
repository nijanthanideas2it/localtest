"""
WebSocket message schemas for real-time notifications.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator
from pydantic.types import UUID4


class WebSocketMessage(BaseModel):
    """Base WebSocket message model."""
    type: str = Field(..., description="Type of WebSocket message")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(), description="Message timestamp")
    data: Optional[Dict[str, Any]] = Field(None, description="Message data")


class WebSocketNotificationMessage(BaseModel):
    """WebSocket notification message model."""
    type: str = Field("notification", description="Message type")
    data: Dict[str, Any] = Field(..., description="Notification data")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(), description="Message timestamp")


class WebSocketConnectionMessage(BaseModel):
    """WebSocket connection message model."""
    type: str = Field("connection_established", description="Message type")
    connection_id: str = Field(..., description="Connection ID")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(), description="Message timestamp")


class WebSocketHeartbeatMessage(BaseModel):
    """WebSocket heartbeat message model."""
    type: str = Field("heartbeat", description="Message type")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(), description="Message timestamp")


class WebSocketErrorMessage(BaseModel):
    """WebSocket error message model."""
    type: str = Field("error", description="Message type")
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(), description="Message timestamp")


class WebSocketStatusMessage(BaseModel):
    """WebSocket status message model."""
    type: str = Field("status", description="Message type")
    status: str = Field(..., description="Status message")
    connection_count: Optional[int] = Field(None, description="Number of active connections")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(), description="Message timestamp")


class WebSocketClientMessage(BaseModel):
    """WebSocket client message model."""
    type: str = Field(..., description="Type of client message")
    data: Optional[Dict[str, Any]] = Field(None, description="Message data")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(), description="Message timestamp")

    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        """Validate message type."""
        if not v or not v.strip():
            raise ValueError("Message type cannot be empty")
        allowed_types = [
            'heartbeat', 'subscribe', 'unsubscribe', 'ping', 'pong',
            'notification_request', 'status_request'
        ]
        if v not in allowed_types:
            raise ValueError(f"Message type '{v}' is not allowed")
        return v.strip()


class WebSocketSubscribeMessage(BaseModel):
    """WebSocket subscribe message model."""
    type: str = Field("subscribe", description="Message type")
    channels: List[str] = Field(..., description="Channels to subscribe to")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(), description="Message timestamp")

    @field_validator('channels')
    @classmethod
    def validate_channels(cls, v):
        """Validate channels."""
        if not v:
            raise ValueError("Channels list cannot be empty")
        if len(v) > 10:
            raise ValueError("Cannot subscribe to more than 10 channels at once")
        
        allowed_channels = [
            'notifications', 'tasks', 'projects', 'time_entries',
            'comments', 'milestones', 'system_alerts'
        ]
        
        for channel in v:
            if channel not in allowed_channels:
                raise ValueError(f"Channel '{channel}' is not allowed")
        
        return v


class WebSocketUnsubscribeMessage(BaseModel):
    """WebSocket unsubscribe message model."""
    type: str = Field("unsubscribe", description="Message type")
    channels: List[str] = Field(..., description="Channels to unsubscribe from")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(), description="Message timestamp")

    @field_validator('channels')
    @classmethod
    def validate_channels(cls, v):
        """Validate channels."""
        if not v:
            raise ValueError("Channels list cannot be empty")
        if len(v) > 10:
            raise ValueError("Cannot unsubscribe from more than 10 channels at once")
        
        allowed_channels = [
            'notifications', 'tasks', 'projects', 'time_entries',
            'comments', 'milestones', 'system_alerts'
        ]
        
        for channel in v:
            if channel not in allowed_channels:
                raise ValueError(f"Channel '{channel}' is not allowed")
        
        return v


class WebSocketNotificationRequest(BaseModel):
    """WebSocket notification request model."""
    type: str = Field("notification_request", description="Message type")
    notification_id: Optional[str] = Field(None, description="Specific notification ID")
    limit: Optional[int] = Field(20, ge=1, le=100, description="Number of notifications to retrieve")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(), description="Message timestamp")


class WebSocketStatusRequest(BaseModel):
    """WebSocket status request model."""
    type: str = Field("status_request", description="Message type")
    include_connection_count: bool = Field(True, description="Include connection count in response")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(), description="Message timestamp")


class WebSocketConnectionInfo(BaseModel):
    """WebSocket connection information model."""
    connection_id: str
    user_id: str
    connected_at: datetime
    last_activity: datetime
    is_active: bool = True


class WebSocketStats(BaseModel):
    """WebSocket statistics model."""
    total_connections: int
    active_connections: int
    connected_users: int
    total_messages_sent: int
    total_messages_received: int
    uptime_seconds: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(), description="Stats timestamp") 