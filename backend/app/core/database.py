"""
Database configuration and session management.

This module sets up SQLAlchemy's async engine, session factory,
and provides the Base class for all ORM models.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# Create async engine
# - echo=True logs SQL queries (useful for debugging, disable in production)
# - future=True enables SQLAlchemy 2.0 style usage
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL in debug mode
    future=True,
)

# Session factory
# - expire_on_commit=False keeps objects usable after commit (important for async)
# - autoflush=False gives us explicit control over when changes are sent to DB
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.
    
    All models inherit from this class. It provides:
    - Automatic table name generation (can be overridden)
    - Common metadata for all tables
    - Foundation for Alembic migrations
    """
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session for each request.
    
    Usage in FastAPI:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    
    The session is automatically closed when the request completes,
    even if an exception occurs (thanks to the finally block).
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """
    Create all tables in the database.
    
    This is useful for development/testing. In production,
    use Alembic migrations instead for proper version control
    of schema changes.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables() -> None:
    """
    Drop all tables in the database.
    
    WARNING: This destroys all data! Only use in testing.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
