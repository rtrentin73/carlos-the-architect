"""
Azure OpenAI rate limit handling with exponential backoff.

Provides retry logic for handling transient rate limit errors from Azure OpenAI.
"""

import asyncio
from functools import wraps
from typing import TypeVar, Callable, Any
import time

T = TypeVar('T')


class AzureOpenAIThrottler:
    """
    Handle Azure OpenAI rate limits gracefully with token tracking.

    Tracks token usage per minute and proactively waits when approaching limits.
    """

    def __init__(self, max_tokens_per_minute: int = 90000):
        self.token_usage: list[tuple[float, int]] = []
        self.max_tokens_per_minute = max_tokens_per_minute
        self._lock = asyncio.Lock()

    async def wait_if_needed(self, estimated_tokens: int) -> None:
        """Wait if we're approaching rate limits."""
        async with self._lock:
            now = time.time()

            # Remove entries older than 1 minute
            self.token_usage = [
                (timestamp, tokens)
                for timestamp, tokens in self.token_usage
                if now - timestamp < 60
            ]

            # Calculate current usage
            current_usage = sum(tokens for _, tokens in self.token_usage)

            if current_usage + estimated_tokens > self.max_tokens_per_minute:
                # Calculate wait time based on oldest entry
                if self.token_usage:
                    oldest_timestamp = self.token_usage[0][0]
                    wait_time = 60 - (now - oldest_timestamp)

                    if wait_time > 0:
                        print(f"⏳ Approaching Azure OpenAI rate limit, waiting {wait_time:.1f}s...")
                        await asyncio.sleep(wait_time)

            # Record this usage
            self.token_usage.append((time.time(), estimated_tokens))

    def record_usage(self, tokens: int) -> None:
        """Record actual token usage after a call completes."""
        self.token_usage.append((time.time(), tokens))

    def get_current_usage(self) -> dict:
        """Get current token usage stats."""
        now = time.time()
        recent_usage = [
            (timestamp, tokens)
            for timestamp, tokens in self.token_usage
            if now - timestamp < 60
        ]
        total = sum(tokens for _, tokens in recent_usage)
        return {
            "tokens_used_last_minute": total,
            "max_tokens_per_minute": self.max_tokens_per_minute,
            "remaining": max(0, self.max_tokens_per_minute - total),
            "utilization_pct": round(total / self.max_tokens_per_minute * 100, 1)
        }


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0
) -> Callable:
    """
    Decorator for exponential backoff on rate limit errors.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff calculation
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    error_str = str(e).lower()
                    last_exception = e

                    # Check if this is a rate limit error
                    is_rate_limit = (
                        "rate_limit" in error_str or
                        "429" in error_str or
                        "too many requests" in error_str or
                        "quota" in error_str
                    )

                    if is_rate_limit and attempt < max_retries:
                        # Calculate delay with exponential backoff and jitter
                        delay = min(base_delay * (exponential_base ** attempt), max_delay)
                        # Add jitter (±25%)
                        import random
                        jitter = delay * 0.25 * (2 * random.random() - 1)
                        delay = delay + jitter

                        print(f"⚠️  Azure OpenAI rate limit hit (attempt {attempt + 1}/{max_retries + 1}), "
                              f"retrying in {delay:.1f}s...")
                        await asyncio.sleep(delay)
                    else:
                        # Not a rate limit error or max retries exceeded
                        raise

            # Should not reach here, but just in case
            raise last_exception  # type: ignore

        return wrapper
    return decorator


# Singleton throttler instance
_throttler: AzureOpenAIThrottler | None = None


def get_throttler() -> AzureOpenAIThrottler:
    """Get the global throttler instance."""
    global _throttler
    if _throttler is None:
        _throttler = AzureOpenAIThrottler()
    return _throttler
