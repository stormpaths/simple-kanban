"""
Board model for kanban boards.
"""

from typing import List, Optional
from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Board(Base, TimestampMixin):
    """
    Kanban board model with support for both individual and group ownership.

    Boards can be owned by individual users (owner_id) or by groups (group_id).
    This enables team collaboration while maintaining backward compatibility.
    """

    __tablename__ = "boards"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Ownership - either individual user or group (mutually exclusive)
    owner_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    group_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=True
    )

    # Relationships
    owner: Mapped[Optional["User"]] = relationship("User", back_populates="boards")
    group: Mapped[Optional["Group"]] = relationship("Group", back_populates="boards")
    columns: Mapped[List["Column"]] = relationship(
        "Column",
        back_populates="board",
        cascade="all, delete-orphan",
        order_by="Column.position",
    )

    def is_accessible_by_user(self, user_id: int) -> bool:
        """
        Check if a user has access to this board.

        A user has access if:
        1. They own the board directly (owner_id)
        2. They are a member of the group that owns the board (group_id)
        """
        # Direct ownership
        if self.owner_id == user_id:
            return True

        # Group ownership - check if user is a member of the owning group
        if self.group_id and self.group:
            return any(member.user_id == user_id for member in self.group.members)

        return False

    def get_owner_type(self) -> str:
        """Get the type of ownership for this board."""
        if self.owner_id:
            return "user"
        elif self.group_id:
            return "group"
        else:
            return "unknown"

    def __repr__(self) -> str:
        return f"<Board(id={self.id}, name='{self.name}')>"
