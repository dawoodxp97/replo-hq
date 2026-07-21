import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",  # Path to your FastAPI app object
        host="0.0.0.0",
        port=8000,
        reload=True      # Enables auto-reload on code changes
    )