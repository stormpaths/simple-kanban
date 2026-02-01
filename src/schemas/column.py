"""
Column-related Pydantic schemas.
"""

from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class ColumnCreate(BaseModel):
    """Schema for creating a new column."""

    name: str
    position: int
    board_id: int


class ColumnUpdate(BaseModel):
    """Schema for updating a column."""

    name: Optional[str] = None
    position: Optional[int] = None


class ColumnResponse(BaseModel):
    """Schema for column response."""

    id: int
    name: str
    position: int
    board_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ColumnWithTasksResponse(ColumnResponse):
    """Schema for column response with tasks included."""

    tasks: List[dict] = []
