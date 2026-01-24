"""
Design pattern caching module for Carlos the Architect.

Uses Azure Cache for Redis for distributed caching across pod instances.
Falls back to in-memory cache if Redis is not available (local development).
"""

import hashlib
import json
import asyncio
import os
from datetime import datetime, timezone, timedelta
from typing import Optional
import redis.asyncio as redis


class RedisDesignCache:
    """Distributed design cache using Azure Cache for Redis."""

    def __init__(self, ttl_hours: int = 24):
        """
        Initialize the Redis cache.

        Args:
            ttl_hours: Time-to-live for cached entries in hours (default: 24)
        """
        self.ttl_hours = ttl_hours
        self.ttl_seconds = ttl_hours * 3600
        self._redis: Optional[redis.Redis] = None
        self._connected = False
        self._key_prefix = "carlos:design:"

        # Stats tracking (stored in Redis for distributed stats)
        self._stats_key = "carlos:cache:stats"

    async def connect(self):
        """Connect to Azure Cache for Redis."""
        redis_host = os.getenv("REDIS_HOST")
        redis_port = int(os.getenv("REDIS_PORT", "6380"))
        redis_password = os.getenv("REDIS_PASSWORD")
        redis_ssl = os.getenv("REDIS_SSL", "true").lower() == "true"

        if not redis_host:
            print("⚠️  REDIS_HOST not set, Redis cache disabled")
            return False

        try:
            self._redis = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                ssl=redis_ssl,
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0,
            )
            # Test connection
            await self._redis.ping()
            self._connected = True
            print(f"✅ Connected to Azure Cache for Redis at {redis_host}:{redis_port}")

            # Initialize stats if not exists
            if not await self._redis.exists(self._stats_key):
                await self._redis.hset(self._stats_key, mapping={"hits": 0, "misses": 0})

            return True
        except Exception as e:
            print(f"⚠️  Failed to connect to Redis: {e}")
            self._connected = False
            return False

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._connected = False
            print("🔌 Redis connection closed")

    def generate_cache_key(self, requirements: str, settings: dict) -> str:
        """
        Generate a deterministic cache key from requirements and settings.

        Normalizes requirements (lowercase, remove extra spaces) to improve hit rate.
        """
        normalized = " ".join(requirements.lower().strip().split())
        cache_input = {
            "requirements": normalized,
            "scenario": settings.get("scenario"),
            "cost_performance": settings.get("priorities", {}).get("cost_performance"),
            "compliance": settings.get("priorities", {}).get("compliance"),
        }
        cache_str = json.dumps(cache_input, sort_keys=True)
        hash_key = hashlib.sha256(cache_str.encode()).hexdigest()[:16]
        return f"{self._key_prefix}{hash_key}"

    async def get(self, cache_key: str) -> Optional[dict]:
        """Get cached design from Redis."""
        if not self._connected or not self._redis:
            return None

        try:
            data = await self._redis.get(cache_key)
            if data:
                await self._redis.hincrby(self._stats_key, "hits", 1)
                return json.loads(data)
            else:
                await self._redis.hincrby(self._stats_key, "misses", 1)
                return None
        except Exception as e:
            print(f"⚠️  Redis GET error: {e}")
            return None

    async def set(self, cache_key: str, design: dict):
        """Cache a design in Redis with TTL."""
        if not self._connected or not self._redis:
            return

        try:
            await self._redis.setex(
                cache_key,
                self.ttl_seconds,
                json.dumps(design)
            )
        except Exception as e:
            print(f"⚠️  Redis SET error: {e}")

    def should_cache(self, requirements: str) -> bool:
        """Determine if this design should be cached."""
        if not requirements or not requirements.strip():
            return False

        word_count = len(requirements.split())

        if word_count < 25:
            specific_indicators = [
                "my ", "our ", "company", "project", ".com", ".io", ".org", ".net",
                "client", "customer", "acme", "contoso", "$", "million",
            ]
            requirements_lower = requirements.lower()
            if any(indicator in requirements_lower for indicator in specific_indicators):
                return False
            return True

        if word_count >= 25 and word_count < 50:
            specific_indicators = ["my ", "our ", "company", "client", "$"]
            requirements_lower = requirements.lower()
            if any(indicator in requirements_lower for indicator in specific_indicators):
                return False
            return True

        return False

    async def get_stats(self) -> dict:
        """Get cache statistics from Redis."""
        if not self._connected or not self._redis:
            return {"entries": 0, "hits": 0, "misses": 0, "hit_rate_percent": 0, "connected": False}

        try:
            stats = await self._redis.hgetall(self._stats_key)
            hits = int(stats.get("hits", 0))
            misses = int(stats.get("misses", 0))
            total = hits + misses
            hit_rate = (hits / total * 100) if total > 0 else 0

            # Count cached entries (keys matching pattern)
            keys = await self._redis.keys(f"{self._key_prefix}*")
            entries = len(keys)

            return {
                "entries": entries,
                "hits": hits,
                "misses": misses,
                "hit_rate_percent": round(hit_rate, 2),
                "connected": True,
            }
        except Exception as e:
            print(f"⚠️  Redis stats error: {e}")
            return {"entries": 0, "hits": 0, "misses": 0, "hit_rate_percent": 0, "connected": False, "error": str(e)}

    async def clear(self):
        """Clear all cached designs."""
        if not self._connected or not self._redis:
            return 0

        try:
            keys = await self._redis.keys(f"{self._key_prefix}*")
            if keys:
                await self._redis.delete(*keys)
            # Reset stats
            await self._redis.hset(self._stats_key, mapping={"hits": 0, "misses": 0})
            return len(keys)
        except Exception as e:
            print(f"⚠️  Redis clear error: {e}")
            return 0

    @property
    def is_connected(self) -> bool:
        return self._connected


