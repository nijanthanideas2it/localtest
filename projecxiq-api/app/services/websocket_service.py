"""
WebSocket service for real-time notifications.
"""
import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from fastapi import WebSocket, WebSocketDisconnect
import logging

from app.websocket.manager import manager
from app.services.notification_service import NotificationService
from app.services.notification_preference_service import NotificationPreferenceService
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

logger = logging.getLogger(__name__)


class WebSocketService:
    """Service class for WebSocket operations and real-time notifications."""
    
    def __init__(self):
        """Initialize the WebSocket service."""
        self.user_subscriptions: Dict[str, set] = {}  # user_id -> set of subscribed channels
        self.channel_subscribers: Dict[str, set] = {}  # channel -> set of user_ids
        self.connection_subscriptions: Dict[str, set] = {}  # connection_id -> set of subscribed channels
    
    async def handle_websocket_connection(
        self,
        websocket: WebSocket,
        user_id: str
    ) -> None:
        """
        Handle a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            user_id: ID of the connected user
        """
        connection_id = await manager.connect(websocket, user_id)
        
        try:
            # Initialize user subscriptions
            if user_id not in self.user_subscriptions:
                self.user_subscriptions[user_id] = set()
            if connection_id not in self.connection_subscriptions:
                self.connection_subscriptions[connection_id] = set()
            
            # Subscribe to default notifications channel
            await self.subscribe_user_to_channel(user_id, "notifications")
            
            # Handle incoming messages
            while True:
                try:
                    # Receive message from client
                    data = await websocket.receive_text()
                    await self.handle_client_message(connection_id, user_id, data)
                    
                except WebSocketDisconnect:
                    logger.info(f"WebSocket disconnected: {connection_id}")
                    break
                except Exception as e:
                    logger.error(f"Error handling WebSocket message: {e}")
                    await self.send_error_message(connection_id, str(e))
                    
        except Exception as e:
            logger.error(f"Error in WebSocket connection: {e}")
        finally:
            # Clean up on disconnect
            await self.handle_disconnect(connection_id, user_id)
    
    async def handle_client_message(
        self,
        connection_id: str,
        user_id: str,
        message_data: str
    ) -> None:
        """
        Handle incoming client message.
        
        Args:
            connection_id: ID of the connection
            user_id: ID of the user
            message_data: Raw message data
        """
        try:
            # Parse message
            data = json.loads(message_data)
            message_type = data.get("type")
            
            if message_type == "heartbeat":
                await self.handle_heartbeat(connection_id)
            elif message_type == "subscribe":
                await self.handle_subscribe(connection_id, user_id, data)
            elif message_type == "unsubscribe":
                await self.handle_unsubscribe(connection_id, user_id, data)
            elif message_type == "notification_request":
                await self.handle_notification_request(connection_id, user_id, data)
            elif message_type == "status_request":
                await self.handle_status_request(connection_id, user_id, data)
            elif message_type == "ping":
                await self.handle_ping(connection_id)
            else:
                await self.send_error_message(connection_id, f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            await self.send_error_message(connection_id, "Invalid JSON format")
        except Exception as e:
            logger.error(f"Error handling client message: {e}")
            await self.send_error_message(connection_id, str(e))
    
    async def handle_heartbeat(self, connection_id: str) -> None:
        """Handle heartbeat message."""
        await manager.send_personal_message(
            connection_id,
            {
                "type": "heartbeat",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
    async def handle_ping(self, connection_id: str) -> None:
        """Handle ping message."""
        await manager.send_personal_message(
            connection_id,
            {
                "type": "pong",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
    async def handle_subscribe(
        self,
        connection_id: str,
        user_id: str,
        data: Dict[str, Any]
    ) -> None:
        """Handle subscribe message."""
        try:
            subscribe_data = WebSocketSubscribeMessage(**data)
            
            for channel in subscribe_data.channels:
                await self.subscribe_user_to_channel(user_id, channel)
                self.connection_subscriptions[connection_id].add(channel)
            
            await manager.send_personal_message(
                connection_id,
                {
                    "type": "subscribed",
                    "channels": subscribe_data.channels,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
        except Exception as e:
            await self.send_error_message(connection_id, f"Subscribe error: {str(e)}")
    
    async def handle_unsubscribe(
        self,
        connection_id: str,
        user_id: str,
        data: Dict[str, Any]
    ) -> None:
        """Handle unsubscribe message."""
        try:
            unsubscribe_data = WebSocketUnsubscribeMessage(**data)
            
            for channel in unsubscribe_data.channels:
                await self.unsubscribe_user_from_channel(user_id, channel)
                self.connection_subscriptions[connection_id].discard(channel)
            
            await manager.send_personal_message(
                connection_id,
                {
                    "type": "unsubscribed",
                    "channels": unsubscribe_data.channels,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
        except Exception as e:
            await self.send_error_message(connection_id, f"Unsubscribe error: {str(e)}")
    
    async def handle_notification_request(
        self,
        connection_id: str,
        user_id: str,
        data: Dict[str, Any]
    ) -> None:
        """Handle notification request message."""
        try:
            request_data = WebSocketNotificationRequest(**data)
            
            # Get recent notifications for the user
            notifications, _ = NotificationService.get_notifications(
                None,  # We'll need to pass a mock session or handle this differently
                user_id,
                limit=request_data.limit or 20
            )
            
            # Convert to response format
            notification_data = []
            for notification in notifications:
                notification_data.append({
                    "id": str(notification.id),
                    "type": notification.type,
                    "title": notification.title,
                    "message": notification.message,
                    "is_read": notification.is_read,
                    "created_at": notification.created_at.isoformat()
                })
            
            await manager.send_personal_message(
                connection_id,
                {
                    "type": "notifications",
                    "data": notification_data,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
        except Exception as e:
            await self.send_error_message(connection_id, f"Notification request error: {str(e)}")
    
    async def handle_status_request(
        self,
        connection_id: str,
        user_id: str,
        data: Dict[str, Any]
    ) -> None:
        """Handle status request message."""
        try:
            request_data = WebSocketStatusRequest(**data)
            
            status_data = {
                "status": "connected",
                "user_id": user_id,
                "connection_id": connection_id,
                "subscribed_channels": list(self.connection_subscriptions.get(connection_id, set()))
            }
            
            if request_data.include_connection_count:
                status_data["connection_count"] = manager.get_connection_count()
                status_data["user_connection_count"] = manager.get_user_connection_count(user_id)
            
            await manager.send_personal_message(
                connection_id,
                {
                    "type": "status",
                    "data": status_data,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
        except Exception as e:
            await self.send_error_message(connection_id, f"Status request error: {str(e)}")
    
    async def subscribe_user_to_channel(self, user_id: str, channel: str) -> None:
        """
        Subscribe a user to a channel.
        
        Args:
            user_id: ID of the user
            channel: Channel name
        """
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = set()
        
        self.user_subscriptions[user_id].add(channel)
        
        if channel not in self.channel_subscribers:
            self.channel_subscribers[channel] = set()
        
        self.channel_subscribers[channel].add(user_id)
        
        logger.info(f"User {user_id} subscribed to channel {channel}")
    
    async def unsubscribe_user_from_channel(self, user_id: str, channel: str) -> None:
        """
        Unsubscribe a user from a channel.
        
        Args:
            user_id: ID of the user
            channel: Channel name
        """
        if user_id in self.user_subscriptions:
            self.user_subscriptions[user_id].discard(channel)
        
        if channel in self.channel_subscribers:
            self.channel_subscribers[channel].discard(user_id)
            
            # Clean up empty channel
            if not self.channel_subscribers[channel]:
                del self.channel_subscribers[channel]
        
        logger.info(f"User {user_id} unsubscribed from channel {channel}")
    
    async def broadcast_to_channel(
        self,
        channel: str,
        message: Dict[str, Any],
        exclude_user: Optional[str] = None
    ) -> int:
        """
        Broadcast a message to all subscribers of a channel.
        
        Args:
            channel: Channel name
            message: Message to broadcast
            exclude_user: User ID to exclude from broadcast
            
        Returns:
            Number of users that received the message
        """
        if channel not in self.channel_subscribers:
            return 0
        
        subscribers = self.channel_subscribers[channel].copy()
        if exclude_user:
            subscribers.discard(exclude_user)
        
        success_count = 0
        for user_id in subscribers:
            if await manager.send_personal_notification(user_id, message):
                success_count += 1
        
        return success_count
    
    async def send_notification_to_user(
        self,
        user_id: str,
        notification: Dict[str, Any]
    ) -> bool:
        """
        Send a notification to a specific user via WebSocket.
        
        Args:
            user_id: ID of the target user
            notification: Notification data
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        # Check if user has notification preferences
        # For now, we'll send to all connected instances of the user
        return await manager.send_personal_notification(user_id, notification)
    
    async def send_error_message(self, connection_id: str, error_message: str) -> None:
        """
        Send an error message to a specific connection.
        
        Args:
            connection_id: ID of the connection
            error_message: Error message
        """
        await manager.send_personal_message(
            connection_id,
            {
                "type": "error",
                "error": error_message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
    async def handle_disconnect(self, connection_id: str, user_id: str) -> None:
        """
        Handle WebSocket disconnection.
        
        Args:
            connection_id: ID of the connection
            user_id: ID of the user
        """
        # Remove connection from manager
        manager.disconnect(connection_id)
        
        # Clean up subscriptions
        if connection_id in self.connection_subscriptions:
            for channel in self.connection_subscriptions[connection_id]:
                await self.unsubscribe_user_from_channel(user_id, channel)
            del self.connection_subscriptions[connection_id]
        
        logger.info(f"WebSocket connection {connection_id} cleaned up")
    
    def get_channel_subscribers(self, channel: str) -> set:
        """
        Get all subscribers of a channel.
        
        Args:
            channel: Channel name
            
        Returns:
            Set of user IDs subscribed to the channel
        """
        return self.channel_subscribers.get(channel, set()).copy()
    
    def get_user_subscriptions(self, user_id: str) -> set:
        """
        Get all channels a user is subscribed to.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Set of channel names the user is subscribed to
        """
        return self.user_subscriptions.get(user_id, set()).copy()
    
    def get_websocket_stats(self) -> Dict[str, Any]:
        """
        Get WebSocket statistics.
        
        Returns:
            Dictionary with WebSocket statistics
        """
        return {
            "total_connections": manager.get_connection_count(),
            "connected_users": len(manager.get_connected_users()),
            "total_channels": len(self.channel_subscribers),
            "total_subscriptions": sum(len(subscribers) for subscribers in self.channel_subscribers.values()),
            "channel_subscribers": {
                channel: len(subscribers) 
                for channel, subscribers in self.channel_subscribers.items()
            }
        }


# Global WebSocket service instance
websocket_service = WebSocketService() 