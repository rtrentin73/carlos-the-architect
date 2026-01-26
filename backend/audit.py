"""
Production audit logging module for Carlos the Architect.

Tracks all significant user actions for compliance and operational visibility:
- Authentication events (login, logout, registration)
- Design operations (requests, cache hits, completions)
- Document uploads and processing
- Feedback submissions
- Admin operations

Uses Azure Cosmos DB for persistent storage, falls back to in-memory for local development.
"""

import os
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class AuditAction(str, Enum):
    """Categorized audit action types."""
    # Authentication
    AUTH_LOGIN_SUCCESS = "auth.login.success"
    AUTH_LOGIN_FAILURE = "auth.login.failure"
    AUTH_LOGOUT = "auth.logout"
    AUTH_REGISTER = "auth.register"

    # Design operations
    DESIGN_REQUEST = "design.request"
    DESIGN_STREAM_START = "design.stream.start"
    DESIGN_STREAM_COMPLETE = "design.stream.complete"
    DESIGN_CACHE_HIT = "design.cache.hit"
    DESIGN_CACHE_MISS = "design.cache.miss"

    # Document operations
    DOCUMENT_UPLOAD = "document.upload"
    DOCUMENT_PROCESS_START = "document.process.start"
    DOCUMENT_PROCESS_COMPLETE = "document.process.complete"
    DOCUMENT_PROCESS_FAILED = "document.process.failed"
    DOCUMENT_ACCESS = "document.access"

    # Feedback operations
    FEEDBACK_SUBMIT = "feedback.submit"
    FEEDBACK_VIEW = "feedback.view"

    # Cache operations
    CACHE_CLEAR = "cache.clear"
    CACHE_STATS_VIEW = "cache.stats.view"

    # Admin operations
    ADMIN_AUDIT_QUERY = "admin.audit.query"
    ADMIN_AUDIT_EXPORT = "admin.audit.export"

    # Rate limiting
    RATE_LIMIT_EXCEEDED = "rate_limit.exceeded"

    # Errors
    ERROR_INTERNAL = "error.internal"
    ERROR_VALIDATION = "error.validation"
    ERROR_UNAUTHORIZED = "error.unauthorized"


