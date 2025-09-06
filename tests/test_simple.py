"""
Simple tests to verify security hardening and basic functionality.

These tests use mocking to avoid database dependencies and focus on
testing the security middleware and core functionality.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

from src.main import app
from src.auth.jwt_handler import jwt_handler


# Create test client
client = TestClient(app)


class TestJWTSecurity:
    """Test JWT token security."""
    
    def test_create_access_token(self):
        """Test JWT token creation."""
        user_data = {"sub": "testuser", "user_id": 1}
        token = jwt_handler.create_access_token(user_data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count('.') == 2  # JWT has 3 parts separated by dots
    
    def test_verify_valid_token(self):
        """Test verification of valid JWT token."""
        user_data = {"sub": "testuser", "user_id": 1}
        token = jwt_handler.create_access_token(user_data)
        
        token_data = jwt_handler.verify_token(token)
        
        assert token_data is not None
        assert token_data.username == "testuser"
        assert token_data.user_id == 1
    
    def test_verify_invalid_token(self):
        """Test verification of invalid JWT token."""
        invalid_token = "invalid.jwt.token"
        
        token_data = jwt_handler.verify_token(invalid_token)
        
        assert token_data is None


class TestSecurityMiddleware:
    """Test security middleware functionality."""
    
    def test_security_headers_present(self):
        """Test that security headers are added to responses."""
        response = client.get("/health")
        
        assert response.status_code == 200
        headers = response.headers
        
        # Check for security headers
        assert "X-Content-Type-Options" in headers
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert "X-Frame-Options" in headers
        assert headers["X-Frame-Options"] == "DENY"
        assert "X-XSS-Protection" in headers
        assert "Content-Security-Policy" in headers
    
    def test_rate_limiting_allows_normal_requests(self):
        """Test that rate limiting allows normal request volumes."""
        # Make several requests within normal limits
        for _ in range(5):
            response = client.get("/health")
            assert response.status_code == 200
    
    def test_csrf_protection_allows_safe_methods(self):
        """Test that CSRF protection allows safe HTTP methods."""
        response = client.get("/health")
        assert response.status_code == 200
        
        response = client.options("/api/auth/profile")
        assert response.status_code in [200, 405]  # Either allowed or method not allowed


class TestBasicEndpoints:
    """Test basic application endpoints."""
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        # Should return either the HTML file or JSON response
        assert response.status_code == 200
    
    def test_metrics_endpoint(self):
        """Test metrics endpoint."""
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "requests_total" in data
        assert "uptime_seconds" in data
        assert "memory_usage_mb" in data


class TestAuthenticationSecurity:
    """Test authentication security without database."""
    
    def test_unauthenticated_access_blocked(self):
        """Test that protected endpoints block unauthenticated access."""
        response = client.get("/api/auth/profile")
        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]
    
    def test_invalid_token_rejected(self):
        """Test that invalid tokens are rejected."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/auth/profile", headers=headers)
        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]
    
    @patch('src.middleware.security.settings.csrf_protection_enabled', True)
    def test_csrf_protection_blocks_unsafe_methods_without_token(self):
        """Test that CSRF protection blocks unsafe methods without token."""
        response = client.post("/api/boards", json={"name": "Test Board"})
        
        # Should be blocked by CSRF protection
        assert response.status_code == 403
        assert "CSRF token missing" in response.json()["detail"]
    
    @patch('src.middleware.security.settings.csrf_protection_enabled', True)
    def test_csrf_protection_allows_unsafe_methods_with_token(self):
        """Test that CSRF protection allows unsafe methods with valid token."""
        headers = {"X-CSRF-Token": "valid_csrf_token_12345678"}
        response = client.post("/api/boards", json={"name": "Test Board"}, headers=headers)
        
        # Should pass CSRF check (may fail later due to auth, but not CSRF)
        assert response.status_code != 403 or "CSRF token" not in response.json().get("detail", "")


class TestPasswordSecurity:
    """Test password hashing and validation."""
    
    def test_password_hashing(self):
        """Test that passwords are properly hashed."""
        from src.models.user import User
        
        user = User(username="test", email="test@example.com")
        password = "testpassword123"
        
        user.set_password(password)
        
        assert user.hashed_password != password
        assert user.hashed_password is not None
        assert len(user.hashed_password) > 50  # Bcrypt hashes are long
    
    def test_password_verification_correct(self):
        """Test password verification with correct password."""
        from src.models.user import User
        
        user = User(username="test", email="test@example.com")
        password = "testpassword123"
        
        user.set_password(password)
        
        assert user.verify_password(password) is True
    
    def test_password_verification_incorrect(self):
        """Test password verification with incorrect password."""
        from src.models.user import User
        
        user = User(username="test", email="test@example.com")
        password = "testpassword123"
        wrong_password = "wrongpassword"
        
        user.set_password(password)
        
        assert user.verify_password(wrong_password) is False


class TestConfigurationSecurity:
    """Test security configuration validation."""
    
    @patch.dict('os.environ', {'JWT_SECRET_KEY': 'short'})
    def test_jwt_secret_validation_short_key(self):
        """Test that short JWT secrets are rejected."""
        from src.core.config import Settings
        
        with pytest.raises(ValueError, match="JWT_SECRET_KEY must be at least 32 characters"):
            Settings(jwt_secret_key="short")
    
    @patch.dict('os.environ', {'JWT_SECRET_KEY': 'a' * 32})
    def test_jwt_secret_validation_valid_key(self):
        """Test that valid JWT secrets are accepted."""
        from src.core.config import Settings
        
        settings = Settings(jwt_secret_key='a' * 32)
        assert len(settings.jwt_secret_key) == 32


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
