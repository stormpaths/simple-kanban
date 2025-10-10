"""
Column model for kanban board columns.
"""

from typing import List, Optional
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Column(Base, TimestampMixin):
    """
    Kanban column model (To Do, In Progress, Done).

    Supports flexible column management with positioning
    and future customization capabilities.
    """

    __tablename__ = "columns"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    board_id: Mapped[int] = mapped_column(
        ForeignKey("boards.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    board: Mapped["Board"] = relationship("Board", back_populates="columns")
    tasks: Mapped[List["Task"]] = relationship(
        "Task",
        back_populates="column",
        cascade="all, delete-orphan",
        order_by="Task.position",
    )

    def __repr__(self) -> str:
        return f"<Column(id={self.id}, name='{self.name}', position={self.position})>"
