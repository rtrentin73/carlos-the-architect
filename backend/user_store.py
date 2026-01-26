"""
User storage module for Carlos the Architect.

Stores user accounts persistently using Azure Cosmos DB, with in-memory fallback
for local development.

Uses the same Cosmos DB database as feedback but with a separate container for users.
"""

import os
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from abc import ABC, abstractmethod


class UserStoreBase(ABC):
    """Abstract base class for user storage."""

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the storage backend."""
        pass

    @abstractmethod
    async def close(self):
        """Close the connection."""
        pass

    @abstractmethod
    async def get_user(self, username: str) -> Optional[dict]:
        """Get a user by username."""
        pass

    @abstractmethod
    async def get_user_by_oauth(self, provider: str, oauth_id: str) -> Optional[dict]:
        """Get a user by OAuth provider and ID."""
        pass

    @abstractmethod
    async def create_user(self, user_dict: dict) -> dict:
        """Create a new user."""
        pass

    @abstractmethod
    async def update_user(self, username: str, updates: dict) -> Optional[dict]:
        """Update user fields."""
        pass

    @abstractmethod
    async def username_exists(self, username: str) -> bool:
        """Check if username already exists."""
        pass

    @abstractmethod
    async def get_all_users(self) -> List[dict]:
        """Get all users (for admin)."""
        pass

    @abstractmethod
    async def delete_user(self, username: str) -> bool:
        """Delete a user by username. Returns True if deleted, False if not found."""
        pass

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to storage."""
        pass


class CosmosDBUserStore(UserStoreBase):
    """Persistent user storage using Azure Cosmos DB."""

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
        container_name = os.getenv("COSMOSDB_USERS_CONTAINER", "users")

        if not endpoint or not key:
            print("  COSMOSDB_ENDPOINT or COSMOSDB_KEY not set, Cosmos DB user store disabled")
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
                print(f"  Creating users container: {container_name}")
                self._container = await self._database.create_container(
                    id=container_name,
                    partition_key=PartitionKey(path="/username"),
                )

            self._connected = True
            print(f"  Connected to Cosmos DB for user storage (container: {container_name})")
            return True
        except Exception as e:
            print(f"  Failed to connect to Cosmos DB for users: {e}")
            self._connected = False
            return False

    async def close(self):
        """Close Cosmos DB connection."""
        if self._client:
            await self._client.close()
            self._connected = False

    async def get_user(self, username: str) -> Optional[dict]:
        """Get a user by username."""
        if not self._connected or not self._container:
            return None

        try:
            query = "SELECT * FROM c WHERE c.username = @username AND c.type = 'user'"
            params = [{"name": "@username", "value": username}]

            async for item in self._container.query_items(
                query=query,
                parameters=params,
            ):
                return self._cosmos_to_user_dict(item)
            return None
        except Exception as e:
            print(f"  Error getting user {username}: {e}")
            return None

    async def get_user_by_oauth(self, provider: str, oauth_id: str) -> Optional[dict]:
        """Get a user by OAuth provider and ID."""
        if not self._connected or not self._container:
            return None

        try:
            query = """
                SELECT * FROM c
                WHERE c.auth_provider = @provider
                AND c.oauth_id = @oauth_id
                AND c.type = 'user'
            """
            params = [
                {"name": "@provider", "value": provider},
                {"name": "@oauth_id", "value": oauth_id},
            ]

            # Cross-partition query needed because we're not filtering by username (partition key)
            async for item in self._container.query_items(
                query=query,
                parameters=params
            ):
                return self._cosmos_to_user_dict(item)
            return None
        except Exception as e:
            print(f"  Error getting OAuth user {provider}/{oauth_id}: {e}")
            return None

    async def create_user(self, user_dict: dict) -> dict:
        """Create a new user."""
        if not self._connected or not self._container:
            raise RuntimeError("Cosmos DB not connected")

        # Add Cosmos DB specific fields
        document = {
            "id": str(uuid.uuid4()),
            "type": "user",
            "created_at": datetime.now(timezone.utc).isoformat(),
            **user_dict,
        }

        await self._container.create_item(body=document)
        print(f"  Created user in Cosmos DB: {user_dict['username']}")
        return user_dict

    async def update_user(self, username: str, updates: dict) -> Optional[dict]:
        """Update user fields."""
        if not self._connected or not self._container:
            return None

        try:
            # First get the existing document
            query = "SELECT * FROM c WHERE c.username = @username AND c.type = 'user'"
            params = [{"name": "@username", "value": username}]

            existing_doc = None
            async for item in self._container.query_items(
                query=query,
                parameters=params,
            ):
                existing_doc = item
                break

            if not existing_doc:
                return None

            # Update the document
            for key, value in updates.items():
                existing_doc[key] = value
            existing_doc["updated_at"] = datetime.now(timezone.utc).isoformat()

            # Replace the document
            await self._container.replace_item(
                item=existing_doc["id"],
                body=existing_doc,
            )

            return self._cosmos_to_user_dict(existing_doc)
        except Exception as e:
            print(f"  Error updating user {username}: {e}")
            return None

    async def username_exists(self, username: str) -> bool:
        """Check if username already exists."""
        user = await self.get_user(username)
        return user is not None

    async def get_all_users(self) -> List[dict]:
        """Get all users (for admin)."""
        if not self._connected or not self._container:
            return []

        try:
            users = []
            query = "SELECT * FROM c WHERE c.type = 'user'"

            # Cross-partition query to get all users across all partitions
            async for item in self._container.query_items(
                query=query
            ):
                users.append(self._cosmos_to_user_dict(item))

            return users
        except Exception as e:
            print(f"  Error getting all users: {e}")
            return []

    async def delete_user(self, username: str) -> bool:
        """Delete a user by username."""
        if not self._connected or not self._container:
            return False

        try:
            # First get the document to find its ID
            query = "SELECT * FROM c WHERE c.username = @username AND c.type = 'user'"
            params = [{"name": "@username", "value": username}]

            doc_to_delete = None
            async for item in self._container.query_items(
                query=query,
                parameters=params,
            ):
                doc_to_delete = item
                break

            if not doc_to_delete:
                return False

            # Delete the document using ID and partition key (username)
            await self._container.delete_item(
                item=doc_to_delete["id"],
                partition_key=username,
            )
            print(f"  Deleted user from Cosmos DB: {username}")
            return True
        except Exception as e:
            print(f"  Error deleting user {username}: {e}")
            return False

    def _cosmos_to_user_dict(self, item: dict) -> dict:
        """Convert Cosmos DB document to user dict."""
        return {
            "username": item.get("username"),
            "email": item.get("email"),
            "hashed_password": item.get("hashed_password"),
            "disabled": item.get("disabled", False),
            "is_admin": item.get("is_admin", False),
            "auth_provider": item.get("auth_provider", "local"),
            "oauth_id": item.get("oauth_id"),
            "avatar_url": item.get("avatar_url"),
        }

    @property
    def is_connected(self) -> bool:
        return self._connected


