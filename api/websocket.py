"""
WebSocket endpoints for real-time updates.
"""
import json
import logging
from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept WebSocket connection."""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
        logger.info(f"WebSocket connected for user {user_id}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove WebSocket connection."""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to specific user."""
        if user_id in self.active_connections:
            disconnected = []
            
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    disconnected.append(connection)
            
            # Clean up disconnected connections
            for connection in disconnected:
                self.disconnect(connection, user_id)
    
    async def broadcast_to_user(self, message: dict, user_id: str):
        """Broadcast message to all connections for a user."""
        await self.send_personal_message(message, user_id)


# Global connection manager
manager = ConnectionManager()


async def notify_processing_update(contract_id: str, user_id: str, status: str, progress: int, message: str = ""):
    """Send processing update notification."""
    update_message = {
        "type": "processing_update",
        "data": {
            "contract_id": contract_id,
            "status": status,
            "progress": progress,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
    }
    
    await manager.send_personal_message(update_message, user_id)


async def notify_analysis_complete(contract_id: str, user_id: str, analysis_summary: dict):
    """Send analysis completion notification."""
    notification = {
        "type": "analysis_complete",
        "data": {
            "contract_id": contract_id,
            "summary": analysis_summary,
            "timestamp": datetime.now().isoformat()
        }
    }
    
    await manager.send_personal_message(notification, user_id)


async def notify_batch_update(batch_id: str, user_id: str, status: str, progress: int):
    """Send batch processing update."""
    update_message = {
        "type": "batch_update",
        "data": {
            "batch_id": batch_id,
            "status": status,
            "progress": progress,
            "timestamp": datetime.now().isoformat()
        }
    }
    
    await manager.send_personal_message(update_message, user_id)


# WebSocket endpoint handler
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """Handle WebSocket connections."""
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "ping":
                    # Respond to ping with pong
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))
                
                elif message_type == "subscribe":
                    # Handle subscription to specific events
                    await websocket.send_text(json.dumps({
                        "type": "subscribed",
                        "data": message.get("data", {}),
                        "timestamp": datetime.now().isoformat()
                    }))
                
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from user {user_id}")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {str(e)}")
        manager.disconnect(websocket, user_id)