class InMemoryDesignCache:
    """Fallback in-memory cache for local development."""

    def __init__(self, ttl_hours: int = 24):
        self.cache: dict = {}
        self.ttl_hours = ttl_hours
        self.hit_count = 0
        self.miss_count = 0

    async def connect(self):
        print("📦 Using in-memory cache (Redis not configured)")
        return True

    async def close(self):
        pass

    def generate_cache_key(self, requirements: str, settings: dict) -> str:
        normalized = " ".join(requirements.lower().strip().split())
        cache_input = {
            "requirements": normalized,
            "scenario": settings.get("scenario"),
            "cost_performance": settings.get("priorities", {}).get("cost_performance"),
            "compliance": settings.get("priorities", {}).get("compliance"),
        }
        cache_str = json.dumps(cache_input, sort_keys=True)
        return hashlib.sha256(cache_str.encode()).hexdigest()[:16]

    async def get(self, cache_key: str) -> Optional[dict]:
        entry = self.cache.get(cache_key)
        if not entry:
            self.miss_count += 1
            return None

        if datetime.now(timezone.utc) > entry["expires_at"]:
            del self.cache[cache_key]
            self.miss_count += 1
            return None

        self.hit_count += 1
        return entry["design"]

    async def set(self, cache_key: str, design: dict):
        self.cache[cache_key] = {
            "design": design,
            "cached_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=self.ttl_hours),
        }

    def should_cache(self, requirements: str) -> bool:
        if not requirements or not requirements.strip():
            return False

        word_count = len(requirements.split())

        if word_count < 25:
            specific_indicators = [
                "my ", "our ", "company", "project", ".com", ".io", ".org", ".net",
                "client", "customer", "acme", "contoso", "$", "million",
            ]
            requirements_lower = requirements.lower()
            if any(indicator in requirements_lower for indicator in specific_indicators):
                return False
            return True

        if word_count >= 25 and word_count < 50:
            specific_indicators = ["my ", "our ", "company", "client", "$"]
            requirements_lower = requirements.lower()
            if any(indicator in requirements_lower for indicator in specific_indicators):
                return False
            return True

        return False

    async def get_stats(self) -> dict:
        total = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total * 100) if total > 0 else 0
        return {
            "entries": len(self.cache),
            "hits": self.hit_count,
            "misses": self.miss_count,
            "hit_rate_percent": round(hit_rate, 2),
            "connected": False,
            "mode": "in-memory",
        }

    async def clear(self):
        count = len(self.cache)
        self.cache.clear()
        self.hit_count = 0
        self.miss_count = 0
        return count

    @property
    def is_connected(self) -> bool:
        return False


async def stream_cached_design(design: dict):
    """
    Stream a cached design with simulated delays for UX consistency.
    """
    yield json.dumps({
        "type": "cache_hit",
        "message": "Using cached design pattern",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

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
            yield json.dumps({
                "type": "agent_start",
                "agent": agent,
                "cached": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

            await asyncio.sleep(0.05)

            yield json.dumps({
                "type": "field_update",
                "field": field,
                "content": design[field],
                "cached": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

            yield json.dumps({
                "type": "agent_complete",
                "agent": agent,
                "cached": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

            await asyncio.sleep(0.05)

    yield json.dumps({
        "type": "complete",
        "cached": True,
        "summary": design,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# Global cache instance
_design_cache = None


async def initialize_cache(ttl_hours: int = 24):
    """Initialize the cache - tries Redis first, falls back to in-memory."""
    global _design_cache

    # Try Redis first
    redis_cache = RedisDesignCache(ttl_hours=ttl_hours)
    if await redis_cache.connect():
        _design_cache = redis_cache
        return _design_cache

    # Fall back to in-memory
    _design_cache = InMemoryDesignCache(ttl_hours=ttl_hours)
    await _design_cache.connect()
    return _design_cache


async def close_cache():
    """Close the cache connection."""
    global _design_cache
    if _design_cache:
        await _design_cache.close()


def get_cache():
    """Get the global cache instance."""
    global _design_cache
    if _design_cache is None:
        raise RuntimeError("Cache not initialized. Call initialize_cache() first.")
    return _design_cache
