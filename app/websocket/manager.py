"""
WebSocket connection manager for real-time notifications.
"""
import json
import asyncio
from typing import Dict, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time notifications."""
    
    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> set of connection_ids
        self.connection_users: Dict[str, str] = {}  # connection_id -> user_id
    
    async def connect(self, websocket: WebSocket, user_id: str) -> str:
        """
        Connect a new WebSocket client.
        
        Args:
            websocket: WebSocket connection
            user_id: ID of the connected user
            
        Returns:
            Connection ID
        """
        await websocket.accept()
        
        # Generate unique connection ID
        connection_id = f"{user_id}_{datetime.now(timezone.utc).timestamp()}"
        
        # Store connection
        self.active_connections[connection_id] = websocket
        self.connection_users[connection_id] = user_id
        
        # Add to user's connections
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)
        
        logger.info(f"WebSocket connected: {connection_id} for user {user_id}")
        
        # Send connection confirmation
        await self.send_personal_message(
            connection_id,
            {
                "type": "connection_established",
                "connection_id": connection_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
        return connection_id
    
    def disconnect(self, connection_id: str) -> None:
        """
        Disconnect a WebSocket client.
        
        Args:
            connection_id: ID of the connection to disconnect
        """
        if connection_id in self.active_connections:
            user_id = self.connection_users.get(connection_id)
            
            # Remove from active connections
            del self.active_connections[connection_id]
            
            # Remove from user's connections
            if user_id and user_id in self.user_connections:
                self.user_connections[user_id].discard(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            # Remove from connection users mapping
            if connection_id in self.connection_users:
                del self.connection_users[connection_id]
            
            logger.info(f"WebSocket disconnected: {connection_id} for user {user_id}")
    
    async def send_personal_message(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """
        Send a message to a specific connection.
        
        Args:
            connection_id: ID of the target connection
            message: Message to send
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        if connection_id not in self.active_connections:
            return False
        
        try:
            websocket = self.active_connections[connection_id]
            await websocket.send_text(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Failed to send message to {connection_id}: {e}")
            # Remove the connection if it's broken
            self.disconnect(connection_id)
            return False
    
    async def send_personal_notification(self, user_id: str, notification: Dict[str, Any]) -> bool:
        """
        Send a notification to all connections of a specific user.
        
        Args:
            user_id: ID of the target user
            notification: Notification data to send
            
        Returns:
            True if message was sent to at least one connection, False otherwise
        """
        if user_id not in self.user_connections:
            return False
        
        message = {
            "type": "notification",
            "data": notification,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        success = False
        connections_to_remove = []
        
        for connection_id in self.user_connections[user_id]:
            if await self.send_personal_message(connection_id, message):
                success = True
            else:
                connections_to_remove.append(connection_id)
        
        # Clean up broken connections
        for connection_id in connections_to_remove:
            self.disconnect(connection_id)
        
        return success
    
    async def broadcast(self, message: Dict[str, Any]) -> int:
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: Message to broadcast
            
        Returns:
            Number of connections that received the message
        """
        message["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        connections_to_remove = []
        success_count = 0
        
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to broadcast to {connection_id}: {e}")
                connections_to_remove.append(connection_id)
        
        # Clean up broken connections
        for connection_id in connections_to_remove:
            self.disconnect(connection_id)
        
        return success_count
    
    async def broadcast_to_users(self, user_ids: Set[str], message: Dict[str, Any]) -> int:
        """
        Broadcast a message to specific users.
        
        Args:
            user_ids: Set of user IDs to send the message to
            message: Message to broadcast
            
        Returns:
            Number of users that received the message
        """
        success_count = 0
        
        for user_id in user_ids:
            if await self.send_personal_notification(user_id, message):
                success_count += 1
        
        return success_count
    
    def get_connection_count(self) -> int:
        """
        Get the total number of active connections.
        
        Returns:
            Number of active connections
        """
        return len(self.active_connections)
    
    def get_user_connection_count(self, user_id: str) -> int:
        """
        Get the number of active connections for a specific user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Number of active connections for the user
        """
        if user_id not in self.user_connections:
            return 0
        return len(self.user_connections[user_id])
    
    def get_connected_users(self) -> Set[str]:
        """
        Get the set of currently connected user IDs.
        
        Returns:
            Set of connected user IDs
        """
        return set(self.user_connections.keys())
    
    def is_user_connected(self, user_id: str) -> bool:
        """
        Check if a user has any active connections.
        
        Args:
            user_id: ID of the user to check
            
        Returns:
            True if user has active connections, False otherwise
        """
        return user_id in self.user_connections and len(self.user_connections[user_id]) > 0


# Global connection manager instance
manager = ConnectionManager() 