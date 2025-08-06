"""Elasticsearch database routes."""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from app.core.database import DatabaseManager
from app.services.database_api import DatabaseAPIService
from app.services.permissions import PermissionManager
from app.services.sandbox_auth import get_current_sandbox_user
from app.schemas.database import (
    ElasticsearchRequest, ElasticsearchResponse,
    ExecutionContext
)

router = APIRouter(prefix="/elasticsearch", tags=["elasticsearch"])


# Dependency to get database manager
async def get_database_manager() -> DatabaseManager:
    """Get database manager from app state."""
    # This would typically be injected from app state
    # For now, create a new instance
    from app.core.database import DatabaseManager
    return DatabaseManager()


# Dependency to get permission manager
async def get_permission_manager(
    db_manager: DatabaseManager = Depends(get_database_manager)
) -> PermissionManager:
    """Get permission manager instance."""
    return PermissionManager(db_manager)


# Dependency to get database API service
async def get_database_api_service(
    db_manager: DatabaseManager = Depends(get_database_manager),
    permission_manager: PermissionManager = Depends(get_permission_manager)
) -> DatabaseAPIService:
    """Get database API service instance."""
    return DatabaseAPIService(db_manager, permission_manager)


@router.post("/search", response_model=ElasticsearchResponse)
async def elasticsearch_search(
    request: ElasticsearchRequest,
    current_user: Dict = Depends(get_current_sandbox_user),
    db_service: DatabaseAPIService = Depends(get_database_api_service)
):
    """Execute Elasticsearch search with user context."""
    
    try:
        execution_context = ExecutionContext(
            user_id=current_user["user_id"],
            execution_id=current_user["execution_id"],
            **request.execution_context.dict() if request.execution_context else {}
        )
        
        result = await db_service.elasticsearch_search(
            user_id=current_user["user_id"],
            index=request.index,
            query=request.query,
            size=request.size,
            from_=request.from_,
            execution_context=execution_context
        )
        
        return result
        
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Elasticsearch operation failed: {str(e)}")


@router.post("/index")
async def elasticsearch_index(
    request: Dict[str, Any],
    current_user: Dict = Depends(get_current_sandbox_user),
    db_service: DatabaseAPIService = Depends(get_database_api_service)
):
    """Index document in Elasticsearch with user context."""
    
    try:
        index = request.get("index")
        document = request.get("document")
        doc_id = request.get("id")
        
        if not index or not document:
            raise HTTPException(status_code=400, detail="Index and document are required")
        
        # Add user context to document
        document["user_id"] = current_user["user_id"]
        
        # Ensure index is user-scoped
        scoped_index = f"user_{current_user['user_id']}_{index}"
        
        # Execute indexing
        es_client = db_service.db_manager.elasticsearch
        result = await es_client.index(
            index=scoped_index,
            body=document,
            id=doc_id
        )
        
        return {
            "success": True,
            "index": scoped_index,
            "id": result["_id"],
            "version": result["_version"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Elasticsearch indexing failed: {str(e)}")


@router.post("/save-vectors")
async def save_vectors(
    request: Dict[str, Any],
    current_user: Dict = Depends(get_current_sandbox_user),
    db_service: DatabaseAPIService = Depends(get_database_api_service)
):
    """Save vectors to Elasticsearch."""
    
    try:
        collection_name = request.get("collection_name")
        vectors = request.get("vectors", [])
        
        if not collection_name or not vectors:
            raise HTTPException(status_code=400, detail="Collection name and vectors are required")
        
        # User-scoped index
        index = f"user_{current_user['user_id']}_vectors_{collection_name}"
        
        # Index each vector
        es_client = db_service.db_manager.elasticsearch
        indexed_count = 0
        
        for vector_data in vectors:
            # Add user context
            vector_data["user_id"] = current_user["user_id"]
            vector_data["execution_id"] = current_user["execution_id"]
            
            await es_client.index(
                index=index,
                body=vector_data
            )
            indexed_count += 1
        
        return {
            "success": True,
            "indexed_count": indexed_count,
            "collection_name": collection_name,
            "index": index
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save vectors: {str(e)}") 