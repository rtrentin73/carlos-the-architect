"""
Rate limiting middleware for Carlos the Architect.

Provides per-user rate limiting to prevent abuse and protect Azure OpenAI quotas.
Uses in-memory storage by default, can be upgraded to Redis for distributed deployments.
"""

import os
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException
from starlette.responses import JSONResponse

# Rate limit configurations per endpoint
RATE_LIMITS = {
    "design": "10/hour",          # 10 designs per hour per user
    "design_stream": "10/hour",   # Same for streaming endpoint
    "upload": "30/hour",          # 30 document uploads per hour
    "auth": "20/minute",          # 20 auth attempts per minute (brute force protection)
}


def get_user_identifier(request: Request) -> str:
    """
    Get unique identifier for rate limiting.
    Uses authenticated username if available, otherwise falls back to IP.
    """
    # Try to get user from request state (set by auth middleware)
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.username}"

    # Check for Authorization header to extract user
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        # Use token hash as identifier (rate limit per token)
        token = auth_header[7:]
        return f"token:{hash(token) % 1000000}"

    # Fall back to IP address
    return f"ip:{get_remote_address(request)}"


# Initialize limiter with custom key function
limiter = Limiter(key_func=get_user_identifier)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom handler for rate limit exceeded errors."""
    # Parse the limit string to provide useful info
    limit_str = str(exc.detail) if hasattr(exc, 'detail') else "Rate limit exceeded"

    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": limit_str,
            "message": "You've made too many requests. Please wait before trying again.",
            "retry_after": "See Retry-After header"
        },
        headers={
            "Retry-After": "60",  # Suggest retry after 60 seconds
            "X-RateLimit-Limit": limit_str,
        }
    )


# Export commonly used limits as decorators
def design_limit():
    """Rate limit decorator for design endpoints."""
    return limiter.limit(RATE_LIMITS["design"])


def upload_limit():
    """Rate limit decorator for upload endpoints."""
    return limiter.limit(RATE_LIMITS["upload"])


def auth_limit():
    """Rate limit decorator for auth endpoints."""
    return limiter.limit(RATE_LIMITS["auth"])
