"""
API Router for Brain_Net Backend v1
Contains all API endpoints for the application.
"""

from fastapi import APIRouter

# Import route modules here when they're created
# from app.api.v1.routes import documents, queries, health

api_router = APIRouter()

# Include route modules here when they're created
# api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
# api_router.include_router(queries.router, prefix="/queries", tags=["queries"])
# api_router.include_router(health.router, prefix="/health", tags=["health"])

@api_router.get("/")
async def api_root():
    """API root endpoint."""
    return {
        "message": "Brain_Net API v1",
        "version": "1.0.0",
        "status": "operational"
    } 