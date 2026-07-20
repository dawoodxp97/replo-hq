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

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_PASSWORD_RAW = os.getenv('REDIS_PASSWORD', '')
REDIS_PASSWORD = REDIS_PASSWORD_RAW.strip() if REDIS_PASSWORD_RAW else None
REDIS_DB = int(os.getenv('REDIS_DB', 0))

class WorkerSettings:
    functions = [generate_tutorial_task]
    redis_settings = RedisSettings(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        database=REDIS_DB
    )
    
    max_jobs = 10
    job_timeout = 3600
    
    async def startup(self, ctx):
        logger.info("ARQ Worker Starting Up...")
        logger.info(f"Redis Config: host={REDIS_HOST}, port={REDIS_PORT}, db={REDIS_DB}")

    async def shutdown(self, ctx):
        logger.info("ARQ Worker Shutting Down...")

async def get_redis_pool():
    return await create_pool(WorkerSettings.redis_settings)
