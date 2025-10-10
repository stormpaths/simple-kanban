"""
Column management API routes.

Provides CRUD operations for kanban board columns.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Board, Column
from ..schemas import (
    ColumnCreate,
    ColumnResponse,
    ColumnUpdate,
    ColumnWithTasksResponse,
)

router = APIRouter(prefix="/columns", tags=["columns"])


@router.post("/", response_model=ColumnResponse, status_code=status.HTTP_201_CREATED)
async def create_column(column: ColumnCreate, db: Session = Depends(get_db)):
    """Create a new column in a board."""
    # Verify board exists
    board = db.query(Board).filter(Board.id == column.board_id).first()
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Board not found"
        )

    db_column = Column(
        name=column.name, position=column.position, board_id=column.board_id
    )
    db.add(db_column)
    db.commit()
    db.refresh(db_column)
    return db_column


@router.get("/board/{board_id}", response_model=List[ColumnWithTasksResponse])
async def list_board_columns(board_id: int, db: Session = Depends(get_db)):
    """List all columns for a specific board."""
    # Verify board exists
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Board not found"
        )

    columns = (
        db.query(Column)
        .filter(Column.board_id == board_id)
        .order_by(Column.position)
        .all()
    )

    # Convert to response format with tasks
    result = []
    for col in columns:
        col_dict = {
            "id": col.id,
            "name": col.name,
            "position": col.position,
            "board_id": col.board_id,
            "created_at": col.created_at.isoformat(),
            "updated_at": col.updated_at.isoformat(),
            "tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "position": task.position,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                }
                for task in col.tasks
            ],
        }
        result.append(col_dict)

    return result


@router.get("/{column_id}", response_model=ColumnWithTasksResponse)
async def get_column(column_id: int, db: Session = Depends(get_db)):
    """Get a specific column with its tasks."""
    column = db.query(Column).filter(Column.id == column_id).first()
    if not column:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Column not found"
        )

    # Convert to response format
    col_dict = {
        "id": column.id,
        "name": column.name,
        "position": column.position,
        "board_id": column.board_id,
        "created_at": column.created_at.isoformat(),
        "updated_at": column.updated_at.isoformat(),
        "tasks": [
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "position": task.position,
            }
            for task in column.tasks
        ],
    }

    return col_dict


@router.put("/{column_id}", response_model=ColumnResponse)
async def update_column(
    column_id: int, column_update: ColumnUpdate, db: Session = Depends(get_db)
):
    """Update a column's name or position."""
    column = db.query(Column).filter(Column.id == column_id).first()
    if not column:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Column not found"
        )

    if column_update.name is not None:
        column.name = column_update.name
    if column_update.position is not None:
        column.position = column_update.position

    db.commit()
    db.refresh(column)
    return column


@router.delete("/{column_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_column(column_id: int, db: Session = Depends(get_db)):
    """Delete a column and all its tasks."""
    column = db.query(Column).filter(Column.id == column_id).first()
    if not column:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Column not found"
        )

    db.delete(column)
    db.commit()


@router.post("/{column_id}/reorder", status_code=status.HTTP_200_OK)
async def reorder_column(
    column_id: int, new_position: int, db: Session = Depends(get_db)
):
    """Reorder a column within its board."""
    column = db.query(Column).filter(Column.id == column_id).first()
    if not column:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Column not found"
        )

    old_position = column.position
    board_id = column.board_id

    # Get all columns in the board
    columns = (
        db.query(Column)
        .filter(Column.board_id == board_id)
        .order_by(Column.position)
        .all()
    )

    # Update positions
    if new_position > old_position:
        # Moving right - shift columns left
        for col in columns:
            if old_position < col.position <= new_position:
                col.position -= 1
    else:
        # Moving left - shift columns right
        for col in columns:
            if new_position <= col.position < old_position:
                col.position += 1

    # Set new position
    column.position = new_position

    db.commit()
    return {"message": "Column reordered successfully"}
