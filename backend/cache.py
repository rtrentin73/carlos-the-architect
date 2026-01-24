"""
Design pattern caching module for Carlos the Architect.

Caches frequent architecture patterns for instant responses.
Problem: Common requests like "AKS cluster with monitoring" get repeated many times.
Solution: Cache these patterns to reduce cost and latency by 90%+.
"""

import hashlib
import json
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional


class DesignCache:
    """Cache common design patterns for instant responses."""

    def __init__(self, ttl_hours: int = 24):
        """
        Initialize the design cache.

        Args:
            ttl_hours: Time-to-live for cached entries in hours (default: 24)
        """
        self.cache: dict = {}  # In-memory cache. Use Redis in production for distributed caching.
        self.ttl_hours = ttl_hours
        self.hit_count = 0
        self.miss_count = 0

    def generate_cache_key(self, requirements: str, settings: dict) -> str:
        """
        Generate a deterministic cache key from requirements and settings.

        Normalizes requirements (lowercase, remove extra spaces) to improve hit rate.
        Includes relevant settings that affect the output.
        """
        # Normalize requirements
        normalized = " ".join(requirements.lower().strip().split())

        # Include relevant settings that affect design output
        cache_input = {
            "requirements": normalized,
            "scenario": settings.get("scenario"),
            "cost_performance": settings.get("priorities", {}).get("cost_performance"),
            "compliance": settings.get("priorities", {}).get("compliance"),
        }

        # Create deterministic hash
        cache_str = json.dumps(cache_input, sort_keys=True)
        return hashlib.sha256(cache_str.encode()).hexdigest()[:16]  # Use first 16 chars for readability

    def get(self, cache_key: str) -> Optional[dict]:
        """
        Get cached design if it exists and hasn't expired.

        Returns None if not cached or expired.
        """
        entry = self.cache.get(cache_key)
        if not entry:
            self.miss_count += 1
            return None

        # Check if expired
        if datetime.now(timezone.utc) > entry["expires_at"]:
            del self.cache[cache_key]
            self.miss_count += 1
            return None

        self.hit_count += 1
        return entry["design"]

    def set(self, cache_key: str, design: dict):
        """Cache a design with TTL."""
        self.cache[cache_key] = {
            "design": design,
            "cached_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=self.ttl_hours),
        }

    def should_cache(self, requirements: str) -> bool:
        """
        Determine if this design should be cached.

        Caches short, generic requirements (likely common patterns).
        Skips caching for specific/personalized requirements.
        """
        # Don't cache empty requirements
        if not requirements or not requirements.strip():
            return False

        word_count = len(requirements.split())

        # Cache short, generic requirements (likely common patterns)
        # These are typically questions like "AKS cluster with monitoring"
        if word_count < 25:
            # Check for specific/personalized indicators
            specific_indicators = [
                "my ",
                "our ",
                "company",
                "project",
                ".com",
                ".io",
                ".org",
                ".net",
                "client",
                "customer",
                "acme",
                "contoso",
                "$",  # Specific budget amounts
                "million",
            ]
            requirements_lower = requirements.lower()
            if any(indicator in requirements_lower for indicator in specific_indicators):
                return False
            return True

        # For longer requirements, be more selective
        # Only cache if it looks like a template/common pattern
        if word_count >= 25 and word_count < 50:
            # Only cache if no specific indicators
            specific_indicators = ["my ", "our ", "company", "client", "$"]
            requirements_lower = requirements.lower()
            if any(indicator in requirements_lower for indicator in specific_indicators):
                return False
            return True

        # Don't cache very long, detailed requirements (likely specific use cases)
        return False

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total * 100) if total > 0 else 0
        return {
            "entries": len(self.cache),
            "hits": self.hit_count,
            "misses": self.miss_count,
            "hit_rate_percent": round(hit_rate, 2),
        }

    def clear(self):
        """Clear all cached entries."""
        self.cache.clear()
        self.hit_count = 0
        self.miss_count = 0

    def clear_expired(self) -> int:
        """Remove expired entries. Returns count of removed entries."""
        now = datetime.now(timezone.utc)
        expired_keys = [
            key for key, entry in self.cache.items() if now > entry["expires_at"]
        ]
        for key in expired_keys:
            del self.cache[key]
        return len(expired_keys)


async def stream_cached_design(design: dict):
    """
    Stream a cached design with simulated delays for UX consistency.

    This provides a similar experience to the live streaming, but much faster.
    Users see data appearing progressively rather than all at once.
    """
    # Emit cache hit notification
    yield json.dumps({
        "type": "cache_hit",
        "message": "Using cached design pattern",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    # Simulate streaming by emitting field updates with small delays
    field_order = [
        ("design", "carlos"),
        ("ronei_design", "ronei_design"),
        ("security_report", "security"),
        ("cost_report", "cost"),
        ("reliability_report", "reliability"),
        ("audit_report", "audit"),
        ("recommendation", "recommender"),
        ("terraform_code", "terraform_coder"),
        ("terraform_validation", "terraform_validator"),
    ]

    for field, agent in field_order:
        if field in design and design[field]:
            # Emit agent_start
            yield json.dumps({
                "type": "agent_start",
                "agent": agent,
                "cached": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

            await asyncio.sleep(0.05)  # Small delay for UX

            # Emit field_update
            yield json.dumps({
                "type": "field_update",
                "field": field,
                "content": design[field],
                "cached": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

            # Emit agent_complete
            yield json.dumps({
                "type": "agent_complete",
                "agent": agent,
                "cached": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

            await asyncio.sleep(0.05)

    # Emit complete summary
    yield json.dumps({
        "type": "complete",
        "cached": True,
        "summary": design,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# Global cache instance
_design_cache: Optional[DesignCache] = None


def get_cache(ttl_hours: int = 24) -> DesignCache:
    """Get or create the global design cache instance."""
    global _design_cache
    if _design_cache is None:
        _design_cache = DesignCache(ttl_hours=ttl_hours)
    return _design_cache
