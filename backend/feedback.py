"""
Deployment feedback tracking module for Carlos the Architect.

Stores user feedback on deployed designs to enable:
- Tracking deployment success rates
- Identifying common issues
- Improving prompts based on real outcomes
- Product intelligence for roadmap decisions

Uses Azure Cosmos DB for persistent storage, falls back to in-memory for local development.
"""

import os
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class CloudProvider(str, Enum):
    AZURE = "azure"
    AWS = "aws"
    GCP = "gcp"
    MULTI_CLOUD = "multi_cloud"
    OTHER = "other"


class Environment(str, Enum):
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"
    TEST = "test"


class DeploymentFeedback(BaseModel):
    """Model for deployment feedback submission."""
    design_id: str = Field(description="Unique identifier for the design")
    deployed: bool = Field(description="Whether the design was deployed")
    deployment_date: Optional[datetime] = Field(default=None, description="When the deployment occurred")
    cloud_provider: CloudProvider = Field(default=CloudProvider.AZURE, description="Cloud provider used")
    environment: Environment = Field(default=Environment.DEV, description="Deployment environment")
    success: bool = Field(description="Whether deployment was successful")
    issues_encountered: Optional[List[str]] = Field(default=None, description="List of issues encountered")
    modifications_made: Optional[str] = Field(default=None, description="Description of modifications made to the design")
    satisfaction_rating: int = Field(ge=1, le=5, description="User satisfaction rating (1-5)")
    comments: Optional[str] = Field(default=None, description="Additional comments from user")


class StoredFeedback(BaseModel):
    """Full feedback record as stored in the database."""
    feedback_id: str
    username: str
    design_id: str
    deployed: bool
    deployment_date: Optional[str]
    cloud_provider: str
    environment: str
    success: bool
    issues_encountered: Optional[List[str]]
    modifications_made: Optional[str]
    satisfaction_rating: int
    comments: Optional[str]
    created_at: str
    requirements_summary: Optional[str] = None


