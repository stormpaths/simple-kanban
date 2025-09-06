"""
OIDC Provider model for linking external identity providers to users.
"""
from typing import Optional
from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .base import Base, TimestampMixin


class OIDCProvider(Base, TimestampMixin):
    """Model for storing OIDC provider connections."""
    
    __tablename__ = "oidc_providers"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # 'google', 'microsoft', 'github', etc.
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)  # External user ID from provider
    provider_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Email from provider
    provider_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Display name from provider
    provider_avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # Avatar URL from provider
    
    # Relationships - commented out to avoid async/sync issues in OIDC flow
    # user = relationship("User", back_populates="oidc_providers")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('provider', 'provider_user_id', name='uq_provider_user'),
    )
    
    def __repr__(self):
        return f"<OIDCProvider(id={self.id}, user_id={self.user_id}, provider='{self.provider}', provider_user_id='{self.provider_user_id}')>"
