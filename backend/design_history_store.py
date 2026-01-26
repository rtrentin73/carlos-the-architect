"""
Design history storage module for Carlos the Architect.

Stores design history persistently using Azure Cosmos DB, with in-memory fallback
for local development.

Uses the same Cosmos DB database as feedback but with a separate container for design history.
"""

import os
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from abc import ABC, abstractmethod


class DesignHistoryStoreBase(ABC):
    """Abstract base class for design history storage."""

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the storage backend."""
        pass

    @abstractmethod
    async def close(self):
        """Close the connection."""
        pass

    @abstractmethod
    async def save_design(self, username: str, design: dict) -> dict:
        """Save a design to history."""
        pass

    @abstractmethod
    async def get_user_designs(self, username: str, limit: int = 50) -> List[dict]:
        """Get all designs for a user."""
        pass

    @abstractmethod
    async def get_design(self, design_id: str, username: str) -> Optional[dict]:
        """Get a specific design by ID."""
        pass

    @abstractmethod
    async def delete_design(self, design_id: str, username: str) -> bool:
        """Delete a design from history."""
        pass

    @abstractmethod
    async def clear_user_history(self, username: str) -> int:
        """Clear all designs for a user. Returns count deleted."""
        pass

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to storage."""
        pass


class CosmosDBDesignHistoryStore(DesignHistoryStoreBase):
    """Persistent design history storage using Azure Cosmos DB."""

    def __init__(self):
        self._client = None
        self._database = None
        self._container = None
        self._connected = False

    async def connect(self) -> bool:
        """Connect to Azure Cosmos DB."""
        endpoint = os.getenv("COSMOSDB_ENDPOINT")
        key = os.getenv("COSMOSDB_KEY")
        database_name = os.getenv("COSMOSDB_DATABASE", "carlos-feedback")
        container_name = os.getenv("COSMOSDB_HISTORY_CONTAINER", "design_history")

        if not endpoint or not key:
            print("  COSMOSDB_ENDPOINT or COSMOSDB_KEY not set, Cosmos DB design history store disabled")
            return False

        try:
            from azure.cosmos.aio import CosmosClient
            from azure.cosmos import PartitionKey
            from azure.cosmos.exceptions import CosmosResourceNotFoundError

            self._client = CosmosClient(endpoint, credential=key)
            self._database = self._client.get_database_client(database_name)

            # Try to get container, create if it doesn't exist
            try:
                self._container = self._database.get_container_client(container_name)
                await self._container.read()
            except CosmosResourceNotFoundError:
                # Create the container with username as partition key
                print(f"  Creating design history container: {container_name}")
                self._container = await self._database.create_container(
                    id=container_name,
                    partition_key=PartitionKey(path="/username"),
                )

            self._connected = True
            print(f"  Connected to Cosmos DB for design history storage (container: {container_name})")
            return True
        except Exception as e:
            print(f"  Failed to connect to Cosmos DB for design history: {e}")
            self._connected = False
            return False

    async def close(self):
        """Close Cosmos DB connection."""
        if self._client:
            await self._client.close()
            self._connected = False

    async def save_design(self, username: str, design: dict) -> dict:
        """Save a design to history."""
        if not self._connected or not self._container:
            raise RuntimeError("Cosmos DB not connected")

        # Generate unique ID if not provided
        design_id = design.get("id") or str(uuid.uuid4())
        print(f"  💾 Saving design {design_id} to Cosmos DB for user {username}")

        # Build the document
        document = {
            "id": design_id,
            "type": "design_history",
            "username": username,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "requirements": design.get("requirements"),
            "cloud_provider": design.get("cloud_provider"),
            "environment": design.get("environment"),
            "architecture": design.get("architecture"),
            "terraform": design.get("terraform"),
            "diagram_svg": design.get("diagram_svg"),
            "cost_estimate": design.get("cost_estimate"),
            "security_analysis": design.get("security_analysis"),
            "reliability_analysis": design.get("reliability_analysis"),
            "title": design.get("title") or self._generate_title(design),
            # Additional fields from frontend
            "scenario": design.get("scenario"),
            "cost_performance": design.get("cost_performance"),
            "compliance_level": design.get("compliance_level"),
            "reliability_level": design.get("reliability_level"),
            "strictness_level": design.get("strictness_level"),
            "ronei_design": design.get("ronei_design"),
            "audit_status": design.get("audit_status"),
            "audit_report": design.get("audit_report"),
            "recommendation": design.get("recommendation"),
            "terraform_validation": design.get("terraform_validation"),
            "agent_chat": design.get("agent_chat"),
            "carlos_tokens": design.get("carlos_tokens"),
            "ronei_tokens": design.get("ronei_tokens"),
            "total_tokens": design.get("total_tokens"),
            "duration_seconds": design.get("duration_seconds"),
        }

        try:
            await self._container.create_item(body=document)
            print(f"  ✅ Design {design_id} saved to Cosmos DB")
            return self._cosmos_to_design_dict(document)
        except Exception as e:
            print(f"  ❌ Failed to save design {design_id}: {e}")
            import traceback
            traceback.print_exc()
            raise

    async def get_user_designs(self, username: str, limit: int = 50) -> List[dict]:
        """Get all designs for a user, ordered by creation date (newest first)."""
        if not self._connected or not self._container:
            print(f"  ⚠️ Design history store not connected, returning empty list")
            return []

        try:
            designs = []
            # Simple query without ORDER BY to avoid composite index requirements
            # We'll sort client-side
            query = """
                SELECT * FROM c
                WHERE c.username = @username AND c.type = 'design_history'
            """
            params = [
                {"name": "@username", "value": username},
            ]

            print(f"  📊 Querying designs for user: {username}")
            async for item in self._container.query_items(
                query=query,
                parameters=params,
            ):
                designs.append(self._cosmos_to_design_dict(item))

            # Sort by created_at descending (newest first) and apply limit
            designs.sort(key=lambda d: d.get("created_at", ""), reverse=True)
            designs = designs[:limit]

            print(f"  📊 Query returned {len(designs)} designs")
            return designs
        except Exception as e:
            print(f"  ❌ Error getting designs for user {username}: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def get_design(self, design_id: str, username: str) -> Optional[dict]:
        """Get a specific design by ID."""
        if not self._connected or not self._container:
            return None

        try:
            query = """
                SELECT * FROM c
                WHERE c.id = @design_id AND c.username = @username AND c.type = 'design_history'
            """
            params = [
                {"name": "@design_id", "value": design_id},
                {"name": "@username", "value": username},
            ]

            async for item in self._container.query_items(
                query=query,
                parameters=params,
            ):
                return self._cosmos_to_design_dict(item)
            return None
        except Exception as e:
            print(f"  Error getting design {design_id}: {e}")
            return None

    async def delete_design(self, design_id: str, username: str) -> bool:
        """Delete a design from history."""
        if not self._connected or not self._container:
            return False

        try:
            # First verify the design exists and belongs to user
            design = await self.get_design(design_id, username)
            if not design:
                return False

            await self._container.delete_item(
                item=design_id,
                partition_key=username,
            )
            return True
        except Exception as e:
            print(f"  Error deleting design {design_id}: {e}")
            return False

    async def clear_user_history(self, username: str) -> int:
        """Clear all designs for a user. Returns count deleted."""
        if not self._connected or not self._container:
            return 0

        try:
            # Get all designs for user
            designs = await self.get_user_designs(username, limit=1000)
            count = 0

            for design in designs:
                try:
                    await self._container.delete_item(
                        item=design["id"],
                        partition_key=username,
                    )
                    count += 1
                except Exception:
                    pass

            return count
        except Exception as e:
            print(f"  Error clearing history for user {username}: {e}")
            return 0

    def _generate_title(self, design: dict) -> str:
        """Generate a title from design requirements."""
        requirements = design.get("requirements", "")
        if isinstance(requirements, str) and requirements:
            # Take first 50 chars of requirements as title
            title = requirements[:50]
            if len(requirements) > 50:
                title += "..."
            return title
        return "Untitled Design"

    def _cosmos_to_design_dict(self, item: dict) -> dict:
        """Convert Cosmos DB document to design dict."""
        return {
            "id": item.get("id"),
            "username": item.get("username"),
            "created_at": item.get("created_at"),
            "requirements": item.get("requirements"),
            "cloud_provider": item.get("cloud_provider"),
            "environment": item.get("environment"),
            "architecture": item.get("architecture"),
            "terraform": item.get("terraform"),
            "diagram_svg": item.get("diagram_svg"),
            "cost_estimate": item.get("cost_estimate"),
            "security_analysis": item.get("security_analysis"),
            "reliability_analysis": item.get("reliability_analysis"),
            "title": item.get("title"),
            # Additional fields from frontend
            "scenario": item.get("scenario"),
            "cost_performance": item.get("cost_performance"),
            "compliance_level": item.get("compliance_level"),
            "reliability_level": item.get("reliability_level"),
            "strictness_level": item.get("strictness_level"),
            "ronei_design": item.get("ronei_design"),
            "audit_status": item.get("audit_status"),
            "audit_report": item.get("audit_report"),
            "recommendation": item.get("recommendation"),
            "terraform_validation": item.get("terraform_validation"),
            "agent_chat": item.get("agent_chat"),
            "carlos_tokens": item.get("carlos_tokens"),
            "ronei_tokens": item.get("ronei_tokens"),
            "total_tokens": item.get("total_tokens"),
            "duration_seconds": item.get("duration_seconds"),
        }

    @property
    def is_connected(self) -> bool:
        return self._connected


class InMemoryDesignHistoryStore(DesignHistoryStoreBase):
    """In-memory design history storage for local development."""

    def __init__(self):
        # Store designs by username -> list of designs
        self._designs: dict[str, list[dict]] = {}

    async def connect(self) -> bool:
        print("  Using in-memory design history store (Cosmos DB not configured)")
        return True

    async def close(self):
        pass

    async def save_design(self, username: str, design: dict) -> dict:
        """Save a design to history."""
        design_id = design.get("id") or str(uuid.uuid4())

        design_doc = {
            "id": design_id,
            "username": username,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "requirements": design.get("requirements"),
            "cloud_provider": design.get("cloud_provider"),
            "environment": design.get("environment"),
            "architecture": design.get("architecture"),
            "terraform": design.get("terraform"),
            "diagram_svg": design.get("diagram_svg"),
            "cost_estimate": design.get("cost_estimate"),
            "security_analysis": design.get("security_analysis"),
            "reliability_analysis": design.get("reliability_analysis"),
            "title": design.get("title") or self._generate_title(design),
            # Additional fields from frontend
            "scenario": design.get("scenario"),
            "cost_performance": design.get("cost_performance"),
            "compliance_level": design.get("compliance_level"),
            "reliability_level": design.get("reliability_level"),
            "strictness_level": design.get("strictness_level"),
            "ronei_design": design.get("ronei_design"),
            "audit_status": design.get("audit_status"),
            "audit_report": design.get("audit_report"),
            "recommendation": design.get("recommendation"),
            "terraform_validation": design.get("terraform_validation"),
            "agent_chat": design.get("agent_chat"),
            "carlos_tokens": design.get("carlos_tokens"),
            "ronei_tokens": design.get("ronei_tokens"),
            "total_tokens": design.get("total_tokens"),
            "duration_seconds": design.get("duration_seconds"),
        }

        if username not in self._designs:
            self._designs[username] = []

        self._designs[username].insert(0, design_doc)  # Insert at beginning (newest first)
        return design_doc

    async def get_user_designs(self, username: str, limit: int = 50) -> List[dict]:
        """Get all designs for a user."""
        designs = self._designs.get(username, [])
        return designs[:limit]

    async def get_design(self, design_id: str, username: str) -> Optional[dict]:
        """Get a specific design by ID."""
        designs = self._designs.get(username, [])
        for design in designs:
            if design["id"] == design_id:
                return design
        return None

    async def delete_design(self, design_id: str, username: str) -> bool:
        """Delete a design from history."""
        if username not in self._designs:
            return False

        designs = self._designs[username]
        for i, design in enumerate(designs):
            if design["id"] == design_id:
                designs.pop(i)
                return True
        return False

    async def clear_user_history(self, username: str) -> int:
        """Clear all designs for a user."""
        if username not in self._designs:
            return 0
        count = len(self._designs[username])
        self._designs[username] = []
        return count

    def _generate_title(self, design: dict) -> str:
        """Generate a title from design requirements."""
        requirements = design.get("requirements", "")
        if isinstance(requirements, str) and requirements:
            title = requirements[:50]
            if len(requirements) > 50:
                title += "..."
            return title
        return "Untitled Design"

    @property
    def is_connected(self) -> bool:
        return False  # Indicates not connected to persistent storage


# Global design history store instance
_design_history_store: Optional[DesignHistoryStoreBase] = None


async def initialize_design_history_store() -> DesignHistoryStoreBase:
    """Initialize the design history store - tries Cosmos DB first, falls back to in-memory."""
    global _design_history_store

    # Try Cosmos DB first
    cosmos_store = CosmosDBDesignHistoryStore()
    if await cosmos_store.connect():
        _design_history_store = cosmos_store
        print("📚 Design history: Using Cosmos DB (persistent storage)")
        return _design_history_store

    # Fall back to in-memory
    _design_history_store = InMemoryDesignHistoryStore()
    await _design_history_store.connect()
    print("📚 Design history: Using in-memory store (⚠️ data will be lost on restart)")
    return _design_history_store


async def close_design_history_store():
    """Close the design history store connection."""
    global _design_history_store
    if _design_history_store:
        await _design_history_store.close()


def get_design_history_store() -> DesignHistoryStoreBase:
    """Get the global design history store instance."""
    global _design_history_store
    if _design_history_store is None:
        raise RuntimeError("Design history store not initialized. Call initialize_design_history_store() first.")
    return _design_history_store
