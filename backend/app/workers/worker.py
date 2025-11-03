# ./backend/app/workers/worker.py
import os
import logging
from arq import create_pool
from arq.connections import RedisSettings
from arq.worker import Worker, Function

from .analysis_worker import process_repository_analysis, generate_tutorial

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis connection settings
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
REDIS_DB = int(os.getenv('REDIS_DB', 0))

# ARQ worker settings
class WorkerSettings:
    """Settings for the ARQ worker."""
    redis_settings = RedisSettings(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        database=REDIS_DB
    )
    
    # Register functions to be available to the queue
    # Use direct callable registration to avoid ARQ Function signature conflicts
    functions = [
        process_repository_analysis,
        generate_tutorial,
    ]
    
    # Job execution settings
    max_jobs = 10
    job_timeout = 3600  # 1 hour timeout for long-running jobs
    
    # Startup and shutdown handlers
    async def startup(self, ctx):
        """Called when the worker starts up."""
        logger.info('Worker starting up...')
    
    async def shutdown(self, ctx):
        """Called when the worker shuts down."""
        logger.info('Worker shutting down...')

# Function to create a Redis pool for enqueueing jobs
async def get_redis_pool():
    """Create and return a Redis connection pool."""
    return await create_pool(
        RedisSettings(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            database=REDIS_DB
        )
    )