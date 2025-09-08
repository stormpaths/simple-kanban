"""
Admin-related Pydantic schemas for API requests and responses.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class UserStatsResponse(BaseModel):
    """Response schema for user statistics."""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    is_admin: bool
    is_verified: bool
    created_at: datetime
    board_count: int = Field(description="Number of boards owned by the user")
    task_count: int = Field(description="Total number of tasks across all user's boards")

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    """Request schema for updating user properties."""
    is_active: Optional[bool] = Field(None, description="Enable or disable the user account")
    is_admin: Optional[bool] = Field(None, description="Grant or revoke admin privileges")
