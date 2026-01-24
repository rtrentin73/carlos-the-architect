"""
Reference Search Module for Carlos the Architect

Searches for best practices, documentation, and architecture patterns
to inject into design prompts. Uses Tavily API for search.
"""

import os
import asyncio
import re
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple
import httpx


# Configuration
MAX_REFERENCES = int(os.getenv("MAX_REFERENCES", "8"))
SEARCH_TIMEOUT_SECONDS = float(os.getenv("SEARCH_TIMEOUT_SECONDS", "10.0"))
ENABLE_REFERENCE_SEARCH = os.getenv("ENABLE_REFERENCE_SEARCH", "true").lower() == "true"


@dataclass
class Reference:
    """A single reference from search results."""
    title: str
    url: str
    snippet: str
    source: str  # e.g., "AWS Docs", "Azure Docs", "Blog", "GitHub"

    def to_dict(self) -> dict:
        return asdict(self)


class ReferenceSearchService:
    """Service for searching and formatting architecture references."""

    def __init__(self):
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=SEARCH_TIMEOUT_SECONDS)
        return self._client

    async def close(self):
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _extract_keywords(self, requirements: str) -> List[str]:
        """Extract key terms from requirements for search queries."""
        # Common cloud/architecture terms to look for
        cloud_terms = [
            "aws", "azure", "gcp", "kubernetes", "k8s", "docker", "serverless",
            "lambda", "api gateway", "ecs", "eks", "aks", "gke", "s3", "dynamodb",
            "rds", "aurora", "redis", "elasticsearch", "kafka", "sqs", "sns",
            "cloudfront", "cdn", "load balancer", "alb", "nlb", "vpc", "subnet",
            "microservices", "monolith", "event-driven", "cqrs", "saga",
            "ci/cd", "terraform", "cloudformation", "helm"
        ]

        # Architecture patterns
        pattern_terms = [
            "high availability", "disaster recovery", "multi-region", "failover",
            "auto scaling", "horizontal scaling", "caching", "queue", "async",
            "real-time", "batch processing", "data pipeline", "etl", "streaming",
            "authentication", "authorization", "oauth", "jwt", "api", "rest",
            "graphql", "websocket", "grpc"
        ]

        # Business domains
        domain_terms = [
            "e-commerce", "ecommerce", "payment", "checkout", "inventory",
            "analytics", "dashboard", "reporting", "notification", "email",
            "mobile", "web app", "saas", "b2b", "b2c", "marketplace",
            "iot", "machine learning", "ai", "chatbot"
        ]

        text_lower = requirements.lower()
        found_terms = []

        # Find matching terms
        for term in cloud_terms + pattern_terms + domain_terms:
            if term in text_lower:
                found_terms.append(term)

        # Also extract capitalized proper nouns (likely service names)
        words = requirements.split()
        for word in words:
            clean = re.sub(r'[^\w]', '', word)
            if clean and clean[0].isupper() and len(clean) > 2:
                found_terms.append(clean.lower())

        # Deduplicate and limit
        return list(dict.fromkeys(found_terms))[:10]

    def _build_search_queries(
        self,
        requirements: str,
        cloud_provider: Optional[str] = None
    ) -> List[str]:
        """Generate search queries from requirements."""
        keywords = self._extract_keywords(requirements)

        # Determine cloud provider focus
        provider = cloud_provider or "AWS"  # Default to AWS
        provider_map = {
            "aws": "AWS",
            "azure": "Azure",
            "gcp": "Google Cloud",
            "multi_cloud": "cloud"
        }
        provider_name = provider_map.get(provider.lower(), "AWS")

        queries = []

        # Well-Architected Framework query
        queries.append(f"{provider_name} Well-Architected Framework best practices")

        # Architecture patterns based on keywords
        if any(k in keywords for k in ["e-commerce", "ecommerce", "payment", "checkout"]):
            queries.append(f"{provider_name} e-commerce architecture best practices")

        if any(k in keywords for k in ["microservices", "kubernetes", "k8s", "ecs", "eks"]):
            queries.append(f"{provider_name} microservices architecture patterns")

        if any(k in keywords for k in ["serverless", "lambda", "functions"]):
            queries.append(f"{provider_name} serverless architecture patterns")

        if any(k in keywords for k in ["high availability", "disaster recovery", "multi-region"]):
            queries.append(f"{provider_name} high availability disaster recovery patterns")

        if any(k in keywords for k in ["api", "rest", "graphql", "gateway"]):
            queries.append(f"{provider_name} API design best practices")

        if any(k in keywords for k in ["data pipeline", "etl", "streaming", "kafka"]):
            queries.append(f"{provider_name} data pipeline architecture")

        if any(k in keywords for k in ["authentication", "authorization", "security"]):
            queries.append(f"{provider_name} security architecture best practices")

        # Generic architecture query with top keywords
        if len(keywords) >= 2:
            top_keywords = " ".join(keywords[:3])
            queries.append(f"{provider_name} {top_keywords} architecture")

        # Limit queries
        return queries[:4]

    def _classify_source(self, url: str) -> str:
        """Classify the source type based on URL."""
        url_lower = url.lower()

        if "docs.aws.amazon.com" in url_lower or "aws.amazon.com" in url_lower:
            return "AWS Docs"
        elif "docs.microsoft.com" in url_lower or "azure.microsoft.com" in url_lower or "learn.microsoft.com" in url_lower:
            return "Azure Docs"
        elif "cloud.google.com" in url_lower:
            return "Google Cloud Docs"
        elif "github.com" in url_lower:
            return "GitHub"
        elif "medium.com" in url_lower:
            return "Medium"
        elif "dev.to" in url_lower:
            return "Dev.to"
        elif "stackoverflow.com" in url_lower:
            return "Stack Overflow"
        elif "hashicorp.com" in url_lower or "terraform.io" in url_lower:
            return "HashiCorp"
        elif "kubernetes.io" in url_lower:
            return "Kubernetes Docs"
        elif "serverlessland.com" in url_lower:
            return "Serverless Land"
        else:
            return "Article"

    async def search_tavily(self, query: str, max_results: int = 5) -> List[Reference]:
        """Search using Tavily API."""
        if not self.tavily_api_key:
            return []

        try:
            client = await self._get_client()
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self.tavily_api_key,
                    "query": query,
                    "search_depth": "basic",
                    "include_domains": [
                        "docs.aws.amazon.com",
                        "aws.amazon.com",
                        "docs.microsoft.com",
                        "azure.microsoft.com",
                        "learn.microsoft.com",
                        "cloud.google.com",
                        "kubernetes.io",
                        "github.com",
                        "medium.com",
                        "dev.to",
                        "hashicorp.com",
                        "terraform.io",
                        "serverlessland.com"
                    ],
                    "max_results": max_results
                }
            )
            response.raise_for_status()
            data = response.json()

            references = []
            for result in data.get("results", []):
                ref = Reference(
                    title=result.get("title", "Untitled"),
                    url=result.get("url", ""),
                    snippet=result.get("content", "")[:300],
                    source=self._classify_source(result.get("url", ""))
                )
                references.append(ref)

            return references

        except Exception as e:
            print(f"  Tavily search error for '{query}': {e}")
            return []

    async def get_references(
        self,
        requirements: str,
        cloud_provider: Optional[str] = None
    ) -> List[Reference]:
        """Main entry point - search and return unique references."""
        if not ENABLE_REFERENCE_SEARCH:
            return []

        if not self.tavily_api_key:
            print("  Reference search disabled: TAVILY_API_KEY not set")
            return []

        queries = self._build_search_queries(requirements, cloud_provider)
        print(f"  Searching references with {len(queries)} queries...")

        # Run searches in parallel
        tasks = [self.search_tavily(q, max_results=3) for q in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect and deduplicate references
        seen_urls = set()
        all_references = []

        for result in results:
            if isinstance(result, Exception):
                continue
            for ref in result:
                if ref.url not in seen_urls:
                    seen_urls.add(ref.url)
                    all_references.append(ref)

        # Limit total references
        return all_references[:MAX_REFERENCES]

    def format_for_prompt(self, references: List[Reference]) -> str:
        """Format references as markdown for injection into prompts."""
        if not references:
            return ""

        lines = [
            "## Reference Materials",
            "",
            "The following documentation and best practices are relevant to this design:",
            ""
        ]

        # Group by source
        by_source = {}
        for ref in references:
            if ref.source not in by_source:
                by_source[ref.source] = []
            by_source[ref.source].append(ref)

        for source, refs in by_source.items():
            lines.append(f"### {source}")
            for ref in refs:
                # Truncate snippet for prompt
                snippet = ref.snippet[:150] + "..." if len(ref.snippet) > 150 else ref.snippet
                lines.append(f"- [{ref.title}]({ref.url})")
                lines.append(f"  {snippet}")
            lines.append("")

        lines.append("**Instructions:** Consider these references when designing. Include a '## References' section at the end of your design, citing sources that influenced your architecture decisions.")
        lines.append("")

        return "\n".join(lines)


# Global service instance
_service: Optional[ReferenceSearchService] = None


def get_reference_service() -> ReferenceSearchService:
    """Get the global reference search service instance."""
    global _service
    if _service is None:
        _service = ReferenceSearchService()
    return _service


async def get_reference_context(
    requirements: str,
    cloud_provider: Optional[str] = None
) -> Tuple[str, List[dict]]:
    """
    Convenience function for graph integration.

    Returns:
        Tuple of (formatted_context, list of reference dicts)
    """
    try:
        service = get_reference_service()

        # Apply timeout
        references = await asyncio.wait_for(
            service.get_references(requirements, cloud_provider),
            timeout=SEARCH_TIMEOUT_SECONDS
        )

        if references:
            print(f"  Found {len(references)} references")
            context = service.format_for_prompt(references)
            ref_dicts = [ref.to_dict() for ref in references]
            return context, ref_dicts
        else:
            return "", []

    except asyncio.TimeoutError:
        print("  Reference search timed out")
        return "", []
    except Exception as e:
        print(f"  Reference search error: {e}")
        return "", []


async def close_reference_service():
    """Close the reference service (cleanup)."""
    global _service
    if _service:
        await _service.close()
        _service = None
