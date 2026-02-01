"""
Unit tests for the main FastAPI application.

Tests cover all endpoints and basic functionality.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint returns correct response."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "status" in data
    assert data["status"] == "running"


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_echo_endpoint_valid_message():
    """Test echo endpoint with valid message."""
    test_message = "Hello, World!"
    response = client.post("/echo", json={"message": test_message})
    assert response.status_code == 200
    data = response.json()
    assert data["echo"] == test_message
    assert data["length"] == len(test_message)


def test_echo_endpoint_empty_message():
    """Test echo endpoint with empty message."""
    response = client.post("/echo", json={"message": ""})
    assert response.status_code == 400
    assert "Message cannot be empty" in response.json()["detail"]


def test_echo_endpoint_whitespace_message():
    """Test echo endpoint with whitespace-only message."""
    response = client.post("/echo", json={"message": "   "})
    assert response.status_code == 400


def test_metrics_endpoint():
    """Test metrics endpoint returns expected structure."""
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "requests_total" in data
    assert "uptime_seconds" in data
    assert "memory_usage_mb" in data


def test_docs_endpoint():
    """Test that OpenAPI docs are accessible."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_redoc_endpoint():
    """Test that ReDoc documentation is accessible."""
    response = client.get("/redoc")
    assert response.status_code == 200
