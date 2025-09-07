"""
Task-related Pydantic schemas.
"""
from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class TaskCreate(BaseModel):
    """Schema for creating a new task."""
    title: str
    description: Optional[str] = None
    column_id: int
    position: Optional[int] = None


class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    title: Optional[str] = None
    description: Optional[str] = None
    position: Optional[int] = None


class TaskMove(BaseModel):
    """Schema for moving a task to a different column/position."""
    column_id: int
    position: int


class TaskResponse(BaseModel):
    """Schema for task response."""
    id: int
    title: str
    description: Optional[str]
    column_id: int
    position: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
