"""
API Key model for authentication and testing.
"""

import secrets
import hashlib
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy import String, Boolean, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum

from .base import Base, TimestampMixin


class ApiKeyScope(str, Enum):
    """API key scopes for permission control."""

    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    DOCS = "docs"  # Special scope for accessing documentation


class ApiKey(Base, TimestampMixin):
    """
    API Key model for programmatic access.

    Supports expiration, scoping, and secure key generation for testing
    and automated access to the kanban board API.
    """

    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Security fields
    key_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    key_prefix: Mapped[str] = mapped_column(
        String(8), nullable=False, index=True
    )  # First 8 chars for identification

    # Ownership and permissions
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    scopes: Mapped[str] = mapped_column(
        String(500), nullable=False, default="read"
    )  # Comma-separated scopes

    # Expiration and status
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="api_keys")

    @classmethod
    def generate_key(cls) -> tuple[str, str]:
        """
        Generate a new API key and return (full_key, hash).

        Returns:
            tuple: (full_key, key_hash) where full_key is what the user sees
                   and key_hash is what we store in the database
        """
        # Generate a secure random key (32 bytes = 64 hex chars)
        full_key = f"sk_{secrets.token_urlsafe(32)}"

        # Hash the key for storage (using SHA-256)
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()

        return full_key, key_hash

    @classmethod
    def hash_key(cls, key: str) -> str:
        """Hash an API key for comparison."""
        return hashlib.sha256(key.encode()).hexdigest()

    def get_prefix(self, key: str) -> str:
        """Get the prefix (first 8 chars) of a key for identification."""
        return key[:8] if len(key) >= 8 else key

    def has_scope(self, scope: str) -> bool:
        """Check if the API key has a specific scope."""
        if not self.scopes:
            return False

        key_scopes = [s.strip() for s in self.scopes.split(",")]

        # Admin scope grants all permissions
        if "admin" in key_scopes:
            return True

        return scope in key_scopes

    def is_valid(self) -> bool:
        """Check if the API key is valid (active and not expired)."""
        if not self.is_active:
            return False

        if self.expires_at:
            from datetime import timezone

            now = datetime.now(timezone.utc)
            if now > self.expires_at:
                return False

        return True

    def get_scopes_list(self) -> List[str]:
        """Get list of scopes for this API key."""
        if not self.scopes:
            return []
        return [s.strip() for s in self.scopes.split(",")]

    def set_scopes(self, scopes: List[str]) -> None:
        """Set scopes from a list."""
        self.scopes = ",".join(scopes)

    def record_usage(self) -> None:
        """Record that this API key was used."""
        from datetime import timezone

        self.last_used_at = datetime.now(timezone.utc)
        self.usage_count += 1

    def __repr__(self) -> str:
        return f"<ApiKey(id={self.id}, name='{self.name}', prefix='{self.key_prefix}', active={self.is_active})>"
