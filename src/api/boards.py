"""
Board management API routes.

Provides CRUD operations for kanban boards.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from ..database import get_db_session
from ..models.board import Board
from ..models.column import Column
from ..models.task import Task
from ..models.user import User
from ..schemas import (
    BoardCreate,
    BoardResponse,
    BoardUpdate,
    BoardWithColumnsResponse,
    ColumnWithTasksResponse,
)
from ..auth.dependencies import get_current_user, get_user_from_api_key_or_jwt
from ..utils.sql import get_sql_builder


async def _get_accessible_owner_ids(db: AsyncSession, user: User) -> List[int]:
    """
    Get all owner IDs that the user can access boards for.

    This includes:
    - User's own ID (direct ownership)
    - Group IDs where the user is a member
    """
    accessible_ids = [user.id]

    # Add group IDs where user is a member
    from ..models import UserGroup

    group_result = await db.execute(
        select(UserGroup.group_id).where(UserGroup.user_id == user.id)
    )
    group_ids = [row[0] for row in group_result.fetchall()]
    accessible_ids.extend(group_ids)

    return accessible_ids


async def _can_access_board(db: AsyncSession, user: User, board_id: int) -> bool:
    """
    Check if user can access a specific board.
    Returns True if user owns the board directly or through group membership.
    """
    accessible_owner_ids = await _get_accessible_owner_ids(db, user)

    result = await db.execute(
        select(Board).where(
            and_(
                Board.id == board_id,
                or_(
                    Board.owner_id.in_(accessible_owner_ids),
                    Board.group_id.in_(accessible_owner_ids),
                ),
            )
        )
    )

    return result.scalar_one_or_none() is not None


router = APIRouter(prefix="/boards", tags=["boards"])


@router.post("/", response_model=BoardResponse, status_code=status.HTTP_201_CREATED)
async def create_board(
    board: BoardCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_user_from_api_key_or_jwt),
):
    """Create a new kanban board with default columns."""

    # Validate group ownership if specified
    if board.group_id:
        # Check if user is a member of the specified group
        from ..models import UserGroup

        group_membership = await db.execute(
            select(UserGroup).where(
                and_(
                    UserGroup.group_id == board.group_id,
                    UserGroup.user_id == current_user.id,
                )
            )
        )

        if not group_membership.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of the specified group",
            )

        # Create group-owned board
        db_board = Board(
            name=board.name,
            description=board.description,
            group_id=board.group_id,
            owner_id=None,  # No individual owner for group boards
        )
    else:
        # Create user-owned board
        db_board = Board(
            name=board.name,
            description=board.description,
            owner_id=current_user.id,
            group_id=None,
        )
    db.add(db_board)
    await db.flush()  # Get the board ID

    # Create default columns
    default_columns = [
        {"name": "To Do", "position": 0},
        {"name": "In Progress", "position": 1},
        {"name": "Done", "position": 2},
    ]

    for col_data in default_columns:
        db_column = Column(
            name=col_data["name"], position=col_data["position"], board_id=db_board.id
        )
        db.add(db_column)

    await db.commit()
    await db.refresh(db_board)
    return db_board


@router.get("/", response_model=List[BoardResponse])
async def list_boards(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_user_from_api_key_or_jwt),
):
    """List all kanban boards accessible to the current user."""
    # Get accessible owner IDs (user + future groups)
    accessible_owner_ids = await _get_accessible_owner_ids(db, current_user)

    result = await db.execute(
        select(Board).where(
            or_(
                Board.owner_id.in_(accessible_owner_ids),
                Board.group_id.in_(accessible_owner_ids),
            )
        )
    )
    boards = result.scalars().all()
    return boards


@router.get("/{board_id}", response_model=BoardWithColumnsResponse)
async def get_board(
    board_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_user_from_api_key_or_jwt),
):
    """Get a specific board with its columns and tasks."""
    # Check if user can access this board (direct ownership or group membership)
    if not await _can_access_board(db, current_user, board_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Board not found"
        )

    # Get the board with columns and tasks in a single query

    result = await db.execute(
        select(Board)
        .where(Board.id == board_id)
        .options(selectinload(Board.columns).selectinload(Column.tasks))
    )
    board = result.scalar_one_or_none()

    # Convert to dict with columns and tasks
    board_dict = {
        "id": board.id,
        "name": board.name,
        "description": board.description,
        "owner_id": board.owner_id,
        "group_id": board.group_id,
        "created_at": board.created_at,
        "updated_at": board.updated_at,
        "columns": [
            {
                "id": col.id,
                "name": col.name,
                "position": col.position,
                "tasks": [
                    {
                        "id": task.id,
                        "title": task.title,
                        "description": task.description,
                        "position": task.position,
                        "tags": task.tags,
                        "priority": task.priority,
                        "steps": task.steps,
                        "results": task.results,
                        "task_metadata": task.task_metadata,
                        "created_at": task.created_at,
                        "updated_at": task.updated_at,
                    }
                    for task in sorted(col.tasks, key=lambda t: t.position)
                ],
            }
            for col in sorted(board.columns, key=lambda c: c.position)
        ],
    }

    return board_dict


@router.put("/{board_id}", response_model=BoardResponse)
async def update_board(
    board_id: int,
    board_update: BoardUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_user_from_api_key_or_jwt),
):
    """Update a board's name or description."""
    # Check if user can access this board (direct ownership or group membership)
    if not await _can_access_board(db, current_user, board_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Board not found"
        )

    result = await db.execute(select(Board).where(Board.id == board_id))
    board = result.scalar_one_or_none()

    if board_update.name is not None:
        board.name = board_update.name
    if board_update.description is not None:
        board.description = board_update.description

    await db.commit()
    await db.refresh(board)
    return board


@router.get("/{board_id}/columns")
async def get_board_columns(
    board_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_user_from_api_key_or_jwt),
):
    """Get all columns for a specific board."""
    # Check if user can access this board (direct ownership or group membership)
    if not await _can_access_board(db, current_user, board_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Board not found"
        )

    columns_result = await db.execute(
        select(Column).where(Column.board_id == board_id).order_by(Column.position)
    )
    columns = columns_result.scalars().all()

    return [
        {
            "id": col.id,
            "name": col.name,
            "position": col.position,
            "board_id": col.board_id,
        }
        for col in columns
    ]


@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_board(
    board_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_user_from_api_key_or_jwt),
):
    """Delete a board and all its columns and tasks."""
    # Check if user can access this board (direct ownership or group membership)
    if not await _can_access_board(db, current_user, board_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Board not found"
        )

    result = await db.execute(select(Board).where(Board.id == board_id))
    board = result.scalar_one_or_none()

    await db.delete(board)
    await db.commit()
