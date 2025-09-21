"""
User model for authentication and authorization.
"""
from typing import Optional, List
from sqlalchemy import String, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from passlib.context import CryptContext

from .base import Base, TimestampMixin

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base, TimestampMixin):
    """
    User model for authentication.
    
    Enhanced user model supporting local authentication with JWT tokens
    and future OIDC integration capabilities.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # NULL for OIDC-only users
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    boards: Mapped[List["Board"]] = relationship("Board", back_populates="owner", cascade="all, delete-orphan")
    task_comments: Mapped[List["TaskComment"]] = relationship("TaskComment", back_populates="author", cascade="all, delete-orphan")
    
    # Group relationships
    group_memberships: Mapped[List["UserGroup"]] = relationship("UserGroup", back_populates="user", cascade="all, delete-orphan")
    created_groups: Mapped[List["Group"]] = relationship("Group", foreign_keys="Group.created_by")
    
    # Future relationships for OIDC providers
    # oidc_providers: Mapped[List["OIDCProvider"]] = relationship("OIDCProvider", back_populates="user")
    
    def verify_password(self, password: str) -> bool:
        """Verify a password against the stored hash."""
        if not self.hashed_password:
            return False
        return pwd_context.verify(password, self.hashed_password)
    
    def set_password(self, password: str) -> None:
        """Hash and set a new password."""
        self.hashed_password = pwd_context.hash(password)
    
    @classmethod
    def hash_password(cls, password: str) -> str:
        """Hash a password (class method for utility use)."""
        return pwd_context.hash(password)
    
    def get_groups(self) -> List["Group"]:
        """Get all groups this user belongs to."""
        return [membership.group for membership in self.group_memberships]
    
    def is_member_of_group(self, group_id: int) -> bool:
        """Check if user is a member of the specified group."""
        return any(membership.group_id == group_id for membership in self.group_memberships)
    
    def get_group_role(self, group_id: int) -> Optional[str]:
        """Get user's role in the specified group."""
        for membership in self.group_memberships:
            if membership.group_id == group_id:
                return membership.role.value
        return None
    
    def is_group_admin(self, group_id: int) -> bool:
        """Check if user is an admin or owner of the specified group."""
        role = self.get_group_role(group_id)
        return role in ["admin", "owner"]
    
    # Relationships - commented out to avoid async/sync issues in OIDC flow
    # oidc_providers = relationship("OIDCProvider", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}', is_active={self.is_active})>"