class InMemoryUserStore(UserStoreBase):
    """In-memory user storage for local development."""

    def __init__(self):
        self._users: dict[str, dict] = {}

    async def connect(self) -> bool:
        print("  Using in-memory user store (Cosmos DB not configured)")
        return True

    async def close(self):
        pass

    async def get_user(self, username: str) -> Optional[dict]:
        return self._users.get(username)

    async def get_user_by_oauth(self, provider: str, oauth_id: str) -> Optional[dict]:
        for user_dict in self._users.values():
            if user_dict.get("auth_provider") == provider and user_dict.get("oauth_id") == oauth_id:
                return user_dict
        return None

    async def create_user(self, user_dict: dict) -> dict:
        username = user_dict["username"]
        self._users[username] = user_dict
        return user_dict

    async def update_user(self, username: str, updates: dict) -> Optional[dict]:
        if username not in self._users:
            return None
        for key, value in updates.items():
            self._users[username][key] = value
        return self._users[username]

    async def username_exists(self, username: str) -> bool:
        return username in self._users

    async def get_all_users(self) -> List[dict]:
        return list(self._users.values())

    async def delete_user(self, username: str) -> bool:
        """Delete a user by username."""
        if username in self._users:
            del self._users[username]
            return True
        return False

    @property
    def is_connected(self) -> bool:
        return False  # Indicates not connected to persistent storage


# Global user store instance
_user_store: Optional[UserStoreBase] = None


async def initialize_user_store() -> UserStoreBase:
    """Initialize the user store - tries Cosmos DB first, falls back to in-memory."""
    global _user_store

    # Try Cosmos DB first
    cosmos_store = CosmosDBUserStore()
    if await cosmos_store.connect():
        _user_store = cosmos_store
        return _user_store

    # Fall back to in-memory
    _user_store = InMemoryUserStore()
    await _user_store.connect()
    return _user_store


async def close_user_store():
    """Close the user store connection."""
    global _user_store
    if _user_store:
        await _user_store.close()


def get_user_store() -> UserStoreBase:
    """Get the global user store instance."""
    global _user_store
    if _user_store is None:
        raise RuntimeError("User store not initialized. Call initialize_user_store() first.")
    return _user_store
