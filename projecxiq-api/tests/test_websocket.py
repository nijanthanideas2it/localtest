"""
Tests for WebSocket functionality.
"""
import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone
from uuid import uuid4

# pytestmark = pytest.mark.asyncio  # Removed global marker

from app.websocket.manager import ConnectionManager, manager
from app.services.websocket_service import WebSocketService, websocket_service
from app.schemas.websocket import (
    WebSocketClientMessage,
    WebSocketSubscribeMessage,
    WebSocketUnsubscribeMessage,
    WebSocketNotificationRequest,
    WebSocketStatusRequest,
    WebSocketErrorMessage,
    WebSocketStatusMessage,
    WebSocketNotificationMessage
)
from app.models.user import User
from pydantic import ValidationError


class TestWebSocketManager:
    """Test cases for WebSocket connection manager."""
    
    @pytest.fixture
    def connection_manager(self):
        """Create a fresh connection manager for testing."""
        return ConnectionManager()
    
    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket connection."""
        websocket = MagicMock()
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        websocket.close = AsyncMock()
        return websocket
    
    @pytest.fixture
    def sample_user(self):
        """Sample user for testing."""
        user = User(
            id=uuid4(),
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password_hash="hashed_password",
            role="Developer",
            is_active=True
        )
        return user
    
    @pytest.mark.asyncio
    async def test_connect_success(self, connection_manager, mock_websocket, sample_user):
        """Test successful WebSocket connection."""
        user_id = str(sample_user.id)
        
        connection_id = await connection_manager.connect(mock_websocket, user_id)
        
        assert connection_id is not None
        assert connection_id in connection_manager.active_connections
        assert connection_manager.active_connections[connection_id] == mock_websocket
        assert connection_manager.connection_users[connection_id] == user_id
        assert user_id in connection_manager.user_connections
        assert connection_id in connection_manager.user_connections[user_id]
        
        # Verify connection confirmation was sent
        mock_websocket.send_text.assert_called_once()
        call_args = mock_websocket.send_text.call_args[0][0]
        message = json.loads(call_args)
        assert message["type"] == "connection_established"
        assert message["connection_id"] == connection_id
    
    def test_disconnect_success(self, connection_manager, mock_websocket, sample_user):
        """Test successful WebSocket disconnection."""
        user_id = str(sample_user.id)
        
        # First connect
        connection_id = "test_connection_id"
        connection_manager.active_connections[connection_id] = mock_websocket
        connection_manager.connection_users[connection_id] = user_id
        connection_manager.user_connections[user_id] = {connection_id}
        
        # Then disconnect
        connection_manager.disconnect(connection_id)
        
        assert connection_id not in connection_manager.active_connections
        assert connection_id not in connection_manager.connection_users
        assert user_id not in connection_manager.user_connections
    
    @pytest.mark.asyncio
    async def test_send_personal_message_success(self, connection_manager, mock_websocket, sample_user):
        """Test successful personal message sending."""
        user_id = str(sample_user.id)
        connection_id = await connection_manager.connect(mock_websocket, user_id)
        
        message = {"type": "test", "data": "test_message"}
        result = await connection_manager.send_personal_message(connection_id, message)
        
        assert result is True
        mock_websocket.send_text.assert_called()
        
        # Verify the message was sent
        call_args = mock_websocket.send_text.call_args_list[-1][0][0]
        sent_message = json.loads(call_args)
        assert sent_message["type"] == "test"
        assert sent_message["data"] == "test_message"
    
    @pytest.mark.asyncio
    async def test_send_personal_message_connection_not_found(self, connection_manager):
        """Test sending personal message to non-existent connection."""
        result = await connection_manager.send_personal_message("non_existent", {"type": "test"})
        assert result is False
    
    @pytest.mark.asyncio
    async def test_send_personal_notification_success(self, connection_manager, mock_websocket, sample_user):
        """Test successful personal notification sending."""
        user_id = str(sample_user.id)
        connection_id = await connection_manager.connect(mock_websocket, user_id)
        
        notification = {"id": "123", "title": "Test Notification", "message": "Test message"}
        result = await connection_manager.send_personal_notification(user_id, notification)
        
        assert result is True
        mock_websocket.send_text.assert_called()
        
        # Verify the notification was sent
        call_args = mock_websocket.send_text.call_args_list[-1][0][0]
        sent_message = json.loads(call_args)
        assert sent_message["type"] == "notification"
        assert sent_message["data"] == notification
    
    @pytest.mark.asyncio
    async def test_send_personal_notification_user_not_connected(self, connection_manager):
        """Test sending notification to non-connected user."""
        result = await connection_manager.send_personal_notification("non_existent", {"type": "test"})
        assert result is False
    
    @pytest.mark.asyncio
    async def test_broadcast_success(self, connection_manager, mock_websocket, sample_user):
        """Test successful broadcast to all connections."""
        user_id = str(sample_user.id)
        await connection_manager.connect(mock_websocket, user_id)
        
        message = {"type": "broadcast", "data": "broadcast_message"}
        result = await connection_manager.broadcast(message)
        
        assert result == 1  # One connection received the message
        mock_websocket.send_text.assert_called()
        
        # Verify the broadcast message was sent
        call_args = mock_websocket.send_text.call_args_list[-1][0][0]
        sent_message = json.loads(call_args)
        assert sent_message["type"] == "broadcast"
        assert sent_message["data"] == "broadcast_message"
        assert "timestamp" in sent_message
    
    @pytest.mark.asyncio
    async def test_broadcast_to_users_success(self, connection_manager, mock_websocket, sample_user):
        """Test successful broadcast to specific users."""
        user_id = str(sample_user.id)
        await connection_manager.connect(mock_websocket, user_id)
        
        message = {"type": "user_broadcast", "data": "user_message"}
        result = await connection_manager.broadcast_to_users({user_id}, message)
        
        assert result == 1  # One user received the message
        mock_websocket.send_text.assert_called()
    
    def test_get_connection_count(self, connection_manager, mock_websocket, sample_user):
        """Test getting connection count."""
        user_id = str(sample_user.id)
        connection_id = "test_connection"
        connection_manager.active_connections[connection_id] = mock_websocket
        
        count = connection_manager.get_connection_count()
        assert count == 1
    
    def test_get_user_connection_count(self, connection_manager, mock_websocket, sample_user):
        """Test getting user connection count."""
        user_id = str(sample_user.id)
        connection_manager.user_connections[user_id] = {"conn1", "conn2"}
        
        count = connection_manager.get_user_connection_count(user_id)
        assert count == 2
    
    def test_get_connected_users(self, connection_manager):
        """Test getting connected users."""
        connection_manager.user_connections = {"user1": {"conn1"}, "user2": {"conn2"}}
        
        users = connection_manager.get_connected_users()
        assert users == {"user1", "user2"}
    
    def test_is_user_connected(self, connection_manager):
        """Test checking if user is connected."""
        user_id = "test_user"
        connection_manager.user_connections[user_id] = {"conn1"}
        
        assert connection_manager.is_user_connected(user_id) is True
        assert connection_manager.is_user_connected("non_existent") is False


class TestWebSocketService:
    """Test cases for WebSocket service."""
    
    @pytest.fixture
    def websocket_service_instance(self):
        """Create a fresh WebSocket service instance for testing."""
        return WebSocketService()
    
    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket connection."""
        websocket = MagicMock()
        websocket.send_text = AsyncMock()
        websocket.receive_text = AsyncMock()
        websocket.close = AsyncMock()
        return websocket
    
    @pytest.fixture
    def sample_user(self):
        """Sample user for testing."""
        user = User(
            id=uuid4(),
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password_hash="hashed_password",
            role="Developer",
            is_active=True
        )
        return user
    
    @pytest.mark.asyncio
    async def test_subscribe_user_to_channel(self, websocket_service_instance, sample_user):
        """Test subscribing user to channel."""
        user_id = str(sample_user.id)
        channel = "notifications"
        
        await websocket_service_instance.subscribe_user_to_channel(user_id, channel)
        
        assert user_id in websocket_service_instance.user_subscriptions
        assert channel in websocket_service_instance.user_subscriptions[user_id]
        assert channel in websocket_service_instance.channel_subscribers
        assert user_id in websocket_service_instance.channel_subscribers[channel]
    
    @pytest.mark.asyncio
    async def test_unsubscribe_user_from_channel(self, websocket_service_instance, sample_user):
        """Test unsubscribing user from channel."""
        user_id = str(sample_user.id)
        channel = "notifications"
        
        # First subscribe
        await websocket_service_instance.subscribe_user_to_channel(user_id, channel)
        
        # Then unsubscribe
        await websocket_service_instance.unsubscribe_user_from_channel(user_id, channel)
        
        assert channel not in websocket_service_instance.user_subscriptions[user_id]
        # Check that the channel is removed from subscribers if no users are left
        if channel in websocket_service_instance.channel_subscribers:
            assert user_id not in websocket_service_instance.channel_subscribers[channel]
    
    @pytest.mark.asyncio
    async def test_broadcast_to_channel_success(self, websocket_service_instance, sample_user):
        """Test broadcasting to channel."""
        user_id = str(sample_user.id)
        channel = "notifications"
        
        # Subscribe user to channel
        await websocket_service_instance.subscribe_user_to_channel(user_id, channel)
        
        # Mock the manager's send_personal_notification method
        with patch.object(manager, 'send_personal_notification', return_value=True):
            message = {"type": "test", "data": "test_message"}
            result = await websocket_service_instance.broadcast_to_channel(channel, message)
            
            assert result == 1  # One user received the message
    
    @pytest.mark.asyncio
    async def test_broadcast_to_channel_exclude_user(self, websocket_service_instance, sample_user):
        """Test broadcasting to channel with excluded user."""
        user_id = str(sample_user.id)
        channel = "notifications"
        
        # Subscribe user to channel
        await websocket_service_instance.subscribe_user_to_channel(user_id, channel)
        
        # Mock the manager's send_personal_notification method
        with patch.object(manager, 'send_personal_notification', return_value=True):
            message = {"type": "test", "data": "test_message"}
            result = await websocket_service_instance.broadcast_to_channel(channel, message, exclude_user=user_id)
            
            assert result == 0  # No users received the message (excluded)
    
    @pytest.mark.asyncio
    async def test_send_notification_to_user_success(self, websocket_service_instance, sample_user):
        """Test sending notification to user."""
        user_id = str(sample_user.id)
        
        # Mock the manager's send_personal_notification method
        with patch.object(manager, 'send_personal_notification', return_value=True):
            notification = {"id": "123", "title": "Test", "message": "Test message"}
            result = await websocket_service_instance.send_notification_to_user(user_id, notification)
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_send_notification_to_user_failure(self, websocket_service_instance, sample_user):
        """Test sending notification to user when it fails."""
        user_id = str(sample_user.id)
        
        # Mock the manager's send_personal_notification method
        with patch.object(manager, 'send_personal_notification', return_value=False):
            notification = {"id": "123", "title": "Test", "message": "Test message"}
            result = await websocket_service_instance.send_notification_to_user(user_id, notification)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_send_error_message(self, websocket_service_instance, sample_user):
        """Test sending error message."""
        user_id = str(sample_user.id)
        connection_id = "test_connection"
        
        # Mock the manager's send_personal_message method
        with patch.object(manager, 'send_personal_message', return_value=True):
            error_message = "Test error"
            await websocket_service_instance.send_error_message(connection_id, error_message)
            
            manager.send_personal_message.assert_called_once()
            call_args = manager.send_personal_message.call_args
            assert call_args[0][0] == connection_id
            assert call_args[0][1]["type"] == "error"
            assert call_args[0][1]["error"] == error_message
    
    def test_get_channel_subscribers(self, websocket_service_instance, sample_user):
        """Test getting channel subscribers."""
        user_id = str(sample_user.id)
        channel = "notifications"
        
        # Add subscription
        websocket_service_instance.channel_subscribers[channel] = {user_id}
        
        subscribers = websocket_service_instance.get_channel_subscribers(channel)
        assert subscribers == {user_id}
    
    def test_get_user_subscriptions(self, websocket_service_instance, sample_user):
        """Test getting user subscriptions."""
        user_id = str(sample_user.id)
        channel = "notifications"
        
        # Add subscription
        websocket_service_instance.user_subscriptions[user_id] = {channel}
        
        subscriptions = websocket_service_instance.get_user_subscriptions(user_id)
        assert subscriptions == {channel}
    
    def test_get_websocket_stats(self, websocket_service_instance):
        """Test getting WebSocket statistics."""
        # Mock manager methods
        with patch.object(manager, 'get_connection_count', return_value=5):
            with patch.object(manager, 'get_connected_users', return_value={"user1", "user2"}):
                # Add some channel data
                websocket_service_instance.channel_subscribers = {
                    "notifications": {"user1", "user2"},
                    "tasks": {"user1"}
                }
                
                stats = websocket_service_instance.get_websocket_stats()
                
                assert stats["total_connections"] == 5
                assert stats["connected_users"] == 2
                assert stats["total_channels"] == 2
                assert stats["total_subscriptions"] == 3


