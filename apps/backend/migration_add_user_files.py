"""
Migration script to add user_files table for file ownership tracking.
Run this script to update the database schema.
"""

import asyncio
from sqlalchemy import text
from app.core.database import DatabaseManager
from apps.shared.models import UserFile
from sqlmodel import SQLModel

async def migrate_database():
    """Add user_files table to the database."""
    db_manager = DatabaseManager()
    
    try:
        # Initialize database connections
        await db_manager.initialize()
        
        # Create tables
        async with db_manager.postgres_engine.begin() as conn:
            # Create the user_files table
            await conn.run_sync(SQLModel.metadata.create_all)
            print("✅ user_files table created successfully")
        
        print("✅ Migration completed!")
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        raise
    finally:
        await db_manager.close_all()

if __name__ == "__main__":
    asyncio.run(migrate_database()) 