from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
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

app = FastAPI(
    title="AI Code Tutorial Generator API",
    description="API for analyzing GitHub repos and generating tutorials.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
def get_health():
    return {"status": "ok", "message": "Backend is running!"}


@app.on_event("startup")
async def startup_event():
    app.state.redis_pool = await get_redis_pool()


@app.on_event("shutdown")
async def shutdown_event():
    if hasattr(app.state, "redis_pool"):
        app.state.redis_pool.close()
        await app.state.redis_pool.wait_closed()
