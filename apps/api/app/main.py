from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .core.config import settings
from .core.exceptions import register_exception_handlers
from .core.logging import configure_logging
from .core.middleware import RequestIDMiddleware
from .db.session import AsyncSessionLocal, async_engine
from .routers import (
    author,
    dashboard,
    notification,
    progress,
    repo,
    search,
    tutorial,
    user,
)

# Aliased: the module name collides with the `settings` config object above,
# and a bare `from .routers import settings` silently shadowed it.
from .routers import settings as settings_router
from .workers.worker import get_redis_pool

# Installs the secret-redaction filter before the app can emit a record.
configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown. Replaces the deprecated @app.on_event hooks, which
    could not dispose the async engine — that leaks connections on reload and
    on every redeploy."""
    app.state.redis_pool = await get_redis_pool()
    yield
    if getattr(app.state, "redis_pool", None) is not None:
        app.state.redis_pool.close()
        await app.state.redis_pool.wait_closed()
    await async_engine.dispose()


app = FastAPI(
    title="AI Code Tutorial Generator API",
    description="API for analyzing GitHub repos and generating tutorials.",
    version="0.1.0",
    lifespan=lifespan,
)

register_exception_handlers(app)

# Middleware runs in reverse registration order, so RequestIDMiddleware being
# added last puts it outermost — the request id is therefore set before CORS or
# any handler runs, and is available to every log line and error body.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)
app.add_middleware(RequestIDMiddleware)

app.include_router(repo.router, prefix="/api/repo", tags=["Repository"])
app.include_router(tutorial.router, prefix="/api/tutorial", tags=["Tutorials"])
app.include_router(user.router, prefix="/api/user", tags=["User"])
app.include_router(progress.router, prefix="/api/progress", tags=["Progress"])
app.include_router(author.router, prefix="/api/author", tags=["Authoring"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["Settings"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(notification.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])


@app.get("/api/health", tags=["Health"])
async def get_health():
    """Liveness: the process is up. Deliberately touches nothing external, so a
    database blip cannot make the orchestrator restart a healthy container."""
    return {"status": "ok"}


@app.get("/api/ready", tags=["Health"])
async def get_ready():
    """Readiness: dependencies are reachable. This is what a load balancer
    should poll before routing traffic."""
    checks: dict[str, str] = {}
    healthy = True

    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {type(exc).__name__}"
        healthy = False

    try:
        pool = getattr(app.state, "redis_pool", None)
        if pool is None:
            raise RuntimeError("redis pool not initialised")
        await pool.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error: {type(exc).__name__}"
        healthy = False

    return {"status": "ok" if healthy else "degraded", "checks": checks}
