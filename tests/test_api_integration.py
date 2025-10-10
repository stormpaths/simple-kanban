"""
API integration tests for Simple Kanban Board.

Tests complete API workflows, endpoint interactions, and business logic.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

from src.main import app
from src.database import get_db_session, Base
from src.models.user import User
from src.models.board import Board
from src.models.column import Column
from src.models.task import Task


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_api.db"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db():
    """Override database dependency for testing."""
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db_session] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="function")
async def setup_database():
    """Setup test database for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def authenticated_user():
    """Create and authenticate a test user."""
    async with TestSessionLocal() as session:
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            is_active=True,
            is_verified=True,
        )
        user.set_password("testpassword123")
        session.add(user)
        await session.commit()
        await session.refresh(user)

    # Login to get token
    login_data = {"username": "testuser", "password": "testpassword123"}
    response = client.post("/api/auth/login", data=login_data)
    token = response.json()["access_token"]

    return {
        "user": user,
        "token": token,
        "headers": {
            "Authorization": f"Bearer {token}",
            "X-CSRF-Token": "test_csrf_token_12345678",
        },
    }


class TestBoardAPI:
    """Test board API endpoints."""

    @pytest.mark.asyncio
    async def test_create_board(self, setup_database, authenticated_user):
        """Test creating a new board."""
        board_data = {"name": "My Test Board", "description": "A board for testing"}

        response = client.post(
            "/api/boards", json=board_data, headers=authenticated_user["headers"]
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My Test Board"
        assert data["description"] == "A board for testing"
        assert data["owner_id"] == authenticated_user["user"].id
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_list_boards(self, setup_database, authenticated_user):
        """Test listing user's boards."""
        # Create a board first
        board_data = {"name": "Test Board", "description": "Test"}
        client.post(
            "/api/boards", json=board_data, headers=authenticated_user["headers"]
        )

        # List boards
        response = client.get("/api/boards", headers=authenticated_user["headers"])

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["name"] == "Test Board"

    @pytest.mark.asyncio
    async def test_get_board_with_columns_and_tasks(
        self, setup_database, authenticated_user
    ):
        """Test getting a board with its columns and tasks."""
        # Create board
        board_response = client.post(
            "/api/boards",
            json={"name": "Test Board", "description": "Test"},
            headers=authenticated_user["headers"],
        )
        board_id = board_response.json()["id"]

        # Create column
        column_response = client.post(
            f"/api/boards/{board_id}/columns",
            json={"name": "To Do", "position": 1},
            headers=authenticated_user["headers"],
        )
        column_id = column_response.json()["id"]

        # Create task
        client.post(
            f"/api/columns/{column_id}/tasks",
            json={"title": "Test Task", "description": "Test", "position": 1},
            headers=authenticated_user["headers"],
        )

        # Get board with all data
        response = client.get(
            f"/api/boards/{board_id}", headers=authenticated_user["headers"]
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Board"
        assert len(data["columns"]) == 1
        assert data["columns"][0]["name"] == "To Do"
        assert len(data["columns"][0]["tasks"]) == 1
        assert data["columns"][0]["tasks"][0]["title"] == "Test Task"

    @pytest.mark.asyncio
    async def test_update_board(self, setup_database, authenticated_user):
        """Test updating a board."""
        # Create board
        board_response = client.post(
            "/api/boards",
            json={"name": "Original Name", "description": "Original"},
            headers=authenticated_user["headers"],
        )
        board_id = board_response.json()["id"]

        # Update board
        update_data = {"name": "Updated Name", "description": "Updated description"}
        response = client.put(
            f"/api/boards/{board_id}",
            json=update_data,
            headers=authenticated_user["headers"],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_delete_board(self, setup_database, authenticated_user):
        """Test deleting a board."""
        # Create board
        board_response = client.post(
            "/api/boards",
            json={"name": "To Delete", "description": "Test"},
            headers=authenticated_user["headers"],
        )
        board_id = board_response.json()["id"]

        # Delete board
        response = client.delete(
            f"/api/boards/{board_id}", headers=authenticated_user["headers"]
        )

        assert response.status_code == 204

        # Verify deletion
        response = client.get(
            f"/api/boards/{board_id}", headers=authenticated_user["headers"]
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_unauthorized_board_access(self, setup_database, authenticated_user):
        """Test that users cannot access other users' boards."""
        # Create another user
        async with TestSessionLocal() as session:
            other_user = User(
                username="otheruser", email="other@example.com", is_active=True
            )
            other_user.set_password("password123")
            session.add(other_user)
            await session.commit()
            await session.refresh(other_user)

            # Create board for other user
            board = Board(
                name="Other User's Board",
                description="Private board",
                owner_id=other_user.id,
            )
            session.add(board)
            await session.commit()
            await session.refresh(board)
            board_id = board.id

        # Try to access other user's board
        response = client.get(
            f"/api/boards/{board_id}", headers=authenticated_user["headers"]
        )
        assert response.status_code == 404  # Should not be found for this user


class TestColumnAPI:
    """Test column API endpoints."""

    @pytest.mark.asyncio
    async def test_create_column(self, setup_database, authenticated_user):
        """Test creating a new column."""
        # Create board first
        board_response = client.post(
            "/api/boards",
            json={"name": "Test Board", "description": "Test"},
            headers=authenticated_user["headers"],
        )
        board_id = board_response.json()["id"]

        # Create column
        column_data = {"name": "To Do", "position": 1}
        response = client.post(
            f"/api/boards/{board_id}/columns",
            json=column_data,
            headers=authenticated_user["headers"],
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "To Do"
        assert data["position"] == 1
        assert data["board_id"] == board_id

    @pytest.mark.asyncio
    async def test_update_column(self, setup_database, authenticated_user):
        """Test updating a column."""
        # Create board and column
        board_response = client.post(
            "/api/boards",
            json={"name": "Test Board", "description": "Test"},
            headers=authenticated_user["headers"],
        )
        board_id = board_response.json()["id"]

        column_response = client.post(
            f"/api/boards/{board_id}/columns",
            json={"name": "Original", "position": 1},
            headers=authenticated_user["headers"],
        )
        column_id = column_response.json()["id"]

        # Update column
        update_data = {"name": "Updated Column", "position": 2}
        response = client.put(
            f"/api/columns/{column_id}",
            json=update_data,
            headers=authenticated_user["headers"],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Column"
        assert data["position"] == 2

    @pytest.mark.asyncio
    async def test_delete_column(self, setup_database, authenticated_user):
        """Test deleting a column."""
        # Create board and column
        board_response = client.post(
            "/api/boards",
            json={"name": "Test Board", "description": "Test"},
            headers=authenticated_user["headers"],
        )
        board_id = board_response.json()["id"]

        column_response = client.post(
            f"/api/boards/{board_id}/columns",
            json={"name": "To Delete", "position": 1},
            headers=authenticated_user["headers"],
        )
        column_id = column_response.json()["id"]

        # Delete column
        response = client.delete(
            f"/api/columns/{column_id}", headers=authenticated_user["headers"]
        )

        assert response.status_code == 204


class TestTaskAPI:
    """Test task API endpoints."""

    @pytest.mark.asyncio
    async def test_create_task(self, setup_database, authenticated_user):
        """Test creating a new task."""
        # Create board and column
        board_response = client.post(
            "/api/boards",
            json={"name": "Test Board", "description": "Test"},
            headers=authenticated_user["headers"],
        )
        board_id = board_response.json()["id"]

        column_response = client.post(
            f"/api/boards/{board_id}/columns",
            json={"name": "To Do", "position": 1},
            headers=authenticated_user["headers"],
        )
        column_id = column_response.json()["id"]

        # Create task
        task_data = {"title": "Test Task", "description": "A test task", "position": 1}
        response = client.post(
            f"/api/columns/{column_id}/tasks",
            json=task_data,
            headers=authenticated_user["headers"],
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Task"
        assert data["description"] == "A test task"
        assert data["position"] == 1
        assert data["column_id"] == column_id

    @pytest.mark.asyncio
    async def test_move_task_between_columns(self, setup_database, authenticated_user):
        """Test moving a task between columns."""
        # Create board and columns
        board_response = client.post(
            "/api/boards",
            json={"name": "Test Board", "description": "Test"},
            headers=authenticated_user["headers"],
        )
        board_id = board_response.json()["id"]

        column1_response = client.post(
            f"/api/boards/{board_id}/columns",
            json={"name": "To Do", "position": 1},
            headers=authenticated_user["headers"],
        )
        column1_id = column1_response.json()["id"]

        column2_response = client.post(
            f"/api/boards/{board_id}/columns",
            json={"name": "In Progress", "position": 2},
            headers=authenticated_user["headers"],
        )
        column2_id = column2_response.json()["id"]

        # Create task in first column
        task_response = client.post(
            f"/api/columns/{column1_id}/tasks",
            json={"title": "Test Task", "description": "Test", "position": 1},
            headers=authenticated_user["headers"],
        )
        task_id = task_response.json()["id"]

        # Move task to second column
        move_data = {"column_id": column2_id, "position": 1}
        response = client.put(
            f"/api/tasks/{task_id}",
            json=move_data,
            headers=authenticated_user["headers"],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["column_id"] == column2_id
        assert data["position"] == 1

    @pytest.mark.asyncio
    async def test_delete_task(self, setup_database, authenticated_user):
        """Test deleting a task."""
        # Create board, column, and task
        board_response = client.post(
            "/api/boards",
            json={"name": "Test Board", "description": "Test"},
            headers=authenticated_user["headers"],
        )
        board_id = board_response.json()["id"]

        column_response = client.post(
            f"/api/boards/{board_id}/columns",
            json={"name": "To Do", "position": 1},
            headers=authenticated_user["headers"],
        )
        column_id = column_response.json()["id"]

        task_response = client.post(
            f"/api/columns/{column_id}/tasks",
            json={"title": "To Delete", "description": "Test", "position": 1},
            headers=authenticated_user["headers"],
        )
        task_id = task_response.json()["id"]

        # Delete task
        response = client.delete(
            f"/api/tasks/{task_id}", headers=authenticated_user["headers"]
        )

        assert response.status_code == 204


class TestCompleteWorkflows:
    """Test complete kanban board workflows."""

    @pytest.mark.asyncio
    async def test_complete_kanban_workflow(self, setup_database, authenticated_user):
        """Test a complete kanban board workflow."""
        # 1. Create a board
        board_response = client.post(
            "/api/boards",
            json={"name": "Project Board", "description": "Main project board"},
            headers=authenticated_user["headers"],
        )
        board_id = board_response.json()["id"]

        # 2. Create columns
        columns = []
        for i, name in enumerate(["Backlog", "To Do", "In Progress", "Done"], 1):
            response = client.post(
                f"/api/boards/{board_id}/columns",
                json={"name": name, "position": i},
                headers=authenticated_user["headers"],
            )
            columns.append(response.json())

        # 3. Create tasks in backlog
        tasks = []
        for i in range(3):
            response = client.post(
                f"/api/columns/{columns[0]['id']}/tasks",
                json={
                    "title": f"Task {i+1}",
                    "description": f"Description for task {i+1}",
                    "position": i + 1,
                },
                headers=authenticated_user["headers"],
            )
            tasks.append(response.json())

        # 4. Move first task through workflow
        task_id = tasks[0]["id"]

        # Move to "To Do"
        response = client.put(
            f"/api/tasks/{task_id}",
            json={"column_id": columns[1]["id"], "position": 1},
            headers=authenticated_user["headers"],
        )
        assert response.status_code == 200

        # Move to "In Progress"
        response = client.put(
            f"/api/tasks/{task_id}",
            json={"column_id": columns[2]["id"], "position": 1},
            headers=authenticated_user["headers"],
        )
        assert response.status_code == 200

        # Move to "Done"
        response = client.put(
            f"/api/tasks/{task_id}",
            json={"column_id": columns[3]["id"], "position": 1},
            headers=authenticated_user["headers"],
        )
        assert response.status_code == 200

        # 5. Verify final board state
        response = client.get(
            f"/api/boards/{board_id}", headers=authenticated_user["headers"]
        )
        board_data = response.json()

        assert len(board_data["columns"]) == 4

        # Check task distribution
        backlog_tasks = len(board_data["columns"][0]["tasks"])
        done_tasks = len(board_data["columns"][3]["tasks"])

        assert backlog_tasks == 2  # 2 tasks remaining in backlog
        assert done_tasks == 1  # 1 task moved to done

    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, setup_database, authenticated_user):
        """Test error handling in API workflows."""
        # Try to access non-existent board
        response = client.get(
            "/api/boards/99999", headers=authenticated_user["headers"]
        )
        assert response.status_code == 404

        # Try to create column for non-existent board
        response = client.post(
            "/api/boards/99999/columns",
            json={"name": "Test", "position": 1},
            headers=authenticated_user["headers"],
        )
        assert response.status_code == 404

        # Try to create task for non-existent column
        response = client.post(
            "/api/columns/99999/tasks",
            json={"title": "Test", "position": 1},
            headers=authenticated_user["headers"],
        )
        assert response.status_code == 404

        # Try to move task to non-existent column
        # First create a valid task
        board_response = client.post(
            "/api/boards",
            json={"name": "Test Board", "description": "Test"},
            headers=authenticated_user["headers"],
        )
        board_id = board_response.json()["id"]

        column_response = client.post(
            f"/api/boards/{board_id}/columns",
            json={"name": "Test Column", "position": 1},
            headers=authenticated_user["headers"],
        )
        column_id = column_response.json()["id"]

        task_response = client.post(
            f"/api/columns/{column_id}/tasks",
            json={"title": "Test Task", "position": 1},
            headers=authenticated_user["headers"],
        )
        task_id = task_response.json()["id"]

        # Try to move to non-existent column
        response = client.put(
            f"/api/tasks/{task_id}",
            json={"column_id": 99999, "position": 1},
            headers=authenticated_user["headers"],
        )
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
