"""
Configuration management for Simple Kanban Board application.
"""

import os
import secrets
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application Configuration
    app_name: str = "Simple Kanban Board"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    # API Configuration
    api_v1_str: str = "/api/v1"
    project_name: str = "Simple Kanban Board"
    project_description: str = "Self-hosted kanban board with story planning"

    # Security Configuration
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "")
    jwt_access_token_expire_minutes: int = 1440  # 24 hours
    jwt_refresh_token_expire_days: int = 7
    session_secret_key: str = os.getenv("SESSION_SECRET_KEY", "")
    session_cookie_secure: bool = (
        os.getenv("ENVIRONMENT", "development") == "production"
    )
    session_cookie_httponly: bool = True
    session_cookie_samesite: str = "strict"

    # Security Headers
    security_headers_enabled: bool = True
    csrf_protection_enabled: bool = False

    # Database Configuration
    database_url: Optional[str] = None
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "simple_kanban"
    postgres_user: str = "kanban"
    postgres_password: str = Field(
        default="", description="PostgreSQL password from environment"
    )

    # Redis Configuration
    redis_url: Optional[str] = None
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0

    def model_post_init(self, __context) -> None:
        """Post-initialization hook to load environment variables and construct URLs."""
        # Load environment variables at runtime
        self.postgres_host = os.getenv("POSTGRES_HOST", self.postgres_host)
        self.postgres_port = int(os.getenv("POSTGRES_PORT", str(self.postgres_port)))
        self.postgres_db = os.getenv("POSTGRES_DB", self.postgres_db)
        self.postgres_user = os.getenv("POSTGRES_USER", self.postgres_user)
        self.postgres_password = os.getenv("POSTGRES_PASSWORD", self.postgres_password)

        self.redis_host = os.getenv("REDIS_HOST", self.redis_host)
        self.redis_port = int(os.getenv("REDIS_PORT", str(self.redis_port)))
        self.redis_password = os.getenv("REDIS_PASSWORD", self.redis_password)
        self.redis_db = int(os.getenv("REDIS_DB", str(self.redis_db)))

        # Debug: Print loaded values
        print(f"DEBUG: postgres_host={self.postgres_host}")
        print(f"DEBUG: postgres_user={self.postgres_user}")
        print(f"DEBUG: postgres_password={self.postgres_password}")
        print(f"DEBUG: postgres_db={self.postgres_db}")

        # Construct database_url from components if not provided
        if not self.database_url:
            self.database_url = f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

        # Construct redis_url from components if not provided
        if not self.redis_url:
            if self.redis_password:
                self.redis_url = f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
            else:
                self.redis_url = (
                    f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
                )

        print(f"DEBUG: Final database_url={self.database_url}")

    # CORS Configuration
    backend_cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080",
    ]

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret_key(cls, v):
        if not v:
            # Generate a secure key for development, but require explicit setting for production
            import secrets

            generated_key = secrets.token_urlsafe(32)
            print(
                f"WARNING: JWT_SECRET_KEY not set. Using generated key for development: {generated_key}"
            )
            return generated_key
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long")
        return v

    @field_validator("session_secret_key")
    @classmethod
    def validate_session_secret_key(cls, v):
        if not v:
            import secrets

            generated_key = secrets.token_urlsafe(32)
            print(
                f"WARNING: SESSION_SECRET_KEY not set. Using generated key for development: {generated_key}"
            )
            return generated_key
        if len(v) < 32:
            raise ValueError("SESSION_SECRET_KEY must be at least 32 characters long")
        return v

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError(v)

    # OAuth2 Configuration
    oauth2_client_id: Optional[str] = None
    oauth2_client_secret: Optional[str] = None
    oauth2_redirect_uri: str = "http://localhost:8000/auth/callback"

    # Email Configuration
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_tls: bool = True
    email_from: str = "noreply@simple-kanban.local"

    # File Upload Configuration
    max_upload_size: int = 10485760  # 10MB
    upload_path: str = "/app/uploads"

    # Rate Limiting
    rate_limit_per_minute: int = 100
    rate_limit_burst: int = 200

    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "json"

    # Monitoring Configuration
    enable_metrics: bool = True
    metrics_port: int = 9090

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False

    # Testing Configuration
    test_database_url: str = (
        "postgresql+asyncpg://kanban:kanban@localhost:5432/simple_kanban_test"
    )

    model_config = {"env_file": ".env", "case_sensitive": False, "env_prefix": ""}


# Global settings instance - lazy initialization
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Global settings instance for backward compatibility
settings = get_settings()
