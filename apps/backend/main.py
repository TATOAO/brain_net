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
from app.core.telemetry import initialize_telemetry, get_tracer, get_meter
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
    
    # Initialize OpenTelemetry first
    initialize_telemetry(app)
    
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
        db_manager: DatabaseManager = app.state.db_manager
        
        # Determine overall status based on required vs optional services
        healthy_required = all(
            health_status.get(service, {}).get("healthy", False) 
            for service in settings.REQUIRED_SERVICES
        )
        
        if healthy_required:
            # Check if any optional services are down
            unhealthy_optional = any(
                not health_status.get(service, {}).get("healthy", False)
                for service in settings.OPTIONAL_SERVICES
            )
            overall_status = "degraded" if unhealthy_optional else "healthy"
        else:
            overall_status = "unhealthy"
        
        return {
            "status": overall_status,
            "timestamp": settings.get_current_timestamp(),
            "services": health_status,
            "service_classification": {
                "required_services": settings.REQUIRED_SERVICES,
                "optional_services": settings.OPTIONAL_SERVICES,
                "available_services": db_manager._get_available_services(),
                "failed_services": list(db_manager.get_failed_services())
            }
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
        status["service_type"] = "required"
        return status
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="PostgreSQL health check failed")


@app.get("/health/elasticsearch")
async def elasticsearch_health():
    """Elasticsearch health check."""
    try:
        db_manager: DatabaseManager = app.state.db_manager
        if "elasticsearch" in db_manager.get_failed_services():
            return {
                "healthy": False,
                "message": "Elasticsearch is not available (failed to initialize)",
                "service_type": "optional",
                "timestamp": settings.get_current_timestamp()
            }
        
        health_service: HealthService = app.state.health_service
        status = await health_service.check_elasticsearch()
        status["service_type"] = "optional"
        return status
    except Exception as e:
        logger.error(f"Elasticsearch health check failed: {str(e)}")
        return {
            "healthy": False,
            "message": f"Elasticsearch health check failed: {str(e)}",
            "service_type": "optional",
            "timestamp": settings.get_current_timestamp()
        }


@app.get("/health/neo4j")
async def neo4j_health():
    """Neo4j database health check."""
    try:
        db_manager: DatabaseManager = app.state.db_manager
        if "neo4j" in db_manager.get_failed_services():
            return {
                "healthy": False,
                "message": "Neo4j is not available (failed to initialize)",
                "service_type": "optional",
                "timestamp": settings.get_current_timestamp()
            }
        
        health_service: HealthService = app.state.health_service
        status = await health_service.check_neo4j()
        status["service_type"] = "optional"
        return status
    except Exception as e:
        logger.error(f"Neo4j health check failed: {str(e)}")
        return {
            "healthy": False,
            "message": f"Neo4j health check failed: {str(e)}",
            "service_type": "optional",
            "timestamp": settings.get_current_timestamp()
        }


@app.get("/health/minio")
async def minio_health():
    """MinIO object storage health check."""
    try:
        db_manager: DatabaseManager = app.state.db_manager
        if "minio" in db_manager.get_failed_services():
            return {
                "healthy": False,
                "message": "MinIO is not available (failed to initialize)",
                "service_type": "optional",
                "timestamp": settings.get_current_timestamp()
            }
        
        health_service: HealthService = app.state.health_service
        status = await health_service.check_minio()
        status["service_type"] = "optional"
        return status
    except Exception as e:
        logger.error(f"MinIO health check failed: {str(e)}")
        return {
            "healthy": False,
            "message": f"MinIO health check failed: {str(e)}",
            "service_type": "optional",
            "timestamp": settings.get_current_timestamp()
        }


@app.get("/health/redis")
async def redis_health():
    """Redis cache health check."""
    try:
        db_manager: DatabaseManager = app.state.db_manager
        if "redis" in db_manager.get_failed_services():
            return {
                "healthy": False,
                "message": "Redis is not available (failed to initialize)",
                "service_type": "optional",
                "timestamp": settings.get_current_timestamp()
            }
        
        health_service: HealthService = app.state.health_service
        status = await health_service.check_redis()
        status["service_type"] = "optional"
        return status
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return {
            "healthy": False,
            "message": f"Redis health check failed: {str(e)}",
            "service_type": "optional",
            "timestamp": settings.get_current_timestamp()
        }


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