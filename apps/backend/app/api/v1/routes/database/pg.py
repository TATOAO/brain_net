"""PostgreSQL database routes."""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from app.core.database import DatabaseManager
from app.services.database_api import DatabaseAPIService
from app.services.permissions import PermissionManager
from app.services.sandbox_auth import get_current_sandbox_user
from app.schemas.database import (
    PostgresQueryRequest, PostgresQueryResponse,
    ExecutionContext
)

router = APIRouter(prefix="/postgres", tags=["postgresql"])


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


@router.post("/query", response_model=PostgresQueryResponse)
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


@router.post("/batch", response_model=List[PostgresQueryResponse])
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


@router.post("/save-processor-result")
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