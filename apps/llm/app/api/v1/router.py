"""
Main API router for Brain_Net LLM Service v1
"""

from fastapi import APIRouter
from app.api.v1.routes import chat, rag, agents, documents, models, processors

api_router = APIRouter()

# Include all route modules
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(rag.router, prefix="/rag", tags=["rag"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(models.router, prefix="/models", tags=["models"])