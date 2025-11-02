# ./backend/app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Import your routers
from .routers import repo, tutorial, user, author, progress, settings

# Import worker
from .workers.worker import get_redis_pool

# Load environment variables
load_dotenv()

app = FastAPI(
    title="AI Code Tutorial Generator API",
    description="API for analyzing GitHub repos and generating tutorials.",
    version="0.1.0"
)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include Routers ---
# Include each feature router with a prefix
app.include_router(repo.router, prefix="/api/repo", tags=["Repository"])
app.include_router(tutorial.router, prefix="/api/tutorial", tags=["Tutorials"])
app.include_router(user.router, prefix="/api/user", tags=["User"])
app.include_router(progress.router, prefix="/api/progress", tags=["Progress"])
app.include_router(author.router, prefix="/api/author", tags=["Authoring"])
app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])

# --- API Health Check ---
@app.get("/api/health", tags=["Health"])
def get_health():
    """
    Health check endpoint.
    """
    return {"status": "ok", "message": "Backend is running!"}

# --- Redis & Worker Initialization ---
@app.on_event("startup")
async def startup_event():
    """
    Initialize Redis connection pool on startup.
    """
    app.state.redis_pool = await get_redis_pool()
    print("Redis connection pool initialized.")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Close Redis connection pool on shutdown.
    """
    if hasattr(app.state, "redis_pool"):
        app.state.redis_pool.close()
        await app.state.redis_pool.wait_closed()
        print("Redis connection pool closed.")



# --- Root & Health Check ---
@app.get("/api/v1/health", tags=["Health"])
def get_health():
    """
    Health check endpoint.
    """
    return {"status": "ok", "message": "Backend is running!"}

# --- Database & Worker Initialization ---
# @app.on_event("startup")
# async def startup_event():
#     # This is where you'll initialize DB connections, Redis pools, etc.
#     print("Starting up API...")

# @app.on_event("shutdown")
# async def shutdown_event():
#     print("Shutting down API...")