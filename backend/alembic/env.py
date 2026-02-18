"""
Alembic environment configuration for async SQLAlchemy.

This file configures how Alembic runs migrations. Key features:
- Async support for SQLAlchemy 2.0
- Imports all models so autogenerate can detect schema changes
- Gets database URL from our settings (not hardcoded)
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import our Base and all models for autogenerate support
# Models must be imported so Alembic can see their table definitions
from app.core.database import Base
from app.core.config import settings

# Import all models here - Alembic needs to see them for autogenerate
from app.models.pantry import PantryItem  # noqa: F401
from app.models.recipe import Recipe  # noqa: F401
from app.models.receipt import ReceiptItem  # noqa: F401

# Alembic Config object - provides access to .ini file values
config = context.config

# Set the database URL from our settings (not from alembic.ini)
# This uses the async driver (aiosqlite for SQLite, asyncpg for PostgreSQL)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Set up Python logging from the config file
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# MetaData object for autogenerate support
# This tells Alembic what our "desired" schema looks like
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    
    This generates SQL scripts without connecting to the database.
    Useful for reviewing migrations before applying them.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Configure the migration context and run migrations.
    
    This is called within a connection context, allowing
    Alembic to perform the actual migration operations.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # Compare types (e.g., String(50) vs String(100))
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations using async engine.
    
    This creates an async engine, connects to the database,
    and runs migrations within that connection.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode (connected to database).
    
    Uses asyncio to run the async migration function.
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
