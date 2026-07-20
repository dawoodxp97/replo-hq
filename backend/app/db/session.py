from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus

import os

# Read from environment when available, fallback to local default
# For Docker: use DATABASE_URL from docker-compose
# For local dev: build from individual POSTGRES_* variables
database_url = os.getenv("DATABASE_URL")
if not database_url:
    # Build connection string from individual variables
    # URL-encode password to handle special characters like @, #, etc.
    postgres_user = os.getenv("POSTGRES_USER", "tutorial_user")
    postgres_password = quote_plus(os.getenv("POSTGRES_PASSWORD", "tutorial_password"))
    postgres_db = os.getenv("POSTGRES_DB", "tutorial_db")
    postgres_host = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port = os.getenv("POSTGRES_PORT", "5432")
    database_url = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"

SQLALCHEMY_DATABASE_URL = database_url

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()