"""
Database API routes for secure database operations.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Request
from app.core.database import DatabaseManager
from app.services.database_api import DatabaseAPIService
from app.services.permissions import PermissionManager
from app.services.sandbox_auth import get_current_sandbox_user
from app.schemas.database import (
    PostgresQueryRequest, PostgresQueryResponse,
    ElasticsearchRequest, ElasticsearchResponse,
    Neo4jQueryRequest, Neo4jQueryResponse,
    RedisCommandRequest, RedisCommandResponse,
    MinIOOperationRequest, MinIOOperationResponse,
    ExecutionContext, AuditLogEntry
)

router = APIRouter(prefix="/db", tags=["database"])


# Dependency to get database API service
async def get_database_api_service(
    db_manager: DatabaseManager = Depends(),
    permission_manager: PermissionManager = Depends()
) -> DatabaseAPIService:
    """Get database API service instance."""
    return DatabaseAPIService(db_manager, permission_manager)


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


# PostgreSQL Endpoints
@router.post("/postgres/query", response_model=PostgresQueryResponse)
async def execute_postgres_query(
    request: PostgresQueryRequest,
    current_user: Dict = Depends(get_current_sandbox_user),
    db_service: DatabaseAPIService = Depends(get_database_api_service)
):
    """Execute PostgreSQL query with user context and authorization."""
    
    try:
        # Create execution context
        execution_context = ExecutionContext(
            user_id=current_user["user_id"],
            execution_id=current_user["execution_id"],
            **request.execution_context.dict() if request.execution_context else {}
        )
        
        result = await db_service.execute_postgres_query(
            user_id=current_user["user_id"],
            query=request.query,
            params=request.params,
            execution_context=execution_context
        )
        
        return result
        
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database operation failed: {str(e)}")


@router.post("/postgres/batch", response_model=List[PostgresQueryResponse])
async def execute_postgres_batch(
    requests: List[PostgresQueryRequest],
    current_user: Dict = Depends(get_current_sandbox_user),
    db_service: DatabaseAPIService = Depends(get_database_api_service)
):
    """Execute multiple PostgreSQL queries in batch."""
    
    results = []
    for request in requests:
        try:
            execution_context = ExecutionContext(
                user_id=current_user["user_id"],
                execution_id=current_user["execution_id"],
                **request.execution_context.dict() if request.execution_context else {}
            )
            
            result = await db_service.execute_postgres_query(
                user_id=current_user["user_id"],
                query=request.query,
                params=request.params,
                execution_context=execution_context
            )
            results.append(result)
            
        except Exception as e:
            # For batch operations, we include error in response
            results.append(PostgresQueryResponse(
                success=False,
                execution_time=0.0,
                operation_id="",
                data=[],
                row_count=0,
                columns=[]
            ))
    
    return results


# Elasticsearch Endpoints
@router.post("/elasticsearch/search", response_model=ElasticsearchResponse)
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


@router.post("/elasticsearch/index")
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


# Neo4j Endpoints
@router.post("/neo4j/query", response_model=Neo4jQueryResponse)
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


# Redis Endpoints
@router.post("/redis/command", response_model=RedisCommandResponse)
async def execute_redis_command(
    request: RedisCommandRequest,
    current_user: Dict = Depends(get_current_sandbox_user),
    db_service: DatabaseAPIService = Depends(get_database_api_service)
):
    """Execute Redis command with user context."""
    
    try:
        execution_context = ExecutionContext(
            user_id=current_user["user_id"],
            execution_id=current_user["execution_id"],
            **request.execution_context.dict() if request.execution_context else {}
        )
        
        result = await db_service.execute_redis_command(
            user_id=current_user["user_id"],
            command=request.command,
            args=request.args,
            execution_context=execution_context
        )
        
        return result
        
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redis operation failed: {str(e)}")


# Convenience endpoints for common operations
@router.post("/postgres/save-processor-result")
async def save_processor_result(
    request: Dict[str, Any],
    current_user: Dict = Depends(get_current_sandbox_user),
    db_service: DatabaseAPIService = Depends(get_database_api_service)
):
    """Save processor execution result to database."""
    
    try:
        processor_id = request.get("processor_id")
        step_index = request.get("step_index")
        input_data = request.get("input_data")
        output_data = request.get("output_data")
        
        query = """
            INSERT INTO processor_execution_results 
            (user_id, processor_id, step_index, input_data, output_data, execution_id, timestamp)
            VALUES (:user_id, :processor_id, :step_index, :input_data, :output_data, :execution_id, NOW())
        """
        
        params = {
            "user_id": current_user["user_id"],
            "processor_id": processor_id,
            "step_index": step_index,
            "input_data": input_data,
            "output_data": output_data,
            "execution_id": current_user["execution_id"]
        }
        
        result = await db_service.execute_postgres_query(
            user_id=current_user["user_id"],
            query=query,
            params=params
        )
        
        return {
            "success": True,
            "message": "Processor result saved successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save processor result: {str(e)}")


@router.post("/elasticsearch/save-vectors")
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


@router.post("/neo4j/save-relationships")
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


# Audit and Monitoring Endpoints
@router.get("/audit/logs")
async def get_audit_logs(
    limit: int = 100,
    current_user: Dict = Depends(get_current_sandbox_user),
    db_service: DatabaseAPIService = Depends(get_database_api_service)
):
    """Get audit logs for current user."""
    
    try:
        logs = await db_service.audit_logger.get_user_audit_logs(
            user_id=current_user["user_id"],
            limit=limit
        )
        
        return {
            "success": True,
            "logs": [log.dict() for log in logs],
            "count": len(logs)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get audit logs: {str(e)}")


@router.get("/health")
async def database_health():
    """Health check for database API."""
    
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "message": "Database API is operational"
    }


# Utility endpoints for debugging
@router.post("/debug/validate-query")
async def validate_query(
    request: Dict[str, Any],
    current_user: Dict = Depends(get_current_sandbox_user),
    permission_manager: PermissionManager = Depends(get_permission_manager)
):
    """Validate query without executing it."""
    
    try:
        database_type = request.get("database_type")
        operation = request.get("operation")
        query = request.get("query")
        
        can_execute, reason = await permission_manager.can_execute_operation(
            user_id=current_user["user_id"],
            database_type=database_type,
            operation=operation,
            query_or_command=query
        )
        
        return {
            "valid": can_execute,
            "reason": reason,
            "user_id": current_user["user_id"],
            "database_type": database_type,
            "operation": operation
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query validation failed: {str(e)}")


@router.get("/permissions")
async def get_user_permissions(
    current_user: Dict = Depends(get_current_sandbox_user),
    permission_manager: PermissionManager = Depends(get_permission_manager)
):
    """Get current user's database permissions."""
    
    try:
        permissions = await permission_manager.get_user_permissions(current_user["user_id"])
        
        return {
            "success": True,
            "user_id": current_user["user_id"],
            "permissions": permissions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get permissions: {str(e)}") 