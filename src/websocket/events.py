"""
WebSocket event definitions for real-time updates.

Defines event types and data structures for broadcasting
task and board changes to connected clients.
"""

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel
from datetime import datetime


class EventType(str, Enum):
    """Types of real-time events that can be broadcast."""
    
    # Task events
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_MOVED = "task_moved"
    TASK_DELETED = "task_deleted"
    
    # Column events
    COLUMN_CREATED = "column_created"
    COLUMN_UPDATED = "column_updated"
    COLUMN_DELETED = "column_deleted"
    
    # Board events
    BOARD_UPDATED = "board_updated"
    
    # Comment events
    COMMENT_CREATED = "comment_created"
    COMMENT_UPDATED = "comment_updated"
    COMMENT_DELETED = "comment_deleted"
    
    # Connection events
    CONNECTED = "connected"
    ERROR = "error"


class BoardEvent(BaseModel):
    """
    Event data structure for broadcasting changes.
    
    Attributes:
        event_type: Type of event (task_created, task_updated, etc.)
        board_id: ID of the board this event relates to
        data: Event-specific payload data
        user_id: ID of user who triggered the event (optional)
        timestamp: When the event occurred
    """
    
    event_type: EventType
    board_id: int
    data: Dict[str, Any]
    user_id: Optional[int] = None
    timestamp: datetime = None
    
    def __init__(self, **data):
        if data.get("timestamp") is None:
            data["timestamp"] = datetime.utcnow()
        super().__init__(**data)
    
    def to_json(self) -> Dict[str, Any]:
        """Convert event to JSON-serializable dict."""
        return {
            "event_type": self.event_type.value,
            "board_id": self.board_id,
            "data": self.data,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
