"""
Dependency injection for Brain_Net LLM Service
"""

from fastapi import Depends, Request
from app.services.chat import ChatService
from app.services.rag import RAGService
from app.services.agents import AgentService
from app.services.documents import DocumentService
from app.services.models import ModelService
from app.services.health import HealthService
from app.services.minio_service import MinIOService
from app.core.database import DatabaseManager


def get_database_manager(request: Request) -> DatabaseManager:
    """Get database manager from application state."""
    return request.app.state.db_manager


def get_health_service(request: Request) -> HealthService:
    """Get health service from application state."""
    return request.app.state.health_service


def get_chat_service(
    db_manager: DatabaseManager = Depends(get_database_manager)
) -> ChatService:
    """Get chat service instance."""
    return ChatService(db_manager)


def get_rag_service(
    db_manager: DatabaseManager = Depends(get_database_manager)
) -> RAGService:
    """Get RAG service instance."""
    return RAGService(db_manager)


def get_agent_service(
    db_manager: DatabaseManager = Depends(get_database_manager)
) -> AgentService:
    """Get agent service instance."""
    return AgentService(db_manager)


def get_document_service(
    db_manager: DatabaseManager = Depends(get_database_manager)
) -> DocumentService:
    """Get document service instance."""
    return DocumentService(db_manager)


def get_model_service(
    db_manager: DatabaseManager = Depends(get_database_manager)
) -> ModelService:
    """Get model service instance."""
    return ModelService(db_manager)


def get_minio_service() -> MinIOService:
    """Get MinIO service instance."""
    return MinIOService() 