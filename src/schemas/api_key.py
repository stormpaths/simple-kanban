"""
Pydantic schemas for API key management.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class ApiKeyScope(str, Enum):
    """API key scopes for permission control."""

    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    DOCS = "docs"


class ApiKeyCreate(BaseModel):
    """Schema for creating a new API key."""

    name: str = Field(..., min_length=1, max_length=255, description="API key name")
    description: Optional[str] = Field(
        None, max_length=1000, description="API key description"
    )
    scopes: List[ApiKeyScope] = Field(
        default=[ApiKeyScope.READ], description="API key scopes"
    )
    expires_in_days: Optional[int] = Field(
        None, ge=1, le=365, description="Expiration in days (max 365)"
    )

    @validator("scopes")
    def validate_scopes(cls, v):
        if not v:
            return [ApiKeyScope.READ]
        # Remove duplicates while preserving order
        seen = set()
        return [scope for scope in v if not (scope in seen or seen.add(scope))]


class ApiKeyUpdate(BaseModel):
    """Schema for updating an API key."""

    name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="API key name"
    )
    description: Optional[str] = Field(
        None, max_length=1000, description="API key description"
    )
    is_active: Optional[bool] = Field(None, description="Whether the API key is active")


class ApiKeyResponse(BaseModel):
    """Schema for API key response (without the actual key)."""

    id: int
    name: str
    description: Optional[str]
    key_prefix: str  # Only show first 8 characters
    scopes: List[str]
    expires_at: Optional[datetime]
    is_active: bool
    last_used_at: Optional[datetime]
    usage_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApiKeyCreateResponse(BaseModel):
    """Schema for API key creation response (includes the actual key once)."""

    api_key: str  # The full key - only shown once!
    key_info: ApiKeyResponse
    warning: str = "This is the only time you'll see this key. Store it securely!"


class ApiKeyListResponse(BaseModel):
    """Schema for listing API keys."""

    api_keys: List[ApiKeyResponse]
    total: int


class ApiKeyUsageStats(BaseModel):
    """Schema for API key usage statistics."""

    total_keys: int
    active_keys: int
    expired_keys: int
    total_requests: int
    requests_today: int
    most_used_key: Optional[ApiKeyResponse]
    recent_usage: List[dict]  # Recent usage events
