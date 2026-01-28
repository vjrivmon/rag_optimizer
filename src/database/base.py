"""
SQLAlchemy declarative base and session management.

Provides:
- Declarative base for all models
- Session factory with connection pooling
- Database initialization helpers
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import os
from typing import Generator

# Database URL from environment variable
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://chatbot_user:chatbot_password@localhost:5432/chatbot_dni'
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,              # Connections to keep open
    max_overflow=20,           # Extra connections when pool is full
    pool_pre_ping=True,        # Verify connection before using
    pool_recycle=3600,         # Recycle connections after 1 hour
    echo=False,                # Set to True for SQL logging
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,  # ← CRÍTICO: Evita que objetos expiren después de commit
)

# Declarative base for all models
Base = declarative_base()


def get_session() -> Session:
    """
    Get a new database session.

    Returns:
        Session: SQLAlchemy session

    Example:
        ```python
        session = get_session()
        try:
            user = session.query(User).filter_by(telegram_user_id=123).first()
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
        ```
    """
    return SessionLocal()


@contextmanager
def get_session_context() -> Generator[Session, None, None]:
    """
    Get a database session as a context manager (auto-cleanup).

    Yields:
        Session: SQLAlchemy session

    Example:
        ```python
        with get_session_context() as session:
            user = session.query(User).filter_by(telegram_user_id=123).first()
            session.commit()
        # Session is automatically closed
        ```
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """
    Initialize database (create all tables).

    This should be called AFTER Alembic migrations in production.
    Use only for testing or initial setup.

    Example:
        ```python
        from src.database.base import init_db
        from src.database import models  # Import models to register them

        init_db()  # Creates all tables
        ```
    """
    # Import all models to register them with Base
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def drop_all_tables() -> None:
    """
    Drop all tables from database.

    **DANGER:** This will delete all data!
    Use only in tests or development.
    """
    Base.metadata.drop_all(bind=engine)
