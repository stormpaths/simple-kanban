"""
Group model for team-based board ownership and permissions.
"""

from typing import List, Optional
from sqlalchemy import String, Text, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from .base import Base, TimestampMixin


class GroupRole(str, enum.Enum):
    """User roles within a group."""

    MEMBER = "member"
    ADMIN = "admin"
    OWNER = "owner"


class Group(Base, TimestampMixin):
    """
    Group model for team-based board management.

    Groups enable multiple users to collaborate on boards with
    role-based permissions and hierarchical access control.
    """

    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])
    members: Mapped[List["UserGroup"]] = relationship(
        "UserGroup", back_populates="group", cascade="all, delete-orphan"
    )
    boards: Mapped[List["Board"]] = relationship(
        "Board", back_populates="group", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Group(id={self.id}, name='{self.name}')>"


class UserGroup(Base, TimestampMixin):
    """
    Association table for users and groups with role-based permissions.

    Tracks which users belong to which groups and their role within each group.
    """

    __tablename__ = "user_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    group_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[GroupRole] = mapped_column(
        SQLEnum(GroupRole), default=GroupRole.MEMBER, nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    group: Mapped["Group"] = relationship("Group", back_populates="members")

    def __repr__(self) -> str:
        return f"<UserGroup(user_id={self.user_id}, group_id={self.group_id}, role={self.role})>"
