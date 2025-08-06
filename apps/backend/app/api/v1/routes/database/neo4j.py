"""Neo4j database routes."""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from app.core.database import DatabaseManager
from app.services.database_api import DatabaseAPIService
from app.services.permissions import PermissionManager
from app.services.sandbox_auth import get_current_sandbox_user
from app.schemas.database import (
    Neo4jQueryRequest, Neo4jQueryResponse,
    ExecutionContext
)

router = APIRouter(prefix="/neo4j", tags=["neo4j"])


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


@router.post("/query", response_model=Neo4jQueryResponse)
async def execute_neo4j_query(
    request: Neo4jQueryRequest,
    current_user: Dict = Depends(get_current_sandbox_user),
    db_service: DatabaseAPIService = Depends(get_database_api_service)
):
    """Execute Neo4j query with user context."""
    
    try:
        execution_context = ExecutionContext(
            user_id=current_user["user_id"],
            execution_id=current_user["execution_id"],
            **request.execution_context.dict() if request.execution_context else {}
        )
        
        result = await db_service.execute_neo4j_query(
            user_id=current_user["user_id"],
            query=request.query,
            params=request.params,
            database=request.database,
            execution_context=execution_context
        )
        
        return result
        
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Neo4j operation failed: {str(e)}")


@router.post("/save-relationships")
async def save_relationships(
    request: Dict[str, Any],
    current_user: Dict = Depends(get_current_sandbox_user),
    db_service: DatabaseAPIService = Depends(get_database_api_service)
):
    """Save relationships to Neo4j."""
    
    try:
        relationships = request.get("relationships", [])
        
        if not relationships:
            raise HTTPException(status_code=400, detail="Relationships are required")
        
        # Create relationships with user context
        results = []
        for rel in relationships:
            query = """
                MERGE (a:Node {id: $from_id, user_id: $user_id})
                MERGE (b:Node {id: $to_id, user_id: $user_id})
                MERGE (a)-[r:$rel_type {user_id: $user_id, execution_id: $execution_id}]->(b)
                SET r.properties = $properties
                RETURN r
            """
            
            params = {
                "from_id": rel.get("from_id"),
                "to_id": rel.get("to_id"),
                "rel_type": rel.get("relationship_type"),
                "properties": rel.get("properties", {}),
                "user_id": current_user["user_id"],
                "execution_id": current_user["execution_id"]
            }
            
            result = await db_service.execute_neo4j_query(
                user_id=current_user["user_id"],
                query=query,
                params=params
            )
            
            results.append(result)
        
        return {
            "success": True,
            "relationships_created": len(results),
            "details": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save relationships: {str(e)}") 