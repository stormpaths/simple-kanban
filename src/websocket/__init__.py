"""
WebSocket module for real-time updates.

Provides WebSocket connections and Redis pub/sub for broadcasting
task and board changes across all connected clients.
"""

from .manager import ConnectionManager, get_connection_manager
from .events import BoardEvent, EventType

__all__ = ["ConnectionManager", "get_connection_manager", "BoardEvent", "EventType"]
