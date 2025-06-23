"""
Brain_Net FastAPI Backend Application
Main application entry point with health checks for all database services.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import logging
from typing import Dict, Any

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1.router import api_router
from app.services.health import HealthService
from app.core.database import DatabaseManager

# Import SQLModel for table creation
from apps.shared.models import User  # Import to register the model
from sqlmodel import SQLModel

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    logger.info("Starting Brain_Net Backend Application...")
    
    # Initialize database connections
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    # Create database tables using SQLModel
    async with db_manager.postgres_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    # Store in app state for access in routes
    app.state.db_manager = db_manager
    app.state.health_service = HealthService(db_manager)
    
    logger.info("Application startup complete")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Brain_Net Backend Application...")
    await db_manager.close_all()
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Brain_Net API",
    description="An intelligent and highly visualized RAG system for local knowledge base management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with basic application information."""
    return {
        "message": "Welcome to Brain_Net API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "timestamp": settings.get_current_timestamp()}


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check for all services."""
    try:
        health_service: HealthService = app.state.health_service
        health_status = await health_service.check_all_services()
        
        # Determine overall status
        overall_status = "healthy"
        if any(not service["healthy"] for service in health_status.values()):
            overall_status = "degraded"
        if all(not service["healthy"] for service in health_status.values()):
            overall_status = "unhealthy"
        
        return {
            "status": overall_status,
            "timestamp": settings.get_current_timestamp(),
            "services": health_status
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Health check failed")


@app.get("/health/postgres")
async def postgres_health():
    """PostgreSQL database health check."""
    try:
        health_service: HealthService = app.state.health_service
        status = await health_service.check_postgres()
        return status
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="PostgreSQL health check failed")


@app.get("/health/elasticsearch")
async def elasticsearch_health():
    """Elasticsearch health check."""
    try:
        health_service: HealthService = app.state.health_service
        status = await health_service.check_elasticsearch()
        return status
    except Exception as e:
        logger.error(f"Elasticsearch health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Elasticsearch health check failed")


@app.get("/health/neo4j")
async def neo4j_health():
    """Neo4j database health check."""
    try:
        health_service: HealthService = app.state.health_service
        status = await health_service.check_neo4j()
        return status
    except Exception as e:
        logger.error(f"Neo4j health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Neo4j health check failed")


@app.get("/health/minio")
async def minio_health():
    """MinIO object storage health check."""
    try:
        health_service: HealthService = app.state.health_service
        status = await health_service.check_minio()
        return status
    except Exception as e:
        logger.error(f"MinIO health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="MinIO health check failed")


@app.get("/health/redis")
async def redis_health():
    """Redis cache health check."""
    try:
        health_service: HealthService = app.state.health_service
        status = await health_service.check_redis()
        return status
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Redis health check failed")


# Include API routes
app.include_router(api_router, prefix="/api/v1")


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# source .env && export BACKEND_PORT=8882 && python -m apps.backend.main
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.BACKEND_RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )