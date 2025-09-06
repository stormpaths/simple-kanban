"""
Pydantic schemas for the Simple Kanban Board application.

This module consolidates all API request/response schemas for better organization
and maintainability.
"""

from .auth import *
from .board import *
from .column import *
from .task import *
from .common import *

__all__ = [
    # Auth schemas
    "UserCreate", "UserLogin", "UserResponse", "UserUpdate", "PasswordChange", "PasswordChangeRequest",
    "TokenResponse", "TokenData", "Token", "OIDCAuthRequest", "OIDCCallbackRequest",
    "OIDCUserInfo", "AccountLinkRequest",
    
    # Board schemas
    "BoardCreate", "BoardUpdate", "BoardResponse", "BoardWithColumnsResponse",
    
    # Column schemas
    "ColumnCreate", "ColumnUpdate", "ColumnResponse", "ColumnWithTasksResponse",
    
    # Task schemas
    "TaskCreate", "TaskUpdate", "TaskMove", "TaskResponse",
    
    # Common schemas
    "HealthResponse", "MessageRequest", "MessageResponse"
]
