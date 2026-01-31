"""
Task model for kanban board tasks.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from .base import Base, TimestampMixin


class Task(Base, TimestampMixin):
    """
    Kanban task model.

    Core entity representing individual tasks that can be moved
    between columns on the kanban board.
    """

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Structured data fields for enhanced tracking
    tags: Mapped[Optional[List[str]]] = mapped_column(JSONB, default=list)
    task_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, default=dict)
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    steps: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSONB, default=list)
    results: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # Foreign key to column
    column_id: Mapped[int] = mapped_column(
        ForeignKey("columns.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    column: Mapped["Column"] = relationship("Column", back_populates="tasks")
    task_comments: Mapped[list["TaskComment"]] = relationship(
        "TaskComment", back_populates="task", cascade="all, delete-orphan"
    )

    @property
    def status(self) -> str:
        """Get task status based on column name."""
        return self.column.name if self.column else "unknown"

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title='{self.title}', column_id={self.column_id})>"
