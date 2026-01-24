"""
Audit logging middleware for Carlos the Architect.

Automatically captures request/response metadata for all endpoints.
Logs to the AuditStore for compliance and operational visibility.
"""

import time
import uuid
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from audit import (
    AuditRecord,
    AuditAction,
    AuditSeverity,
    get_audit_store,
)


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware that logs all significant requests to the audit system."""

    # Endpoints to skip (health checks, documentation, static)
    SKIP_ENDPOINTS = {
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/favicon.ico",
    }

    # Map (method, endpoint) to audit actions
    ENDPOINT_ACTIONS = {
        # Authentication
        ("POST", "/auth/login"): AuditAction.AUTH_LOGIN_SUCCESS,
        ("POST", "/auth/register"): AuditAction.AUTH_REGISTER,
        ("POST", "/auth/logout"): AuditAction.AUTH_LOGOUT,

        # Design operations
        ("POST", "/design"): AuditAction.DESIGN_REQUEST,
        ("POST", "/design-stream"): AuditAction.DESIGN_STREAM_START,

        # Document operations
        ("POST", "/upload-document"): AuditAction.DOCUMENT_UPLOAD,
        ("GET", "/documents"): AuditAction.DOCUMENT_ACCESS,

        # Feedback operations
        ("POST", "/feedback/deployment"): AuditAction.FEEDBACK_SUBMIT,
        ("GET", "/feedback/my-feedback"): AuditAction.FEEDBACK_VIEW,
        ("GET", "/feedback/analytics"): AuditAction.FEEDBACK_VIEW,

        # Cache operations
        ("GET", "/cache/stats"): AuditAction.CACHE_STATS_VIEW,
        ("POST", "/cache/clear"): AuditAction.CACHE_CLEAR,

        # Admin operations
        ("GET", "/admin/audit"): AuditAction.ADMIN_AUDIT_QUERY,
        ("GET", "/admin/audit/export"): AuditAction.ADMIN_AUDIT_EXPORT,
        ("GET", "/admin/audit/stats"): AuditAction.ADMIN_AUDIT_QUERY,
    }

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip non-significant endpoints
        path = request.url.path
        if path in self.SKIP_ENDPOINTS:
            return await call_next(request)

        # Skip static files and paths starting with underscore
        if path.startswith("/_") or path.startswith("/static"):
            return await call_next(request)

        # Generate request ID for correlation
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        # Capture start time
        start_time = time.perf_counter()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Determine action type
        action = self._get_action_for_request(request)
        if action is None:
            # Skip logging for unmapped endpoints
            return response

        # Extract user info (set by auth dependency if authenticated)
        username = self._get_username(request)

        # Determine severity based on status code
        severity = self._get_severity(response.status_code)

        # Handle special cases
        if action == AuditAction.AUTH_LOGIN_SUCCESS and response.status_code == 401:
            action = AuditAction.AUTH_LOGIN_FAILURE
            severity = AuditSeverity.WARNING

        # Build error info if applicable
        error_message = None
        error_type = None
        if response.status_code >= 400:
            if response.status_code == 401:
                error_type = "unauthorized"
                error_message = "Authentication required or failed"
            elif response.status_code == 403:
                error_type = "forbidden"
                error_message = "Access denied"
            elif response.status_code == 404:
                error_type = "not_found"
                error_message = "Resource not found"
            elif response.status_code == 422:
                error_type = "validation_error"
                error_message = "Request validation failed"
            elif response.status_code == 429:
                error_type = "rate_limited"
                error_message = "Rate limit exceeded"
                action = AuditAction.RATE_LIMIT_EXCEEDED
            elif response.status_code >= 500:
                error_type = "internal_error"
                error_message = "Internal server error"

        # Build audit record
        record = AuditRecord(
            username=username,
            user_ip=self._get_client_ip(request),
            user_agent=self._truncate(request.headers.get("user-agent", ""), 200),
            action=action,
            severity=severity,
            endpoint=path,
            method=request.method,
            request_id=request_id,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            error_message=error_message,
            error_type=error_type,
            metadata=self._build_metadata(request),
        )

        # Log asynchronously (fire and forget - never block the response)
        try:
            store = get_audit_store()
            await store.log(record)
        except Exception as e:
            # Never let audit failures break the request
            print(f"  Audit log error (non-fatal): {e}")

        return response

    def _get_action_for_request(self, request: Request) -> Optional[AuditAction]:
        """Determine the audit action for this request."""
        path = request.url.path
        method = request.method

        # Direct mapping
        action = self.ENDPOINT_ACTIONS.get((method, path))
        if action:
            return action

        # Dynamic path patterns
        if path.startswith("/documents/") and method == "GET":
            return AuditAction.DOCUMENT_ACCESS

        if path.startswith("/admin/audit"):
            if method == "GET":
                return AuditAction.ADMIN_AUDIT_QUERY

        # For other authenticated endpoints, log as generic request
        if method in ("POST", "PUT", "DELETE", "PATCH"):
            return AuditAction.DESIGN_REQUEST

        return None

    def _get_username(self, request: Request) -> Optional[str]:
        """Extract username from request state (set by auth dependency)."""
        if hasattr(request.state, "user") and request.state.user:
            return getattr(request.state.user, "username", None)
        return None

    def _get_severity(self, status_code: int) -> AuditSeverity:
        """Determine severity based on HTTP status code."""
        if status_code >= 500:
            return AuditSeverity.ERROR
        elif status_code >= 400:
            return AuditSeverity.WARNING
        return AuditSeverity.INFO

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP, handling proxies."""
        # Check X-Forwarded-For header (set by load balancers/proxies)
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            # Take the first IP in the chain (original client)
            return forwarded.split(",")[0].strip()

        # Check X-Real-IP header (nginx)
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()

        # Fall back to direct client connection
        if request.client:
            return request.client.host

        return "unknown"

    def _build_metadata(self, request: Request) -> dict:
        """Build sanitized metadata from request."""
        metadata = {}

        # Add safe query params (exclude sensitive ones)
        sensitive_params = {"password", "token", "secret", "key", "api_key", "apikey"}
        for key, value in request.query_params.items():
            if key.lower() not in sensitive_params:
                metadata[f"query_{key}"] = self._truncate(value, 100)

        return metadata

    def _truncate(self, value: str, max_length: int) -> str:
        """Truncate a string to max length."""
        if len(value) <= max_length:
            return value
        return value[:max_length] + "..."
