"""
Pydantic schemas for the Simple Kanban Board application.

This module consolidates all API request/response schemas for better organization
and maintainability.
"""

from .auth import *
from .board import *
from .column import *
from .task import *
from .group import *
from .api_key import *
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
    
    # Group schemas
    "GroupCreate", "GroupUpdate", "GroupResponse", "GroupListResponse",
    "UserGroupCreate", "UserGroupUpdate", "UserGroupResponse", "GroupRole",
    "GroupMembershipRequest", "GroupMembershipResponse", "UserInfo",
    
    # API Key schemas
    "ApiKeyCreate", "ApiKeyUpdate", "ApiKeyResponse", "ApiKeyCreateResponse",
    "ApiKeyListResponse", "ApiKeyUsageStats", "ApiKeyScope",
    
    # Common schemas
    "HealthResponse", "MessageRequest", "MessageResponse"
]