class CosmosDBFeedbackStore:
    """Distributed feedback storage using Azure Cosmos DB."""

    def __init__(self):
        self._client = None
        self._database = None
        self._container = None
        self._connected = False

    async def connect(self):
        """Connect to Azure Cosmos DB."""
        endpoint = os.getenv("COSMOSDB_ENDPOINT")
        key = os.getenv("COSMOSDB_KEY")
        database_name = os.getenv("COSMOSDB_DATABASE", "carlos-feedback")
        container_name = os.getenv("COSMOSDB_CONTAINER", "deployments")

        if not endpoint or not key:
            print("  COSMOSDB_ENDPOINT or COSMOSDB_KEY not set, Cosmos DB feedback store disabled")
            return False

        try:
            from azure.cosmos.aio import CosmosClient
            from azure.cosmos import PartitionKey

            self._client = CosmosClient(endpoint, credential=key)
            self._database = self._client.get_database_client(database_name)
            self._container = self._database.get_container_client(container_name)

            # Test connection by reading container properties
            await self._container.read()

            self._connected = True
            print(f"  Connected to Cosmos DB for feedback storage (database: {database_name})")
            return True
        except Exception as e:
            print(f"  Failed to connect to Cosmos DB for feedback: {e}")
            self._connected = False
            return False

    async def close(self):
        """Close Cosmos DB connection."""
        if self._client:
            await self._client.close()
            self._connected = False

    async def save_feedback(
        self,
        username: str,
        feedback: DeploymentFeedback,
        requirements_summary: Optional[str] = None
    ) -> str:
        """Save deployment feedback."""
        if not self._connected or not self._container:
            raise RuntimeError("Cosmos DB not connected")

        feedback_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        # Create document for Cosmos DB
        document = {
            "id": feedback_id,
            "feedback_id": feedback_id,
            "username": username,
            "design_id": feedback.design_id,
            "deployed": feedback.deployed,
            "deployment_date": feedback.deployment_date.isoformat() if feedback.deployment_date else None,
            "cloud_provider": feedback.cloud_provider.value,
            "environment": feedback.environment.value,
            "success": feedback.success,
            "issues_encountered": feedback.issues_encountered,
            "modifications_made": feedback.modifications_made,
            "satisfaction_rating": feedback.satisfaction_rating,
            "comments": feedback.comments,
            "created_at": now,
            "requirements_summary": requirements_summary,
            "type": "deployment_feedback",
        }

        await self._container.create_item(body=document)
        return feedback_id

    async def get_feedback(self, feedback_id: str) -> Optional[StoredFeedback]:
        """Get a specific feedback record."""
        if not self._connected or not self._container:
            return None

        try:
            query = "SELECT * FROM c WHERE c.feedback_id = @feedback_id"
            parameters = [{"name": "@feedback_id", "value": feedback_id}]

            items = []
            async for item in self._container.query_items(
                query=query,
                parameters=parameters
            ):
                items.append(item)

            if items:
                return StoredFeedback(**items[0])
            return None
        except Exception as e:
            print(f"  Error getting feedback: {e}")
            return None

    async def get_user_feedback(self, username: str, limit: int = 20) -> List[StoredFeedback]:
        """Get feedback records for a specific user."""
        if not self._connected or not self._container:
            return []

        try:
            query = """
                SELECT * FROM c
                WHERE c.username = @username
                ORDER BY c.created_at DESC
                OFFSET 0 LIMIT @limit
            """
            parameters = [
                {"name": "@username", "value": username},
                {"name": "@limit", "value": limit}
            ]

            results = []
            async for item in self._container.query_items(
                query=query,
                parameters=parameters
            ):
                results.append(StoredFeedback(**item))

            return results
        except Exception as e:
            print(f"  Error getting user feedback: {e}")
            return []

    async def search_by_keywords(
        self,
        keywords: List[str],
        cloud_provider: Optional[str] = None,
        limit: int = 20
    ) -> List[StoredFeedback]:
        """
        Search feedback by keywords in requirements_summary.

        Used by the historical learning module to find similar past designs.

        Args:
            keywords: List of keywords to search for
            cloud_provider: Optional filter by cloud provider
            limit: Maximum results to return

        Returns:
            List of matching StoredFeedback records, sorted by rating
        """
        if not self._connected or not self._container:
            return []

        if not keywords:
            return []

        try:
            # Build query with CONTAINS for keyword matching
            # We check if requirements_summary contains any of the keywords
            keyword_conditions = " OR ".join([
                f"CONTAINS(LOWER(c.requirements_summary), @kw{i})"
                for i in range(len(keywords))
            ])

            query = f"""
                SELECT * FROM c
                WHERE c.type = 'deployment_feedback'
                AND c.requirements_summary != null
                AND ({keyword_conditions})
            """

            parameters = [
                {"name": f"@kw{i}", "value": kw.lower()}
                for i, kw in enumerate(keywords)
            ]

            # Add cloud provider filter if specified
            if cloud_provider:
                query = query.replace(
                    f"AND ({keyword_conditions})",
                    f"AND c.cloud_provider = @cloud_provider AND ({keyword_conditions})"
                )
                parameters.append({"name": "@cloud_provider", "value": cloud_provider})

            results = []
            async for item in self._container.query_items(
                query=query,
                parameters=parameters
            ):
                results.append(StoredFeedback(**item))

            # Sort by satisfaction rating (descending), then by created_at (descending)
            results.sort(
                key=lambda f: (f.satisfaction_rating, f.created_at),
                reverse=True
            )

            return results[:limit]

        except Exception as e:
            print(f"  Error searching feedback by keywords: {e}")
            return []

    async def get_analytics(self) -> dict:
        """Get aggregate deployment analytics."""
        if not self._connected or not self._container:
            return self._empty_analytics()

        try:
            # Get total count
            total_query = "SELECT VALUE COUNT(1) FROM c WHERE c.type = 'deployment_feedback'"
            total_feedback = 0
            async for item in self._container.query_items(query=total_query):
                total_feedback = item

            # Get deployed count
            deployed_query = "SELECT VALUE COUNT(1) FROM c WHERE c.type = 'deployment_feedback' AND c.deployed = true"
            deployed_count = 0
            async for item in self._container.query_items(query=deployed_query):
                deployed_count = item

            # Get successful deployments
            success_query = "SELECT VALUE COUNT(1) FROM c WHERE c.type = 'deployment_feedback' AND c.deployed = true AND c.success = true"
            successful = 0
            async for item in self._container.query_items(query=success_query):
                successful = item

            # Get failed deployments
            failed = deployed_count - successful

            # Get average satisfaction
            rating_query = "SELECT VALUE AVG(c.satisfaction_rating) FROM c WHERE c.type = 'deployment_feedback'"
            avg_satisfaction = 0
            async for item in self._container.query_items(query=rating_query):
                avg_satisfaction = item or 0

            # Calculate rates
            deployment_rate = (deployed_count / total_feedback * 100) if total_feedback > 0 else 0
            success_rate = (successful / deployed_count * 100) if deployed_count > 0 else 0

            # Get common issues
            common_issues = await self._get_common_issues(limit=10)

            return {
                "total_designs_tracked": total_feedback,
                "deployed_count": deployed_count,
                "deployment_rate_percent": round(deployment_rate, 2),
                "successful_deployments": successful,
                "failed_deployments": failed,
                "success_rate_percent": round(success_rate, 2),
                "average_satisfaction": round(avg_satisfaction, 2) if avg_satisfaction else 0,
                "total_ratings": total_feedback,
                "common_issues": common_issues,
                "connected": True,
                "storage": "cosmosdb",
            }
        except Exception as e:
            print(f"  Error getting analytics: {e}")
            return self._empty_analytics()

    async def _get_common_issues(self, limit: int = 10) -> List[dict]:
        """Get most common issues reported."""
        if not self._container:
            return []

        try:
            # Get all issues from documents
            query = """
                SELECT c.issues_encountered FROM c
                WHERE c.type = 'deployment_feedback'
                AND IS_ARRAY(c.issues_encountered)
            """

            issues_count = {}
            async for item in self._container.query_items(query=query):
                if item.get("issues_encountered"):
                    for issue in item["issues_encountered"]:
                        normalized = issue.lower().strip()[:100]
                        issues_count[normalized] = issues_count.get(normalized, 0) + 1

            # Sort by count and return top N
            sorted_issues = sorted(
                [{"issue": k, "count": v} for k, v in issues_count.items()],
                key=lambda x: x["count"],
                reverse=True
            )
            return sorted_issues[:limit]
        except Exception as e:
            print(f"  Error getting common issues: {e}")
            return []

    def _empty_analytics(self) -> dict:
        """Return empty analytics structure."""
        return {
            "total_designs_tracked": 0,
            "deployed_count": 0,
            "deployment_rate_percent": 0,
            "successful_deployments": 0,
            "failed_deployments": 0,
            "success_rate_percent": 0,
            "average_satisfaction": 0,
            "total_ratings": 0,
            "common_issues": [],
            "connected": False,
        }

    @property
    def is_connected(self) -> bool:
        return self._connected