class TestWebSocketValidation:
    """Test cases for WebSocket message validation."""
    
    def test_websocket_client_message_valid(self):
        """Test valid WebSocket client message."""
        data = {
            "type": "heartbeat",
            "data": {"test": "data"},
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        message = WebSocketClientMessage(**data)
        assert message.type == "heartbeat"
        assert message.data == {"test": "data"}
    
    def test_websocket_client_message_invalid_type(self):
        """Test WebSocket client message with invalid type."""
        data = {
            "type": "invalid_type",
            "data": {"test": "data"}
        }
        
        with pytest.raises(ValidationError, match="Message type 'invalid_type' is not allowed"):
            WebSocketClientMessage(**data)
    
    def test_websocket_subscribe_message_valid(self):
        """Test valid WebSocket subscribe message."""
        data = {
            "type": "subscribe",
            "channels": ["notifications", "tasks"],
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        message = WebSocketSubscribeMessage(**data)
        assert message.type == "subscribe"
        assert message.channels == ["notifications", "tasks"]
    
    def test_websocket_subscribe_message_invalid_channel(self):
        """Test WebSocket subscribe message with invalid channel."""
        data = {
            "type": "subscribe",
            "channels": ["invalid_channel"]
        }
        
        with pytest.raises(ValidationError, match="Channel 'invalid_channel' is not allowed"):
            WebSocketSubscribeMessage(**data)
    
    def test_websocket_subscribe_message_too_many_channels(self):
        """Test WebSocket subscribe message with too many channels."""
        data = {
            "type": "subscribe",
            "channels": ["notifications"] * 11  # More than 10
        }
        
        with pytest.raises(ValidationError, match="Cannot subscribe to more than 10 channels at once"):
            WebSocketSubscribeMessage(**data)
    
    def test_websocket_unsubscribe_message_valid(self):
        """Test valid WebSocket unsubscribe message."""
        data = {
            "type": "unsubscribe",
            "channels": ["notifications"],
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        message = WebSocketUnsubscribeMessage(**data)
        assert message.type == "unsubscribe"
        assert message.channels == ["notifications"]
    
    def test_websocket_notification_request_valid(self):
        """Test valid WebSocket notification request."""
        data = {
            "type": "notification_request",
            "notification_id": "123",
            "limit": 10,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        message = WebSocketNotificationRequest(**data)
        assert message.type == "notification_request"
        assert message.notification_id == "123"
        assert message.limit == 10
    
    def test_websocket_status_request_valid(self):
        """Test valid WebSocket status request."""
        data = {
            "type": "status_request",
            "include_connection_count": True,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        message = WebSocketStatusRequest(**data)
        assert message.type == "status_request"
        assert message.include_connection_count is True 