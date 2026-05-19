# ==============================================================================
# Database Engine & Session Factory
# ==============================================================================
#
# Sets up the SQLAlchemy engine from the DATABASE_URL environment variable and
# provides a `get_db` dependency for FastAPI route handlers. The declarative
# Base lives here so that models.py can import it without circular deps.

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def get_db():
    """FastAPI dependency that yields a database session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
