"""
Security middleware for Simple Kanban Board application.

Provides rate limiting, security headers, and CSRF protection.
"""

import time
from typing import Dict, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import redis.asyncio as redis
from ..core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using sliding window algorithm."""

    def __init__(self, app: ASGIApp, redis_client: Optional[redis.Redis] = None):
        super().__init__(app)
        self.redis_client = redis_client
        self.memory_store: Dict[str, Dict] = (
            {}
        )  # Fallback for when Redis is unavailable

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and static files
        if request.url.path in ["/health", "/metrics"] or request.url.path.startswith(
            "/static"
        ):
            return await call_next(request)

        client_ip = self._get_client_ip(request)

        # Check rate limit
        if await self._is_rate_limited(client_ip):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": 60,
                },
                headers={"Retry-After": "60"},
            )

        response = await call_next(request)
        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request headers."""
        # Check for forwarded headers first (for reverse proxy setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    async def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if client IP is rate limited using sliding window."""
        current_time = int(time.time())
        window_start = current_time - 60  # 1-minute window

        if self.redis_client:
            try:
                return await self._redis_rate_limit(
                    client_ip, current_time, window_start
                )
            except Exception:
                # Fall back to memory store if Redis fails
                pass

        return self._memory_rate_limit(client_ip, current_time, window_start)

    async def _redis_rate_limit(
        self, client_ip: str, current_time: int, window_start: int
    ) -> bool:
        """Redis-based rate limiting."""
        key = f"rate_limit:{client_ip}"

        # Remove old entries
        await self.redis_client.zremrangebyscore(key, 0, window_start)

        # Count current requests
        current_requests = await self.redis_client.zcard(key)

        if current_requests >= settings.rate_limit_per_minute:
            return True

        # Add current request
        await self.redis_client.zadd(key, {str(current_time): current_time})
        await self.redis_client.expire(key, 60)

        return False

    def _memory_rate_limit(
        self, client_ip: str, current_time: int, window_start: int
    ) -> bool:
        """Memory-based rate limiting fallback."""
        if client_ip not in self.memory_store:
            self.memory_store[client_ip] = {"requests": []}

        client_data = self.memory_store[client_ip]

        # Remove old requests
        client_data["requests"] = [
            req_time for req_time in client_data["requests"] if req_time > window_start
        ]

        if len(client_data["requests"]) >= settings.rate_limit_per_minute:
            return True

        # Add current request
        client_data["requests"].append(current_time)
        return False


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if not settings.security_headers_enabled:
            return response

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        # Content Security Policy - relaxed for Swagger UI
        # Skip CSP for docs endpoints to allow Swagger UI to function
        if request.url.path in ["/docs", "/redoc"] or request.url.path.startswith(
            "/openapi"
        ):
            # More permissive CSP for API documentation
            csp_policy = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
                "font-src 'self' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
                "img-src 'self' data: https:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        else:
            # Strict CSP for application endpoints
            csp_policy = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
                "font-src 'self' https://cdnjs.cloudflare.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        response.headers["Content-Security-Policy"] = csp_policy

        # HSTS for production
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """CSRF protection for state-changing operations."""

    SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}
    EXEMPT_PATHS = {
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/oidc/callback",
        "/api/oidc/auth/google",
        "/api/oidc/callback/google",
        "/api/auth/login",
        "/api/auth/register",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    async def dispatch(self, request: Request, call_next):
        if not settings.csrf_protection_enabled:
            return await call_next(request)

        # Skip CSRF for safe methods and exempt paths
        if (
            request.method in self.SAFE_METHODS
            or request.url.path in self.EXEMPT_PATHS
            or request.url.path.startswith("/static")
        ):
            return await call_next(request)

        # For authenticated requests, skip CSRF validation for now
        # This allows the existing frontend to work while we implement proper CSRF tokens
        auth_header = request.headers.get("Authorization")
        print(
            f"CSRF Debug - Path: {request.url.path}, Method: {request.method}, Auth Header: {auth_header}"
        )
        if auth_header and auth_header.startswith("Bearer "):
            print("CSRF Debug - Skipping CSRF for Bearer token")
            return await call_next(request)

        # Check for CSRF token in headers
        csrf_token = request.headers.get("X-CSRF-Token")
        if not csrf_token:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "CSRF token missing"},
            )

        # For now, we'll implement a simple token validation
        # In production, you'd want to validate against a stored token
        if not self._validate_csrf_token(csrf_token):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Invalid CSRF token"},
            )

        return await call_next(request)

    def _validate_csrf_token(self, token: str) -> bool:
        """Validate CSRF token. Simplified implementation."""
        # In a real implementation, you'd validate against a stored token
        # For now, just check that it's not empty and has minimum length
        return len(token) >= 16


def setup_redis_client() -> Optional[redis.Redis]:
    """Setup Redis client for rate limiting."""
    try:
        client = redis.from_url(settings.redis_url)
        return client
    except Exception as e:
        print(f"Warning: Could not connect to Redis for rate limiting: {e}")
        return None
