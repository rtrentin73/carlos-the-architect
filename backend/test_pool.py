#!/usr/bin/env python3
"""
Test script for LLM connection pool.

Verifies that the connection pool can be initialized and used.
"""

import asyncio
from llm_pool import get_pool, LLMPool


async def test_pool_initialization():
    """Test that the pool can be initialized."""
    print("Test 1: Pool Initialization")
    print("-" * 50)

    pool = get_pool(size=3)
    await pool.initialize()

    stats = pool.get_pool_stats()
    print(f"✅ Pool initialized successfully")
    print(f"   Main pool: {stats['main']['total']} connections")
    print(f"   Ronei pool: {stats['ronei']['total']} connections")
    print(f"   Mini pool: {stats['mini']['total']} connections")
    print()


async def test_pool_context_manager():
    """Test that we can get LLMs from the pool using context managers."""
    print("Test 2: Context Manager Usage")
    print("-" * 50)

    pool = get_pool()

    # Test getting main LLM
    async with pool.get_main_llm() as llm:
        print(f"✅ Got main LLM from pool: {type(llm).__name__}")

    # Test getting Ronei LLM
    async with pool.get_ronei_llm() as llm:
        print(f"✅ Got Ronei LLM from pool: {type(llm).__name__}")

    # Test getting mini LLM
    async with pool.get_mini_llm() as llm:
        print(f"✅ Got mini LLM from pool: {type(llm).__name__}")

    print()


async def test_concurrent_usage():
    """Test that multiple concurrent requests can use the pool."""
    print("Test 3: Concurrent Pool Usage")
    print("-" * 50)

    pool = get_pool()

    async def use_llm(agent_name: str):
        async with pool.get_main_llm() as llm:
            print(f"   {agent_name} acquired LLM")
            await asyncio.sleep(0.1)  # Simulate work
            print(f"   {agent_name} released LLM")

    # Run 5 concurrent tasks
    await asyncio.gather(
        use_llm("Carlos"),
        use_llm("Auditor"),
        use_llm("Recommender"),
        use_llm("Terraform"),
        use_llm("Extra")
    )

    stats = pool.get_pool_stats()
    print(f"✅ Concurrent usage completed")
    print(f"   Main pool available: {stats['main']['available']}/{stats['main']['total']}")
    print()


async def test_pool_stats():
    """Test that pool statistics are accurate."""
    print("Test 4: Pool Statistics")
    print("-" * 50)

    pool = get_pool()

    # Get initial stats
    stats_before = pool.get_pool_stats()
    print(f"Before acquiring:")
    print(f"   Main: {stats_before['main']['available']} available, {stats_before['main']['in_use']} in use")

    # Acquire 2 connections
    async with pool.get_main_llm() as llm1:
        async with pool.get_main_llm() as llm2:
            stats_during = pool.get_pool_stats()
            print(f"During (2 acquired):")
            print(f"   Main: {stats_during['main']['available']} available, {stats_during['main']['in_use']} in use")

    # Check stats after release
    stats_after = pool.get_pool_stats()
    print(f"After release:")
    print(f"   Main: {stats_after['main']['available']} available, {stats_after['main']['in_use']} in use")

    assert stats_after['main']['in_use'] == 0, "All connections should be released"
    print(f"✅ Pool statistics are accurate")
    print()


async def main():
    """Run all tests."""
    print("=" * 50)
    print("LLM Connection Pool Tests")
    print("=" * 50)
    print()

    try:
        await test_pool_initialization()
        await test_pool_context_manager()
        await test_concurrent_usage()
        await test_pool_stats()

        print("=" * 50)
        print("✅ All tests passed!")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
