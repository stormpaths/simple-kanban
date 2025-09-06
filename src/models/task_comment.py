"""
TaskComment model for individual task comments with timestamps and authorship.
"""
from typing import Optional
from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class TaskComment(Base, TimestampMixin):
    """
    Individual comment on a kanban task.
    
    Stores individual comments with timestamps and author information,
    allowing for a proper comment thread on each task.
    """
    __tablename__ = "task_comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Foreign key to task
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Foreign key to user (author)
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="comments")
    author: Mapped["User"] = relationship("User", back_populates="task_comments")
    
    def __repr__(self) -> str:
        return f"<TaskComment(id={self.id}, task_id={self.task_id}, author_id={self.author_id})>"