class AuditSeverity(str, Enum):
    """Severity level for audit events."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditRecord(BaseModel):
    """Immutable audit record for compliance tracking."""
    audit_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    username: Optional[str] = Field(default=None, description="Authenticated username")
    user_ip: Optional[str] = Field(default=None, description="Client IP address")
    user_agent: Optional[str] = Field(default=None, description="Client user agent")
    action: AuditAction = Field(description="Categorized action type")
    severity: AuditSeverity = Field(default=AuditSeverity.INFO)
    endpoint: str = Field(description="API endpoint path")
    method: str = Field(description="HTTP method")
    request_id: Optional[str] = Field(default=None, description="Correlation ID")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    status_code: Optional[int] = Field(default=None)
    duration_ms: Optional[float] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    error_type: Optional[str] = Field(default=None)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AuditQueryParams(BaseModel):
    """Parameters for querying audit logs."""
    username: Optional[str] = None
    action: Optional[AuditAction] = None
    action_prefix: Optional[str] = None
    severity: Optional[AuditSeverity] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    endpoint: Optional[str] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)


class CosmosDBauditStore:
    """Distributed audit storage using Azure Cosmos DB."""

    def __init__(self):
        self._client = None
        self._database = None
        self._container = None
        self._connected = False

    async def connect(self):
        """Connect to Azure Cosmos DB audit container."""
        endpoint = os.getenv("COSMOSDB_ENDPOINT")
        key = os.getenv("COSMOSDB_KEY")
        database_name = os.getenv("COSMOSDB_DATABASE", "carlos-feedback")
        container_name = os.getenv("COSMOSDB_AUDIT_CONTAINER", "audit_logs")

        if not endpoint or not key:
            print("  COSMOSDB_ENDPOINT or COSMOSDB_KEY not set, Cosmos DB audit store disabled")
            return False

        try:
            from azure.cosmos.aio import CosmosClient
            from azure.cosmos import PartitionKey

            self._client = CosmosClient(endpoint, credential=key)
            self._database = self._client.get_database_client(database_name)

            # Create container if not exists (partition by month)
            try:
                self._container = await self._database.create_container_if_not_exists(
                    id=container_name,
                    partition_key=PartitionKey(path="/_partition_key"),
                    default_ttl=int(os.getenv("AUDIT_RETENTION_DAYS", "365")) * 24 * 60 * 60
                )
            except Exception:
                self._container = self._database.get_container_client(container_name)

            # Test connection
            await self._container.read()

            self._connected = True
            print(f"  Connected to Cosmos DB for audit storage (container: {container_name})")
            return True
        except Exception as e:
            print(f"  Failed to connect to Cosmos DB for audit: {e}")
            self._connected = False
            return False

    async def close(self):
        """Close Cosmos DB connection."""
        if self._client:
            await self._client.close()
            self._connected = False

    async def log(self, record: AuditRecord) -> str:
        """Write an immutable audit record."""
        if not self._connected or not self._container:
            raise RuntimeError("Audit store not connected")

        # Generate partition key from timestamp (YYYY-MM format)
        partition_key = record.timestamp.strftime("%Y-%m")

        document = {
            "id": record.audit_id,
            "audit_id": record.audit_id,
            "timestamp": record.timestamp.isoformat(),
            "username": record.username,
            "user_ip": record.user_ip,
            "user_agent": record.user_agent,
            "action": record.action.value,
            "severity": record.severity.value,
            "endpoint": record.endpoint,
            "method": record.method,
            "request_id": record.request_id,
            "metadata": record.metadata,
            "status_code": record.status_code,
            "duration_ms": record.duration_ms,
            "error_message": record.error_message,
            "error_type": record.error_type,
            "_partition_key": partition_key,
            "type": "audit_record",
        }

        await self._container.create_item(body=document)
        return record.audit_id

    async def query(self, params: AuditQueryParams) -> List[AuditRecord]:
        """Query audit records with filters."""
        if not self._connected or not self._container:
            return []

        conditions = ["c.type = 'audit_record'"]
        query_params = []

        if params.username:
            conditions.append("c.username = @username")
            query_params.append({"name": "@username", "value": params.username})

        if params.action:
            conditions.append("c.action = @action")
            query_params.append({"name": "@action", "value": params.action.value})

        if params.action_prefix:
            conditions.append("STARTSWITH(c.action, @action_prefix)")
            query_params.append({"name": "@action_prefix", "value": params.action_prefix})

        if params.severity:
            conditions.append("c.severity = @severity")
            query_params.append({"name": "@severity", "value": params.severity.value})

        if params.start_date:
            conditions.append("c.timestamp >= @start_date")
            query_params.append({"name": "@start_date", "value": params.start_date.isoformat()})

        if params.end_date:
            conditions.append("c.timestamp <= @end_date")
            query_params.append({"name": "@end_date", "value": params.end_date.isoformat()})

        if params.endpoint:
            conditions.append("c.endpoint = @endpoint")
            query_params.append({"name": "@endpoint", "value": params.endpoint})

        query = f"""
            SELECT * FROM c
            WHERE {' AND '.join(conditions)}
            ORDER BY c.timestamp DESC
            OFFSET @offset LIMIT @limit
        """
        query_params.extend([
            {"name": "@offset", "value": params.offset},
            {"name": "@limit", "value": params.limit}
        ])

        results = []
        try:
            async for item in self._container.query_items(
                query=query,
                parameters=query_params
            ):
                # Convert to AuditRecord
                item.pop("_partition_key", None)
                item.pop("_rid", None)
                item.pop("_self", None)
                item.pop("_etag", None)
                item.pop("_attachments", None)
                item.pop("_ts", None)
                item.pop("type", None)
                item.pop("id", None)

                # Convert string enums back to enum types
                item["action"] = AuditAction(item["action"])
                item["severity"] = AuditSeverity(item["severity"])
                item["timestamp"] = datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00"))

                results.append(AuditRecord(**item))
        except Exception as e:
            print(f"  Error querying audit logs: {e}")

        return results

    async def get_stats(self, days: int = 30) -> dict:
        """Get aggregate audit statistics for dashboard."""
        if not self._connected or not self._container:
            return self._empty_stats()

        try:
            # Calculate date range
            end_date = datetime.now(timezone.utc)
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            from datetime import timedelta
            start_date = start_date - timedelta(days=days)

            # Total events (cross-partition aggregate)
            total_query = f"""
                SELECT VALUE COUNT(1) FROM c
                WHERE c.type = 'audit_record'
                AND c.timestamp >= '{start_date.isoformat()}'
            """
            total_events = 0
            async for item in self._container.query_items(
                query=total_query
            ):
                total_events = item

            # For GROUP BY queries, use client-side aggregation due to cross-partition limitations
            # Fetch all records and aggregate locally
            base_query = f"""
                SELECT c.action, c.severity, c.username FROM c
                WHERE c.type = 'audit_record'
                AND c.timestamp >= '{start_date.isoformat()}'
            """
            action_counts = {}
            severity_counts = {}
            unique_usernames = set()

            async for item in self._container.query_items(
                query=base_query
            ):
                # Count by action
                action = item.get("action")
                if action:
                    action_counts[action] = action_counts.get(action, 0) + 1

                # Count by severity
                severity = item.get("severity")
                if severity:
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1

                # Track unique users
                username = item.get("username")
                if username:
                    unique_usernames.add(username)

            unique_users = len(unique_usernames)

            # Error count
            error_count = severity_counts.get("error", 0) + severity_counts.get("critical", 0)

            return {
                "total_events": total_events,
                "unique_users": unique_users,
                "error_count": error_count,
                "events_by_action": action_counts,
                "events_by_severity": severity_counts,
                "period_days": days,
                "connected": True,
                "storage": "cosmosdb",
            }
        except Exception as e:
            print(f"  Error getting audit stats: {e}")
            return self._empty_stats()

    def _empty_stats(self) -> dict:
        """Return empty stats structure."""
        return {
            "total_events": 0,
            "unique_users": 0,
            "error_count": 0,
            "events_by_action": {},
            "events_by_severity": {},
            "period_days": 0,
            "connected": False,
            "storage": "none",
        }

    @property
    def is_connected(self) -> bool:
        return self._connected


class InMemoryAuditStore:
    """Fallback in-memory audit storage for local development."""

    def __init__(self, max_records: int = 10000):
        self._records: List[AuditRecord] = []
        self._max_records = max_records

    async def connect(self):
        print("  Using in-memory audit store (Cosmos DB not configured)")
        return True

    async def close(self):
        pass

    async def log(self, record: AuditRecord) -> str:
        """Write audit record to memory."""
        self._records.append(record)
        # Trim if over limit (FIFO)
        if len(self._records) > self._max_records:
            self._records = self._records[-self._max_records:]
        return record.audit_id

    async def query(self, params: AuditQueryParams) -> List[AuditRecord]:
        """Query in-memory records."""
        results = self._records.copy()

        if params.username:
            results = [r for r in results if r.username == params.username]
        if params.action:
            results = [r for r in results if r.action == params.action]
        if params.action_prefix:
            results = [r for r in results if r.action.value.startswith(params.action_prefix)]
        if params.severity:
            results = [r for r in results if r.severity == params.severity]
        if params.start_date:
            results = [r for r in results if r.timestamp >= params.start_date]
        if params.end_date:
            results = [r for r in results if r.timestamp <= params.end_date]
        if params.endpoint:
            results = [r for r in results if r.endpoint == params.endpoint]

        # Sort by timestamp descending
        results.sort(key=lambda r: r.timestamp, reverse=True)

        # Apply pagination
        return results[params.offset:params.offset + params.limit]

    async def get_stats(self, days: int = 30) -> dict:
        """Get aggregate statistics from in-memory records."""
        from datetime import timedelta

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # Filter by date range
        recent = [r for r in self._records if r.timestamp >= start_date]

        # Count by action
        action_counts = {}
        for r in recent:
            action_counts[r.action.value] = action_counts.get(r.action.value, 0) + 1

        # Count by severity
        severity_counts = {}
        for r in recent:
            severity_counts[r.severity.value] = severity_counts.get(r.severity.value, 0) + 1

        # Unique users
        unique_users = len(set(r.username for r in recent if r.username))

        # Error count
        error_count = severity_counts.get("error", 0) + severity_counts.get("critical", 0)

        return {
            "total_events": len(recent),
            "unique_users": unique_users,
            "error_count": error_count,
            "events_by_action": action_counts,
            "events_by_severity": severity_counts,
            "period_days": days,
            "connected": False,
            "storage": "in-memory",
        }

    @property
    def is_connected(self) -> bool:
        return False


# Global audit store instance
_audit_store = None


async def initialize_audit_store():
    """Initialize the audit store - tries Cosmos DB first, falls back to in-memory."""
    global _audit_store

    # Try Cosmos DB first
    cosmos_store = CosmosDBauditStore()
    if await cosmos_store.connect():
        _audit_store = cosmos_store
        return _audit_store

    # Fall back to in-memory
    _audit_store = InMemoryAuditStore()
    await _audit_store.connect()
    return _audit_store


async def close_audit_store():
    """Close the audit store connection."""
    global _audit_store
    if _audit_store:
        await _audit_store.close()


def get_audit_store():
    """Get the global audit store instance."""
    global _audit_store
    if _audit_store is None:
        raise RuntimeError("Audit store not initialized. Call initialize_audit_store() first.")
    return _audit_store
