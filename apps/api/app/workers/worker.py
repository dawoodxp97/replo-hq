import os
import logging
import sys

# Configure logging with a format that includes timestamp and level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

from arq.connections import RedisSettings
from .tutorial_worker import generate_tutorial_task
from arq import create_pool

from ..core.config import settings

_redis_password = (
    settings.redis_password.get_secret_value() if settings.redis_password else None
)

class WorkerSettings:
    functions = [generate_tutorial_task]
    redis_settings = RedisSettings(
        host=settings.redis_host,
        port=settings.redis_port,
        password=_redis_password,
        database=settings.redis_db,
    )
    
    max_jobs = 10
    job_timeout = 3600
    
    async def startup(self, ctx):
        logger.info("ARQ Worker Starting Up...")
        logger.info(
            "Redis config: host=%s port=%s db=%s",
            settings.redis_host,
            settings.redis_port,
            settings.redis_db,
        )

    async def shutdown(self, ctx):
        logger.info("ARQ Worker Shutting Down...")

async def get_redis_pool():
    return await create_pool(WorkerSettings.redis_settings)
