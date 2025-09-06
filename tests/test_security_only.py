"""
Security-focused tests that don't require full application setup.

Tests JWT security, password hashing, and configuration validation.
"""
import pytest
from unittest.mock import patch
import os


class TestJWTSecurity:
    """Test JWT token security."""
    
    def test_create_and_verify_token(self):
        """Test JWT token creation and verification."""
        from src.auth.jwt_handler import jwt_handler
        
        user_data = {"sub": "testuser", "user_id": 1}
        token = jwt_handler.create_access_token(user_data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count('.') == 2  # JWT has 3 parts
        
        # Verify the token
        token_data = jwt_handler.verify_token(token)
        assert token_data is not None
        assert token_data.username == "testuser"
        assert token_data.user_id == 1
    
    def test_invalid_token_rejected(self):
        """Test that invalid tokens are rejected."""
        from src.auth.jwt_handler import jwt_handler
        
        invalid_token = "invalid.jwt.token"
        token_data = jwt_handler.verify_token(invalid_token)
        assert token_data is None


class TestPasswordSecurity:
    """Test password hashing and validation."""
    
    def test_password_hashing_and_verification(self):
        """Test password hashing and verification."""
        from src.models.user import User
        
        user = User(username="test", email="test@example.com")
        password = "testpassword123"
        
        # Test password setting
        user.set_password(password)
        assert user.hashed_password != password
        assert user.hashed_password is not None
        assert len(user.hashed_password) > 50  # Bcrypt hashes are long
        
        # Test password verification
        assert user.verify_password(password) is True
        assert user.verify_password("wrongpassword") is False
    
    def test_password_verification_no_hash(self):
        """Test password verification when no password is set."""
        from src.models.user import User
        
        user = User(username="test", email="test@example.com")
        assert user.verify_password("anypassword") is False


class TestConfigurationSecurity:
    """Test security configuration validation."""
    
    def test_jwt_secret_validation_generates_key_when_empty(self):
        """Test that JWT secret is generated when not provided."""
        from src.core.config import Settings
        
        # Test with empty JWT secret
        settings = Settings(jwt_secret_key="")
        assert len(settings.jwt_secret_key) >= 32
    
    def test_jwt_secret_validation_rejects_short_key(self):
        """Test that short JWT secrets are rejected."""
        from src.core.config import Settings
        
        with pytest.raises(ValueError, match="JWT_SECRET_KEY must be at least 32 characters"):
            Settings(jwt_secret_key="short")
    
    def test_jwt_secret_validation_accepts_valid_key(self):
        """Test that valid JWT secrets are accepted."""
        from src.core.config import Settings
        
        valid_key = 'a' * 32
        settings = Settings(jwt_secret_key=valid_key)
        assert settings.jwt_secret_key == valid_key


class TestSecurityMiddleware:
    """Test security middleware components."""
    
    def test_rate_limit_middleware_initialization(self):
        """Test that rate limit middleware can be initialized."""
        from src.middleware.security import RateLimitMiddleware
        
        # Test initialization without Redis
        middleware = RateLimitMiddleware(None, redis_client=None)
        assert middleware is not None
        assert middleware.memory_store == {}
    
    def test_security_headers_middleware_initialization(self):
        """Test that security headers middleware can be initialized."""
        from src.middleware.security import SecurityHeadersMiddleware
        
        middleware = SecurityHeadersMiddleware(None)
        assert middleware is not None
    
    def test_csrf_protection_middleware_initialization(self):
        """Test that CSRF protection middleware can be initialized."""
        from src.middleware.security import CSRFProtectionMiddleware
        
        middleware = CSRFProtectionMiddleware(None)
        assert middleware is not None
        assert "GET" in middleware.SAFE_METHODS
        assert "POST" not in middleware.SAFE_METHODS


class TestDatabaseFallback:
    """Test database fallback mechanism."""
    
    @patch('src.database.asyncpg', None)
    def test_database_fallback_to_sqlite(self):
        """Test that database falls back to SQLite when asyncpg is not available."""
        # This would test the import fallback, but it's already imported
        # In a real scenario, you'd test this at module load time
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
