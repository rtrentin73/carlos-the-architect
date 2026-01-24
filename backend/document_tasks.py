"""
Document processing task management.

Handles asynchronous document upload and text extraction.
Uses in-memory storage (can be migrated to Redis/Cosmos for production).
"""

from enum import Enum
from typing import Optional, Dict
from datetime import datetime, timezone
import uuid


class TaskStatus(str, Enum):
    """Document processing task status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentTask:
    """Represents a document processing task"""

    def __init__(self, task_id: str, filename: str, username: str):
        self.task_id = task_id
        self.filename = filename
        self.username = username
        self.status = TaskStatus.PENDING
        self.extracted_text: Optional[str] = None
        self.error: Optional[str] = None
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self.file_size: Optional[int] = None

    def to_dict(self) -> dict:
        """Convert task to dictionary for API responses"""
        return {
            "task_id": self.task_id,
            "filename": self.filename,
            "status": self.status.value,
            "extracted_text": self.extracted_text if self.status == TaskStatus.COMPLETED else None,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "file_size": self.file_size
        }

    def update_status(self, status: TaskStatus, error: Optional[str] = None, extracted_text: Optional[str] = None):
        """Update task status and timestamp"""
        self.status = status
        self.updated_at = datetime.now(timezone.utc)
        if error:
            self.error = error
        if extracted_text:
            self.extracted_text = extracted_text


# In-memory task storage
# TODO: Migrate to Redis or Azure Cosmos DB for production multi-instance deployments
_tasks: Dict[str, DocumentTask] = {}


def create_task(filename: str, username: str, file_size: int) -> DocumentTask:
    """Create a new document processing task"""
    task_id = str(uuid.uuid4())
    task = DocumentTask(task_id, filename, username)
    task.file_size = file_size
    _tasks[task_id] = task
    return task


def get_task(task_id: str) -> Optional[DocumentTask]:
    """Retrieve task by ID"""
    return _tasks.get(task_id)


def get_user_tasks(username: str, limit: int = 10) -> list[DocumentTask]:
    """Get recent tasks for a user"""
    user_tasks = [task for task in _tasks.values() if task.username == username]
    # Sort by creation time, newest first
    user_tasks.sort(key=lambda t: t.created_at, reverse=True)
    return user_tasks[:limit]


def cleanup_old_tasks(max_age_hours: int = 24):
    """Clean up tasks older than max_age_hours (for memory management)"""
    now = datetime.now(timezone.utc)
    to_delete = []

    for task_id, task in _tasks.items():
        age_hours = (now - task.created_at).total_seconds() / 3600
        if age_hours > max_age_hours:
            to_delete.append(task_id)

    for task_id in to_delete:
        del _tasks[task_id]

    return len(to_delete)
