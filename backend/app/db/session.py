"""
Database engine and session management.

Single engine instance for the app lifetime. get_db() is a FastAPI
dependency that yields a session per-request and guarantees it's closed
afterward, even on exceptions.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # avoids stale-connection errors after idle periods
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


def get_db():
    """
    FastAPI dependency. Usage in a route:

        @router.get("/something")
        def handler(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()