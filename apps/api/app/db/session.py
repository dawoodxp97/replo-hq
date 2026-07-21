from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from ..core.config import settings

# Connection details are resolved in Settings.sqlalchemy_url: DATABASE_URL wins
# when present (Railway, docker-compose), otherwise it is built from the
# POSTGRES_* parts with the password URL-encoded.
engine = create_engine(
    settings.sqlalchemy_url,
    # Recycle dead connections instead of handing a closed socket to a request.
    # Managed Postgres providers drop idle connections aggressively.
    pool_pre_ping=True,
    echo=settings.debug,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# sqlalchemy.ext.declarative.declarative_base is deprecated in 2.0.
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
