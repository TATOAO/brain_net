"""
Brain_Net LLM Service
Main application entry point for AI/ML operations including RAG, chatbots, and agents.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    logger.info("Starting Brain_Net LLM Service...")
    
    # Initialize OpenTelemetry first
    initialize_telemetry()
    
    # Initialize database connections
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    # Store in app state for access in routes
    app.state.db_manager = db_manager
    app.state.health_service = HealthService(db_manager)
    
    logger.info("LLM Service startup complete")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Brain_Net LLM Service...")
    await db_manager.close_all()
    logger.info("LLM Service shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Brain_Net LLM Service",
    description="AI/ML service for RAG, chatbots, and intelligent agents",
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

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint with basic application information."""
    return {
        "message": "Welcome to Brain_Net LLM Service",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "capabilities": [
            "RAG (Retrieval Augmented Generation)",
            "Chat Completion",
            "Document Processing",
            "Embedding Generation",
            "Agent-based Tasks"
        ]
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
        
        return {
            "status": "healthy",
            "timestamp": settings.get_current_timestamp(),
            "services": health_status,
            "llm_status": {
                "models_loaded": await health_service.check_models(),
                "vector_store_ready": await health_service.check_vector_store(),
                "embedding_service_ready": await health_service.check_embedding_service()
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Health check failed")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    ) 