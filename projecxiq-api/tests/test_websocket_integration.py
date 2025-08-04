"""
Integration tests for WebSocket functionality.
"""
import pytest
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from uuid import uuid4

from app.main import app
from app.websocket.manager import manager
from app.services.websocket_service import websocket_service
from app.models.user import User


class TestWebSocketIntegration:
    """Integration tests for WebSocket functionality."""
    
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
    
    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket connection."""
        websocket = MagicMock()
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        websocket.close = AsyncMock()
        websocket.receive_text = AsyncMock()
        websocket.query_params = {}
        return websocket
    
    @pytest.mark.asyncio
    async def test_websocket_connection_flow(self, mock_websocket, sample_user):
        """Test complete WebSocket connection flow."""
        user_id = str(sample_user.id)
        
        # Test connection
        connection_id = await manager.connect(mock_websocket, user_id)
        
        assert connection_id is not None
        assert connection_id in manager.active_connections
        assert manager.is_user_connected(user_id)
        
        # Test sending message
        message = {"type": "test", "data": "test_message"}
        result = await manager.send_personal_message(connection_id, message)
        assert result is True
        
        # Test disconnection
        manager.disconnect(connection_id)
        assert connection_id not in manager.active_connections
        assert not manager.is_user_connected(user_id)
    
    @pytest.mark.asyncio
    async def test_websocket_service_subscription_flow(self, sample_user):
        """Test WebSocket service subscription flow."""
        user_id = str(sample_user.id)
        channel = "notifications"
        
        # Test subscription
        await websocket_service.subscribe_user_to_channel(user_id, channel)
        assert channel in websocket_service.get_user_subscriptions(user_id)
        assert user_id in websocket_service.get_channel_subscribers(channel)
        
        # Test unsubscription
        await websocket_service.unsubscribe_user_from_channel(user_id, channel)
        assert channel not in websocket_service.get_user_subscriptions(user_id)
    
    @pytest.mark.asyncio
    async def test_websocket_broadcast_functionality(self, mock_websocket, sample_user):
        """Test WebSocket broadcast functionality."""
        user_id = str(sample_user.id)
        channel = "notifications"
        
        # Connect user
        connection_id = await manager.connect(mock_websocket, user_id)
        await websocket_service.subscribe_user_to_channel(user_id, channel)
        
        # Test broadcast
        message = {"type": "notification", "data": "test_notification"}
        result = await websocket_service.broadcast_to_channel(channel, message)
        assert result == 1  # One user should receive the message
        
        # Cleanup
        manager.disconnect(connection_id)
        await websocket_service.unsubscribe_user_from_channel(user_id, channel)
    
    @pytest.mark.asyncio
    async def test_websocket_stats(self):
        """Test WebSocket statistics."""
        stats = websocket_service.get_websocket_stats()
        
        assert "total_connections" in stats
        assert "connected_users" in stats
        assert "total_channels" in stats
        assert "total_subscriptions" in stats
        assert "channel_subscribers" in stats
    
    @pytest.mark.asyncio
    async def test_websocket_error_handling(self, mock_websocket):
        """Test WebSocket error handling."""
        # Test sending message to non-existent connection
        result = await manager.send_personal_message("non_existent_id", {"type": "test"})
        assert result is False
        
        # Test sending notification to non-connected user
        result = await websocket_service.send_notification_to_user("non_existent_user", {"type": "test"})
        assert result is False
    
    @pytest.mark.asyncio
    async def test_websocket_message_validation(self):
        """Test WebSocket message validation."""
        from app.schemas.websocket import WebSocketClientMessage, WebSocketSubscribeMessage
        
        # Test valid client message
        valid_message = WebSocketClientMessage(
            type="heartbeat",
            data={"test": "data"}
        )
        assert valid_message.type == "heartbeat"
        
        # Test valid subscribe message
        valid_subscribe = WebSocketSubscribeMessage(
            channels=["notifications", "tasks"]
        )
        assert "notifications" in valid_subscribe.channels
        assert "tasks" in valid_subscribe.channels
        
        # Test invalid message type
        with pytest.raises(ValueError):
            WebSocketClientMessage(type="invalid_type")
        
        # Test invalid channel
        with pytest.raises(ValueError):
            WebSocketSubscribeMessage(channels=["invalid_channel"])
    
    @pytest.mark.asyncio
    async def test_websocket_connection_manager_cleanup(self, mock_websocket, sample_user):
        """Test WebSocket connection manager cleanup."""
        user_id = str(sample_user.id)
        
        # Create multiple connections for the same user
        connection_id1 = await manager.connect(mock_websocket, user_id)
        connection_id2 = await manager.connect(mock_websocket, user_id)
        
        assert manager.get_user_connection_count(user_id) == 2
        
        # Disconnect one connection
        manager.disconnect(connection_id1)
        assert manager.get_user_connection_count(user_id) == 1
        
        # Disconnect the other connection
        manager.disconnect(connection_id2)
        assert manager.get_user_connection_count(user_id) == 0
        assert not manager.is_user_connected(user_id) 