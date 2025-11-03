#!/usr/bin/env python
"""
Quick script to check if ARQ worker is configured correctly
and can connect to Redis.
"""
import os
import sys
import asyncio
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from arq import create_pool
from arq.connections import RedisSettings

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
REDIS_DB = int(os.getenv('REDIS_DB', 0))

async def check_worker_setup():
    print("=" * 80)
    print("🔍 CHECKING WORKER SETUP")
    print("=" * 80)
    
    # Check Redis connection
    print(f"\n1. Testing Redis connection...")
    print(f"   Host: {REDIS_HOST}")
    print(f"   Port: {REDIS_PORT}")
    print(f"   DB: {REDIS_DB}")
    
    try:
        pool = await create_pool(
            RedisSettings(
                host=REDIS_HOST,
                port=REDIS_PORT,
                password=REDIS_PASSWORD,
                database=REDIS_DB
            )
        )
        print("   ✅ Redis connection successful!")
        
        # Check for pending jobs
        try:
            info = await pool.info()
            print(f"\n2. Redis Queue Info:")
            print(f"   Pending jobs: {info.get('queued', 0)}")
            print(f"   In progress: {info.get('in_progress', 0)}")
            print(f"   Completed: {info.get('complete', 0)}")
            print(f"   Failed: {info.get('failed', 0)}")
        except Exception as info_error:
            print(f"\n2. Redis Queue Info:")
            print(f"   ⚠️  Could not retrieve queue info: {str(info_error)}")
            print(f"   (This is okay - queue info may not be available in all ARQ versions)")
        
        # Check registered functions
        from app.workers.worker import WorkerSettings
        settings = WorkerSettings()
        print(f"\n3. Registered Worker Functions:")
        for func in settings.functions:
            print(f"   ✅ {func.__name__}")
        
        # Close pool using correct async method
        await pool.aclose()
        
        print("\n" + "=" * 80)
        print("✅ All checks passed! Worker should be able to run.")
        print("\nTo start the worker, run:")
        print("   python run_worker.py")
        print("=" * 80)
        
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        print("\n" + "=" * 80)
        print("❌ Setup check failed!")
        print("Please ensure:")
        print("  1. Redis is running")
        print("  2. Redis connection settings are correct")
        print("  3. Environment variables are set correctly")
        print("=" * 80)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(check_worker_setup())

