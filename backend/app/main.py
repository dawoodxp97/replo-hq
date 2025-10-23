# ./backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import your new routers
from .routers import repo, tutorial, user, author

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
app.include_router(user.router, prefix="/api/user", tags=["User & Progress"])
app.include_router(author.router, prefix="/api/author", tags=["Authoring"])



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