"""
TaskComment-related Pydantic schemas.
"""
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
import html


class TaskCommentCreate(BaseModel):
    """Schema for creating a new task comment."""
    content: str = Field(..., min_length=1, max_length=2000, description="Comment content")
    task_id: int
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError('Comment content cannot be empty')
        # Sanitize HTML to prevent XSS
        return html.escape(v.strip())


class TaskCommentUpdate(BaseModel):
    """Schema for updating a task comment."""
    content: str = Field(..., min_length=1, max_length=2000, description="Comment content")
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError('Comment content cannot be empty')
        # Sanitize HTML to prevent XSS
        return html.escape(v.strip())


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
