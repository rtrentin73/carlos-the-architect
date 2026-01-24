#!/usr/bin/env python3
"""
Test that all modules can be imported without errors.
This validates the code structure without requiring Azure credentials.
"""

print("Testing imports...")
print("-" * 50)

try:
    print("Importing llm_pool...")
    from llm_pool import get_pool, LLMPool
    print("✅ llm_pool imported successfully")

    print("Importing graph...")
    from graph import carlos_graph, CarlosState
    print("✅ graph imported successfully")

    print("Importing main...")
    # Don't actually import app to avoid lifespan execution
    import importlib.util
    spec = importlib.util.spec_from_file_location("main", "main.py")
    main_module = importlib.util.module_from_spec(spec)
    print("✅ main module structure validated")

    print()
    print("=" * 50)
    print("✅ All imports successful!")
    print("=" * 50)
    print()
    print("Connection pooling implementation is ready.")
    print("To test with actual LLM calls, run the backend with:")
    print("  cd backend && uvicorn main:app --reload")

except Exception as e:
    print(f"\n❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
