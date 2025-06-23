#!/usr/bin/env python3
"""
Database migration script for Brain_Net Backend
Creates database tables if they don't exist.
"""

import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings

# Import SQLModel for migrations
from apps.shared.models import User  # Import to register the model
from sqlmodel import SQLModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_migrations():
    """Run database migrations."""
    try:
        logger.info("Starting database migrations...")
        
        # Create async engine
        engine = create_async_engine(
            settings.get_database_url(async_driver=True),
            echo=True
        )
        
        # Create all tables using SQLModel
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        
        logger.info("Database migrations completed successfully")
        
        await engine.dispose()
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(run_migrations()) 