"""
Task-related Pydantic schemas.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


class TaskStep(BaseModel):
    """Schema for a task completion step."""
    
    step: str
    completed: bool = False
    completed_at: Optional[datetime] = None


class TaskResults(BaseModel):
    """Schema for task results/summary."""
    
    summary: Optional[str] = None
    output: Optional[str] = None
    status: Optional[str] = None  # success, failed, partial
    data: Optional[Dict[str, Any]] = None


class TaskCreate(BaseModel):
    """Schema for creating a new task."""

    title: str
    description: Optional[str] = None
    column_id: int
    position: Optional[int] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    task_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    priority: Optional[str] = "medium"
    steps: Optional[List[TaskStep]] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    """Schema for updating a task."""

    title: Optional[str] = None
    description: Optional[str] = None
    position: Optional[int] = None
    tags: Optional[List[str]] = None
    task_metadata: Optional[Dict[str, Any]] = None
    priority: Optional[str] = None
    steps: Optional[List[TaskStep]] = None
    results: Optional[TaskResults] = None


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
    tags: Optional[List[str]] = None
    task_metadata: Optional[Dict[str, Any]] = None
    priority: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = None
    results: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
