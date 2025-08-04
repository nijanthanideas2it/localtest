"""
WebSocket API endpoints for real-time notifications.
"""
import json
import logging
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.core.websocket_auth import get_current_user_websocket, authenticate_websocket
from app.services.websocket_service import websocket_service
from app.websocket.manager import manager
from app.schemas.websocket import (
    WebSocketClientMessage,
    WebSocketErrorMessage,
    WebSocketStatusMessage
)

router = APIRouter(tags=["websocket"])
logger = logging.getLogger(__name__)


@router.websocket("/ws/notifications")
async def websocket_notifications_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time notifications.
    
    Handles WebSocket connections for real-time notification delivery.
    """
    try:
        # Authenticate the WebSocket connection
        user_id = await authenticate_websocket(websocket)
        
        # Handle the WebSocket connection
        await websocket_service.handle_websocket_connection(websocket, user_id)
        
    except WebSocketDisconnect:
        # Handle normal disconnection
        logger.info("WebSocket disconnected normally")
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "error": f"Connection error: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }))
        except:
            pass
        finally:
            await websocket.close()


@router.websocket("/ws/notifications/{user_id}")
async def websocket_notifications_user_endpoint(
    websocket: WebSocket,
    user_id: str
):
    """
    WebSocket endpoint for user-specific real-time notifications.
    
    Args:
        websocket: WebSocket connection
        user_id: ID of the user
    """
    try:
        # Authenticate the WebSocket connection
        authenticated_user_id = await authenticate_websocket(websocket)
        
        # Verify the authenticated user matches the requested user_id
        if authenticated_user_id != user_id:
            await websocket.send_text(json.dumps({
                "type": "error",
                "error": "Access denied",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }))
            await websocket.close()
            return
        
        # Handle the WebSocket connection
        await websocket_service.handle_websocket_connection(websocket, user_id)
        
    except WebSocketDisconnect:
        # Handle normal disconnection
        pass
    except Exception as e:
        # Handle unexpected errors
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "error": f"Connection error: {str(e)}",
                "timestamp": "2024-01-01T00:00:00Z"
            }))
        except:
            pass
        finally:
            await websocket.close()


@router.get("/ws/status")
async def websocket_status_endpoint():
    """
    Get WebSocket connection status and statistics.
    
    Returns:
        JSON response with WebSocket statistics
    """
    try:
        stats = websocket_service.get_websocket_stats()
        
        return JSONResponse({
            "success": True,
            "data": stats,
            "message": "WebSocket status retrieved successfully"
        })
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve WebSocket status: {str(e)}"
        )


@router.get("/ws/connections")
async def websocket_connections_endpoint():
    """
    Get information about active WebSocket connections.
    
    Returns:
        JSON response with connection information
    """
    try:
        connected_users = manager.get_connected_users()
        total_connections = manager.get_connection_count()
        
        connection_info = {
            "total_connections": total_connections,
            "connected_users": len(connected_users),
            "user_connections": {}
        }
        
        # Get connection count per user
        for user_id in connected_users:
            connection_info["user_connections"][user_id] = manager.get_user_connection_count(user_id)
        
        return JSONResponse({
            "success": True,
            "data": connection_info,
            "message": "WebSocket connections retrieved successfully"
        })
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve WebSocket connections: {str(e)}"
        )


@router.get("/ws/channels")
async def websocket_channels_endpoint():
    """
    Get information about WebSocket channels and subscriptions.
    
    Returns:
        JSON response with channel information
    """
    try:
        channel_info = {}
        
        # Get channel subscribers
        for channel in websocket_service.channel_subscribers:
            subscribers = websocket_service.get_channel_subscribers(channel)
            channel_info[channel] = {
                "subscriber_count": len(subscribers),
                "subscribers": list(subscribers)
            }
        
        return JSONResponse({
            "success": True,
            "data": {
                "channels": channel_info,
                "total_channels": len(channel_info)
            },
            "message": "WebSocket channels retrieved successfully"
        })
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve WebSocket channels: {str(e)}"
        )


@router.post("/ws/broadcast")
async def websocket_broadcast_endpoint(message: dict):
    """
    Broadcast a message to all connected WebSocket clients.
    
    Args:
        message: Message to broadcast
        
    Returns:
        JSON response with broadcast results
    """
    try:
        # Validate message format
        if "type" not in message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message must contain 'type' field"
            )
        
        # Broadcast the message
        success_count = await manager.broadcast(message)
        
        return JSONResponse({
            "success": True,
            "data": {
                "message_sent": message,
                "recipients": success_count
            },
            "message": f"Message broadcasted to {success_count} connections"
        })
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to broadcast message: {str(e)}"
        )


@router.post("/ws/broadcast/channel/{channel}")
async def websocket_broadcast_channel_endpoint(
    channel: str,
    message: dict,
    exclude_user: Optional[str] = None
):
    """
    Broadcast a message to all subscribers of a specific channel.
    
    Args:
        channel: Channel name
        message: Message to broadcast
        exclude_user: User ID to exclude from broadcast
        
    Returns:
        JSON response with broadcast results
    """
    try:
        # Validate message format
        if "type" not in message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message must contain 'type' field"
            )
        
        # Broadcast to channel
        success_count = await websocket_service.broadcast_to_channel(
            channel, message, exclude_user
        )
        
        return JSONResponse({
            "success": True,
            "data": {
                "channel": channel,
                "message_sent": message,
                "recipients": success_count,
                "exclude_user": exclude_user
            },
            "message": f"Message broadcasted to {success_count} subscribers of channel '{channel}'"
        })
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to broadcast to channel: {str(e)}"
        )


@router.post("/ws/notify/{user_id}")
async def websocket_notify_user_endpoint(
    user_id: str,
    notification: dict
):
    """
    Send a notification to a specific user via WebSocket.
    
    Args:
        user_id: ID of the target user
        notification: Notification data
        
    Returns:
        JSON response with notification results
    """
    try:
        # Validate notification format
        if "type" not in notification:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Notification must contain 'type' field"
            )
        
        # Send notification to user
        success = await websocket_service.send_notification_to_user(user_id, notification)
        
        return JSONResponse({
            "success": success,
            "data": {
                "user_id": user_id,
                "notification_sent": notification,
                "delivered": success
            },
            "message": f"Notification {'sent' if success else 'not sent'} to user {user_id}"
        })
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send notification: {str(e)}"
        ) 