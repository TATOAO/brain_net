"""Database routes package."""

from fastapi import APIRouter
from .pg import router as pg_router
from .es import router as es_router
from .neo4j import router as neo4j_router
from .minio import router as minio_router
from .common import router as common_router

# Create main database router
router = APIRouter(prefix="/db", tags=["database"])

# Include all database-specific routers
router.include_router(pg_router)
router.include_router(es_router)
router.include_router(neo4j_router)
router.include_router(minio_router)
router.include_router(common_router)

# Health check endpoint
@router.get("/health")
async def database_health():
    """Health check for database API."""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "message": "Database API is operational"
    } 