class InMemoryFeedbackStore:
    """Fallback in-memory feedback storage for local development."""

    def __init__(self):
        self._feedback: dict[str, StoredFeedback] = {}
        self._user_feedback: dict[str, List[str]] = {}
        self._analytics = {
            "total_feedback": 0,
            "deployed_count": 0,
            "successful_deployments": 0,
            "failed_deployments": 0,
            "total_ratings": 0,
            "rating_sum": 0,
        }
        self._issues: dict[str, int] = {}

    async def connect(self):
        print("  Using in-memory feedback store (Cosmos DB not configured)")
        return True

    async def close(self):
        pass

    async def save_feedback(
        self,
        username: str,
        feedback: DeploymentFeedback,
        requirements_summary: Optional[str] = None
    ) -> str:
        feedback_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        stored = StoredFeedback(
            feedback_id=feedback_id,
            username=username,
            design_id=feedback.design_id,
            deployed=feedback.deployed,
            deployment_date=feedback.deployment_date.isoformat() if feedback.deployment_date else None,
            cloud_provider=feedback.cloud_provider.value,
            environment=feedback.environment.value,
            success=feedback.success,
            issues_encountered=feedback.issues_encountered,
            modifications_made=feedback.modifications_made,
            satisfaction_rating=feedback.satisfaction_rating,
            comments=feedback.comments,
            created_at=now,
            requirements_summary=requirements_summary,
        )

        self._feedback[feedback_id] = stored

        if username not in self._user_feedback:
            self._user_feedback[username] = []
        self._user_feedback[username].insert(0, feedback_id)

        # Update analytics
        self._analytics["total_feedback"] += 1
        if feedback.deployed:
            self._analytics["deployed_count"] += 1
            if feedback.success:
                self._analytics["successful_deployments"] += 1
            else:
                self._analytics["failed_deployments"] += 1

        self._analytics["total_ratings"] += 1
        self._analytics["rating_sum"] += feedback.satisfaction_rating

        # Track issues
        if feedback.issues_encountered:
            for issue in feedback.issues_encountered:
                normalized = issue.lower().strip()[:100]
                self._issues[normalized] = self._issues.get(normalized, 0) + 1

        return feedback_id

    async def get_feedback(self, feedback_id: str) -> Optional[StoredFeedback]:
        return self._feedback.get(feedback_id)

    async def get_user_feedback(self, username: str, limit: int = 20) -> List[StoredFeedback]:
        feedback_ids = self._user_feedback.get(username, [])[:limit]
        return [self._feedback[fid] for fid in feedback_ids if fid in self._feedback]

    async def search_by_keywords(
        self,
        keywords: List[str],
        cloud_provider: Optional[str] = None,
        limit: int = 20
    ) -> List[StoredFeedback]:
        """
        Search feedback by keywords in requirements_summary.

        Used by the historical learning module to find similar past designs.
        """
        if not keywords:
            return []

        results = []
        for feedback in self._feedback.values():
            if not feedback.requirements_summary:
                continue

            # Check if any keyword matches (case-insensitive)
            summary_lower = feedback.requirements_summary.lower()
            if any(kw.lower() in summary_lower for kw in keywords):
                # Filter by cloud_provider if specified
                if cloud_provider and feedback.cloud_provider != cloud_provider:
                    continue
                results.append(feedback)

        # Sort by rating (descending) then date (descending)
        results.sort(
            key=lambda f: (f.satisfaction_rating, f.created_at),
            reverse=True
        )
        return results[:limit]

    async def get_analytics(self) -> dict:
        total = self._analytics["total_feedback"]
        deployed = self._analytics["deployed_count"]
        successful = self._analytics["successful_deployments"]
        total_ratings = self._analytics["total_ratings"]
        rating_sum = self._analytics["rating_sum"]

        deployment_rate = (deployed / total * 100) if total > 0 else 0
        success_rate = (successful / deployed * 100) if deployed > 0 else 0
        avg_satisfaction = (rating_sum / total_ratings) if total_ratings > 0 else 0

        # Get common issues
        common_issues = sorted(
            [{"issue": k, "count": v} for k, v in self._issues.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:10]

        return {
            "total_designs_tracked": total,
            "deployed_count": deployed,
            "deployment_rate_percent": round(deployment_rate, 2),
            "successful_deployments": successful,
            "failed_deployments": self._analytics["failed_deployments"],
            "success_rate_percent": round(success_rate, 2),
            "average_satisfaction": round(avg_satisfaction, 2),
            "total_ratings": total_ratings,
            "common_issues": common_issues,
            "connected": False,
            "storage": "in-memory",
        }

    @property
    def is_connected(self) -> bool:
        return False


# Global feedback store instance
_feedback_store = None


async def initialize_feedback_store():
    """Initialize the feedback store - tries Cosmos DB first, falls back to in-memory."""
    global _feedback_store

    # Try Cosmos DB first
    cosmos_store = CosmosDBFeedbackStore()
    if await cosmos_store.connect():
        _feedback_store = cosmos_store
        return _feedback_store

    # Fall back to in-memory
    _feedback_store = InMemoryFeedbackStore()
    await _feedback_store.connect()
    return _feedback_store


async def close_feedback_store():
    """Close the feedback store connection."""
    global _feedback_store
    if _feedback_store:
        await _feedback_store.close()


def get_feedback_store():
    """Get the global feedback store instance."""
    global _feedback_store
    if _feedback_store is None:
        raise RuntimeError("Feedback store not initialized. Call initialize_feedback_store() first.")
    return _feedback_store
