#!/usr/bin/env python
# ./backend/run_worker.py
import os
import sys
import asyncio
from arq.worker import Worker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the worker settings
from app.workers.worker import WorkerSettings

async def main():
    """
    Run the ARQ worker.
    """
    print("Starting ARQ worker...")
    # Instantiate WorkerSettings to bind startup/shutdown methods
    settings = WorkerSettings()
    # Instantiate Worker with explicit arguments for arq==0.25.0
    worker = Worker(
        functions=settings.functions,
        redis_settings=settings.redis_settings,
        max_jobs=settings.max_jobs,
        job_timeout=settings.job_timeout,
        on_startup=settings.startup,
        on_shutdown=settings.shutdown,
    )
    await worker.async_run()

if __name__ == "__main__":
    asyncio.run(main())