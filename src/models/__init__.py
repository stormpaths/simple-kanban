"""
Database models for the kanban application.
"""

from .base import Base, TimestampMixin
from .user import User
from .oidc_provider import OIDCProvider
from .group import Group, UserGroup, GroupRole
from .api_key import ApiKey, ApiKeyScope
from .board import Board
from .column import Column
from .task import Task
from .task_comment import TaskComment

# Import all models to ensure they're registered with SQLAlchemy
__all__ = [
    "Base",
    "TimestampMixin",
    "User",
    "OIDCProvider",
    "Group",
    "UserGroup",
    "GroupRole",
    "ApiKey",
    "ApiKeyScope",
    "Board",
    "Column",
    "Task",
    "TaskComment",
]
