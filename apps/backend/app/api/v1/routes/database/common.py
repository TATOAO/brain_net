"""Common database utilities and endpoints."""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from app.core.database import DatabaseManager
from app.services.database_api import DatabaseAPIService
from app.services.permissions import PermissionManager
from app.services.sandbox_auth import get_current_sandbox_user
from app.schemas.database import AuditLogEntry

router = APIRouter(prefix="/common", tags=["database-common"])


# Shared dependency functions
async def get_database_manager() -> DatabaseManager:
    """Get database manager from app state."""
    # This would typically be injected from app state
    # For now, create a new instance
    from app.core.database import DatabaseManager
    return DatabaseManager()


async def get_permission_manager(
    db_manager: DatabaseManager = Depends(get_database_manager)
) -> PermissionManager:
    """Get permission manager instance."""
    return PermissionManager(db_manager)


async def get_database_api_service(
    db_manager: DatabaseManager = Depends(get_database_manager),
    permission_manager: PermissionManager = Depends(get_permission_manager)
) -> DatabaseAPIService:
    """Get database API service instance."""
    return DatabaseAPIService(db_manager, permission_manager)


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