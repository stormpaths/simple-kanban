"""
TaskComment-related Pydantic schemas.
"""
from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class TaskCommentCreate(BaseModel):
    """Schema for creating a new task comment."""
    content: str
    task_id: int


class TaskCommentUpdate(BaseModel):
    """Schema for updating a task comment."""
    content: str


class TaskCommentResponse(BaseModel):
    """Schema for task comment response."""
    id: int
    content: str
    task_id: int
    author_id: int
    author_name: str  # Derived from author relationship
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskCommentListResponse(BaseModel):
    """Schema for listing task comments."""
    comments: list[TaskCommentResponse]
    total: int
