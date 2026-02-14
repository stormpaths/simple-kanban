"""
WebSocket connection manager with Redis pub/sub support.

Manages WebSocket connections for real-time updates and uses Redis
pub/sub to broadcast events across multiple server instances.
"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
import redis.asyncio as redis

from ..core.config import settings
from .events import BoardEvent, EventType

logger = logging.getLogger(__name__)

# Redis channel for broadcasting events
REDIS_CHANNEL = "kanban:events"


class ConnectionManager:
    """
    Manages WebSocket connections and broadcasts events to clients.
    
    Uses Redis pub/sub to support multiple server instances broadcasting
    to all connected clients across the cluster.
    """
    
    def __init__(self):
        # board_id -> set of WebSocket connections
        self._connections: Dict[int, Set[WebSocket]] = {}
        self._redis_client: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None
        self._listener_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """Initialize Redis connection and start listening for events."""
        if self._running:
            return
            
        try:
            self._redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            await self._redis_client.ping()
            logger.info("WebSocket manager connected to Redis")
            
            # Start pub/sub listener
            self._pubsub = self._redis_client.pubsub()
            await self._pubsub.subscribe(REDIS_CHANNEL)
            self._running = True
            self._listener_task = asyncio.create_task(self._listen_for_events())
            logger.info("WebSocket manager started listening for Redis events")
            
        except Exception as e:
            logger.warning(f"Redis not available for WebSocket pub/sub: {e}")
            logger.info("WebSocket manager will work in local-only mode")
            self._running = True
    
    async def stop(self):
        """Stop the connection manager and clean up resources."""
        self._running = False
        
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        
        if self._pubsub:
            await self._pubsub.unsubscribe(REDIS_CHANNEL)
            await self._pubsub.close()
        
        if self._redis_client:
            await self._redis_client.close()
        
        # Close all WebSocket connections
        for board_id in list(self._connections.keys()):
            for ws in list(self._connections.get(board_id, [])):
                try:
                    await ws.close()
                except Exception:
                    pass
        
        self._connections.clear()
        logger.info("WebSocket manager stopped")
    
    async def connect(self, websocket: WebSocket, board_id: int, user_id: Optional[int] = None):
        """
        Accept a new WebSocket connection for a specific board.
        
        Args:
            websocket: The WebSocket connection
            board_id: ID of the board to subscribe to
            user_id: Optional user ID for the connection
        """
        await websocket.accept()
        
        if board_id not in self._connections:
            self._connections[board_id] = set()
        self._connections[board_id].add(websocket)
        
        logger.info(f"WebSocket connected: board_id={board_id}, user_id={user_id}")
        
        # Send connection confirmation
        await websocket.send_json({
            "event_type": EventType.CONNECTED.value,
            "board_id": board_id,
            "message": "Connected to real-time updates",
        })
    
    def disconnect(self, websocket: WebSocket, board_id: int):
        """
        Remove a WebSocket connection.
        
        Args:
            websocket: The WebSocket connection to remove
            board_id: ID of the board the connection was subscribed to
        """
        if board_id in self._connections:
            self._connections[board_id].discard(websocket)
            if not self._connections[board_id]:
                del self._connections[board_id]
        
        logger.info(f"WebSocket disconnected: board_id={board_id}")
    
    async def broadcast_event(self, event: BoardEvent):
        """
        Broadcast an event to all clients subscribed to the board.
        
        If Redis is available, publishes to Redis for cross-instance delivery.
        Otherwise, broadcasts directly to local connections only.
        
        Args:
            event: The event to broadcast
        """
        event_json = json.dumps(event.to_json())
        
        # Publish to Redis if available (for multi-instance support)
        if self._redis_client:
            try:
                await self._redis_client.publish(REDIS_CHANNEL, event_json)
                logger.debug(f"Published event to Redis: {event.event_type}")
                return  # Redis listener will handle local broadcast
            except Exception as e:
                logger.warning(f"Failed to publish to Redis: {e}")
        
        # Fallback: broadcast directly to local connections
        await self._broadcast_to_local(event)
    
    async def _broadcast_to_local(self, event: BoardEvent):
        """Broadcast event to locally connected WebSocket clients."""
        board_id = event.board_id
        
        if board_id not in self._connections:
            return
        
        disconnected = set()
        event_data = event.to_json()
        
        for websocket in self._connections[board_id]:
            try:
                await websocket.send_json(event_data)
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected clients
        for ws in disconnected:
            self._connections[board_id].discard(ws)
    
    async def _listen_for_events(self):
        """Listen for events from Redis pub/sub and broadcast to local clients."""
        try:
            while self._running and self._pubsub:
                message = await self._pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0,
                )
                
                if message and message["type"] == "message":
                    try:
                        event_data = json.loads(message["data"])
                        event = BoardEvent(
                            event_type=EventType(event_data["event_type"]),
                            board_id=event_data["board_id"],
                            data=event_data["data"],
                            user_id=event_data.get("user_id"),
                        )
                        await self._broadcast_to_local(event)
                    except Exception as e:
                        logger.error(f"Failed to process Redis message: {e}")
                
                await asyncio.sleep(0.01)  # Small delay to prevent busy loop
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Redis listener error: {e}")


# Global connection manager instance
_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance."""
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager
