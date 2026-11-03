from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import settings


# Create database connection
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}
)


# Create database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# Base class for database models
class Base(DeclarativeBase):
    pass


# Provide database sessions to API endpoints
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()