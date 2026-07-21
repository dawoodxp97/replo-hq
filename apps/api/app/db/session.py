"""Database engines and session factories.

Two stacks live here **during Phase 2 only**:

- `get_async_db` / `AsyncSessionLocal` — the target. AsyncSession over asyncpg.
- `get_db` / `SessionLocal` — legacy sync, kept alive so the app keeps working
  while routers are converted one domain at a time.

Every router still on `get_db` is unconverted work. When the last one flips, the
sync half of this module and the `psycopg2` dependency go away (Alembic keeps
using `settings.sqlalchemy_url`, but builds its own engine).

Why this conversion matters: every `db.query(...)` inside an `async def` blocks
the event loop. In the API that serialises concurrent requests; in the worker it
serialises jobs that are already slow because they wait on an LLM.
"""

from collections.abc import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from ..core.config import settings

Base = declarative_base()

# --- Async (target) ---------------------------------------------------------

async_engine = create_async_engine(
    settings.async_sqlalchemy_url,
    # Managed Postgres drops idle connections aggressively; without this a
    # pooled connection can be handed out already closed.
    pool_pre_ping=True,
    echo=settings.debug,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an AsyncSession.

    Rolls back on exception so a failed request cannot leave a half-applied
    transaction on a pooled connection for the next caller to inherit.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


# --- Sync (legacy, being removed) -------------------------------------------

engine = create_engine(
    settings.sqlalchemy_url,
    pool_pre_ping=True,
    echo=settings.debug,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Legacy sync dependency. Do not use in new code — see get_async_db."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
