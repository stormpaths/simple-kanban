"""
Board-related Pydantic schemas.
"""
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class BoardCreate(BaseModel):
    """Schema for creating a new board."""
    name: str
    description: Optional[str] = None


class BoardUpdate(BaseModel):
    """Schema for updating a board."""
    name: Optional[str] = None
    description: Optional[str] = None


class BoardResponse(BaseModel):
    """Schema for board response."""
    id: int
    name: str
    description: Optional[str]
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BoardWithColumnsResponse(BoardResponse):
    """Schema for board response with columns included."""
    columns: List[dict] = []
