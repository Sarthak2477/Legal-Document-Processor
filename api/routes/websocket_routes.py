"""
WebSocket routes for real-time communication.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from api.websocket import websocket_endpoint, manager
from api.services import AuthService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/{user_id}")
async def websocket_connection(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time updates.
    
    Provides real-time notifications for:
    - Contract processing progress
    - Analysis completion
    - Batch processing updates
    - System notifications
    """
    # TODO: Add proper authentication for WebSocket connections
    # For now, accept any user_id for development
    
    await websocket_endpoint(websocket, user_id)


@router.get("/ws/stats", tags=["WebSocket"])
async def get_websocket_stats():
    """Get WebSocket connection statistics."""
    stats = {
        "total_connections": sum(len(connections) for connections in manager.active_connections.values()),
        "connected_users": len(manager.active_connections),
        "connections_per_user": {
            user_id: len(connections) 
            for user_id, connections in manager.active_connections.items()
        }
    }
    
    return stats


@router.post("/ws/broadcast/{user_id}", tags=["WebSocket"])
async def send_test_message(user_id: str, message: dict):
    """Send test message to user (development only)."""
    await manager.send_personal_message(message, user_id)
    return {"message": "Test message sent", "user_id": user_id}