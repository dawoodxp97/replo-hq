"""Test configuration.

Two tiers, per the Phase 6 plan:

- **Unit tests** run everywhere. No containers, no network — they exercise the
  pure logic (contracts, retry, retention caps, tickets, rate-limit windowing
  against a fake Redis).
- **Integration tests** (marked `integration`) start real Postgres/Redis via
  testcontainers. They skip themselves when Docker is unavailable, so the
  default local run is green on any laptop while CI (which has Docker) runs
  everything.

Environment is pinned *before* app modules are imported: `core.config.settings`
is instantiated at import time and cached, so env vars that must differ from the
developer's `.env` (e.g. `ENVIRONMENT=test`, which keeps Sentry off) are set
here, at the top.
"""

import os

import pytest

os.environ["ENVIRONMENT"] = "test"


def _docker_reachable() -> bool:
    """Cheap probe before paying testcontainers' startup cost."""
    import shutil
    import subprocess

    docker = shutil.which("docker")
    if docker is None:
        return False
    try:
        result = subprocess.run(  # noqa: S603 - fixed argv, no shell
            [docker, "info", "--format", "{{.ServerVersion}}"],
            capture_output=True,
            timeout=15,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


@pytest.fixture(scope="session")
def postgres_url(request):
    """Async URL for a throwaway Postgres. Skips the requesting tests when
    Docker is down rather than failing them."""
    if not _docker_reachable():
        pytest.skip("Docker is not available; skipping integration tests")

    from testcontainers.postgres import PostgresContainer

    try:
        with PostgresContainer("postgres:15-alpine") as container:
            # testcontainers reports a psycopg2 URL by default; the app speaks
            # asyncpg. Only the driver segment differs.
            url = container.get_connection_url().replace(
                "postgresql+psycopg2://", "postgresql+asyncpg://"
            )
            yield url
    except Exception as exc:  # noqa: BLE001 - any container failure is a skip
        pytest.skip(f"Postgres container could not start: {exc}")


@pytest.fixture(scope="session")
def redis_url(request):
    if not _docker_reachable():
        pytest.skip("Docker is not available; skipping integration tests")

    from testcontainers.redis import RedisContainer

    try:
        with RedisContainer("redis:7-alpine") as container:
            # RedisContainer exposes no get_connection_url in testcontainers 4.x;
            # assemble it from the mapped host/port.
            yield f"redis://{container.get_container_host_ip()}:{container.get_exposed_port(6379)}/0"
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Redis container could not start: {exc}")


@pytest.fixture()
async def db(postgres_url):
    """An async session over a schema built straight from the models.

    `metadata.create_all` rather than alembic: these tests exercise code paths,
    not the migration chain — CI applies migrations separately to prove they
    run. Tables are dropped at teardown so tests are order-independent.
    """
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    import app.models  # noqa: F401 - register every model on Base.metadata
    from app.db.session import Base

    engine = create_async_engine(postgres_url)
    async with engine.begin() as conn:
        # pg_trgm backs the search indexes declared on the models; the
        # testcontainers image ships the extension but does not enable it.
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        # Drop first: rows from one test must never be visible to the next.
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session

    await engine.dispose()


@pytest.fixture()
async def redis_pool(redis_url):
    """A real Redis client, shaped like the app's arq pool for the rate limiter."""
    import redis.asyncio as redis

    client = redis.from_url(redis_url, decode_responses=True)
    await client.flushdb()
    yield client
    await client.aclose()
