"""
Board model for kanban boards.
"""
from typing import List, Optional
from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Board(Base, TimestampMixin):
    """
    Kanban board model.
    
    Supports future multi-board functionality while maintaining
    single-board simplicity for MVP.
    """
    __tablename__ = "boards"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="boards")
    columns: Mapped[List["Column"]] = relationship(
        "Column", 
        back_populates="board",
        cascade="all, delete-orphan",
        order_by="Column.position"
    )
    
    def __repr__(self) -> str:
        return f"<Board(id={self.id}, name='{self.name}')>"
