"""
Authentication-related Pydantic schemas.
"""

from typing import Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from datetime import datetime


class UserCreate(BaseModel):
    """Schema for user registration."""

    username: str = Field(
        ..., min_length=3, max_length=50, description="Username (3-50 characters)"
    )
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(
        ..., min_length=8, max_length=128, description="Password (8-128 characters)"
    )
    full_name: Optional[str] = Field(
        None, max_length=255, description="Full name (optional)"
    )


class UserLogin(BaseModel):
    """Schema for user login."""

    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")


class UserResponse(BaseModel):
    """Schema for user response (excludes sensitive data)."""

    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    is_admin: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """Schema for user profile updates."""

    full_name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None


class PasswordChange(BaseModel):
    """Schema for password change."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ..., min_length=8, max_length=128, description="New password (8-128 characters)"
    )


class PasswordChangeRequest(BaseModel):
    """Schema for password change request."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ..., min_length=8, max_length=128, description="New password (8-128 characters)"
    )


class TokenData(BaseModel):
    """Token data model for JWT payload."""

    username: Optional[str] = None
    user_id: Optional[int] = None


class Token(BaseModel):
    """Token response model."""

    access_token: str
    token_type: str = "bearer"


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class OIDCAuthRequest(BaseModel):
    """Schema for OIDC authentication initiation."""

    provider: str = Field(..., description="OIDC provider name (e.g., 'google')")
    redirect_url: Optional[str] = Field(
        None, description="URL to redirect to after authentication"
    )


class OIDCCallbackRequest(BaseModel):
    """Schema for OIDC callback handling."""

    code: str = Field(..., description="Authorization code from provider")
    state: str = Field(..., description="State parameter for CSRF protection")


class OIDCUserInfo(BaseModel):
    """Schema for OIDC user information."""

    provider: str
    provider_user_id: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


class AccountLinkRequest(BaseModel):
    """Schema for linking OIDC account to existing user."""

    username: str = Field(..., description="Existing username to link to")
    password: str = Field(..., description="Password for existing account")
