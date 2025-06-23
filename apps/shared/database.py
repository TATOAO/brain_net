"""
Database configuration for SQLModel.
"""

from sqlmodel import SQLModel, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator


def create_db_engine(database_url: str, echo: bool = False):
    """Create SQLAlchemy engine for SQLModel."""
    return create_engine(database_url, echo=echo)


def create_async_db_engine(database_url: str, echo: bool = False, **kwargs):
    """Create async SQLAlchemy engine for SQLModel."""
    return create_async_engine(database_url, echo=echo, **kwargs)


def create_tables(engine):
    """Create all tables defined in SQLModel models."""
    SQLModel.metadata.create_all(engine)


async def create_tables_async(engine):
    """Create all tables defined in SQLModel models asynchronously."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session(session_factory) -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with session_factory() as session:
        yield session 