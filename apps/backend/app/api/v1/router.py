"""
API Router for Brain_Net Backend v1
Contains all API endpoints for the application.
"""

from fastapi import APIRouter

# Import route modules
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.upload import router as upload_router
from app.api.v1.routes.processors import router as processors_router
from app.api.v1.routes.sandbox import router as sandbox_router
from app.api.v1.routes.database import router as database_router

api_router = APIRouter()

# Include route modules
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(upload_router, prefix="/upload", tags=["upload"])
api_router.include_router(processors_router, tags=["processors"])
api_router.include_router(sandbox_router, tags=["sandbox"])
api_router.include_router(database_router, prefix="/db", tags=["database"])

@api_router.get("/")
async def api_root():
    """API root endpoint."""
    return {
        "message": "Brain_Net API v1",
        "version": "1.0.0",
        "status": "operational",
        "available_endpoints": [
            "/auth - Authentication endpoints",
            "/upload - File upload endpoints", 
            "/processors - Processor and pipeline management endpoints",
            "/sandbox - Python sandbox environment for AI agents"
            "/db - Database API endpoints for secure sandbox access"
        ]
    } 