"""WebSocket endpoints for real-time updates."""

from typing import List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from redis import asyncio as aioredis
import json
import structlog

from app.config import settings

router = APIRouter()
logger = structlog.get_logger()


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: WebSocket connection to register
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("websocket_connected", total_connections=len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection to remove
        """
        self.active_connections.remove(websocket)
        logger.info("websocket_disconnected", total_connections=len(self.active_connections))

    async def broadcast(self, message: dict):
        """
        Broadcast message to all connected clients.

        Args:
            message: Message dictionary to broadcast
        """
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error("websocket_send_failed", error=str(e))
                disconnected.append(connection)

        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)


manager = ConnectionManager()


@router.websocket("/ws/realtime")
async def websocket_realtime(websocket: WebSocket):
    """
    WebSocket endpoint for real-time station and bike updates.

    Clients connect to this endpoint to receive real-time notifications
    when station status or bike positions change.
    """
    await manager.connect(websocket)

    try:
        # Subscribe to Redis pub/sub for real-time updates
        redis_client = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )

        pubsub = redis_client.pubsub()
        await pubsub.subscribe("station_status_changed", "bike_position_changed")

        # Send initial connection message
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "message": "Connected to Vélivert real-time updates"
        })

        # Listen for Redis pub/sub messages
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    await websocket.send_json(data)
                except Exception as e:
                    logger.error("websocket_message_parse_failed", error=str(e))

            # Also listen for client messages (heartbeat, etc.)
            try:
                client_message = await websocket.receive_text()
                if client_message == "ping":
                    await websocket.send_json({"type": "pong"})
            except:
                pass  # No message from client

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("websocket_client_disconnected")

    except Exception as e:
        logger.error("websocket_error", error=str(e), exc_info=True)
        manager.disconnect(websocket)

    finally:
        try:
            await pubsub.unsubscribe()
            await redis_client.close()
        except:
            pass