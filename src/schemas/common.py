"""
Common Pydantic schemas used across the application.
"""
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str
    version: str


class MessageRequest(BaseModel):
    """Schema for message request."""
    message: str


class MessageResponse(BaseModel):
    """Schema for message response."""
    echo: str
    length: int
