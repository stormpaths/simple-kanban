"""
Pydantic schemas for group management.
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class GroupRole(str, Enum):
    """User roles within a group."""
    MEMBER = "member"
    ADMIN = "admin"
    OWNER = "owner"


class GroupBase(BaseModel):
    """Base schema for group data."""
    name: str = Field(..., min_length=1, max_length=255, description="Group name")
    description: Optional[str] = Field(None, max_length=1000, description="Group description")


class GroupCreate(GroupBase):
    """Schema for creating a new group."""
    pass


class GroupUpdate(BaseModel):
    """Schema for updating group information."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Group name")
    description: Optional[str] = Field(None, max_length=1000, description="Group description")


class UserGroupBase(BaseModel):
    """Base schema for user-group membership."""
    user_id: int = Field(..., description="User ID")
    role: GroupRole = Field(GroupRole.MEMBER, description="User role in the group")


class UserGroupCreate(UserGroupBase):
    """Schema for adding a user to a group."""
    pass


class UserGroupUpdate(BaseModel):
    """Schema for updating user role in a group."""
    role: GroupRole = Field(..., description="New role for the user")


class UserInfo(BaseModel):
    """Basic user information for group membership display."""
    id: int
    username: str
    full_name: Optional[str]
    email: str
    
    class Config:
        from_attributes = True


class UserGroupResponse(BaseModel):
    """Schema for user-group membership response."""
    id: int
    user_id: int
    group_id: int
    role: GroupRole
    created_at: datetime
    updated_at: datetime
    user: UserInfo
    
    class Config:
        from_attributes = True


class GroupResponse(BaseModel):
    """Schema for group response with member information."""
    id: int
    name: str
    description: Optional[str]
    created_by: int
    created_at: datetime
    updated_at: datetime
    members: List[UserGroupResponse] = []
    member_count: int = 0
    
    class Config:
        from_attributes = True


class GroupListResponse(BaseModel):
    """Schema for group list response (without detailed member info)."""
    id: int
    name: str
    description: Optional[str]
    created_by: int
    created_at: datetime
    updated_at: datetime
    member_count: int = 0
    user_role: Optional[GroupRole] = None  # Current user's role in this group
    
    class Config:
        from_attributes = True


class GroupMembershipRequest(BaseModel):
    """Schema for group membership requests."""
    user_id: int = Field(..., description="ID of user to add to group")
    role: GroupRole = Field(GroupRole.MEMBER, description="Role to assign to user")


class GroupMembershipResponse(BaseModel):
    """Schema for group membership operation responses."""
    success: bool
    message: str
    user_group: Optional[UserGroupResponse] = None
