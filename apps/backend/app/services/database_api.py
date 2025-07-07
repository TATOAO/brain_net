"""
Database API service for secure database operations via HTTP endpoints.
"""

import time
import uuid
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import LoggerMixin
from app.core.database import DatabaseManager
from app.services.permissions import PermissionManager
from app.schemas.database import (
    ExecutionContext, PostgresQueryRequest, PostgresQueryResponse,
    ElasticsearchRequest, ElasticsearchResponse, Neo4jQueryRequest, Neo4jQueryResponse,
    RedisCommandRequest, RedisCommandResponse, MinIOOperationRequest, MinIOOperationResponse,
    AuditLogEntry
)


class DatabaseAPIService(LoggerMixin):
    """Service for handling database operations with authorization and auditing."""
    
    def __init__(self, db_manager: DatabaseManager, permission_manager: PermissionManager):
        self.db_manager = db_manager
        self.permission_manager = permission_manager
        self.audit_logger = AuditLogger(db_manager)
    
    async def execute_postgres_query(self, user_id: int, query: str, params: Dict[str, Any],
                                   execution_context: Optional[ExecutionContext] = None) -> PostgresQueryResponse:
        """Execute PostgreSQL query with full authorization and auditing."""
        
        operation_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Create execution context if not provided
        if execution_context is None:
            execution_context = ExecutionContext(
                user_id=user_id,
                execution_id=operation_id
            )
        
        try:
            # 1. Check permissions
            can_execute, reason = await self.permission_manager.can_execute_operation(
                user_id=user_id,
                database_type="postgres",
                operation=self._extract_postgres_operation(query),
                query_or_command=query,
                context={"params": params}
            )
            
            if not can_execute:
                raise PermissionError(f"Permission denied: {reason}")
            
            # 2. Add user context to query parameters
            contextualized_params = self._add_user_context_to_params(params, user_id)
            
            # 3. Sanitize and validate query
            sanitized_query = await self._sanitize_postgres_query(query, user_id)
            
            # 4. Execute query
            async with self.db_manager.get_postgres_session() as session:
                result = await session.execute(text(sanitized_query), contextualized_params)
                
                # Handle different result types
                if result.returns_rows:
                    rows = result.fetchall()
                    columns = list(result.keys()) if rows else []
                    data = [dict(zip(columns, row)) for row in rows]
                else:
                    data = []
                    columns = []
                    rows = []
                
                execution_time = time.time() - start_time
                
                # 5. Audit logging
                await self.audit_logger.log_database_operation(
                    user_id=user_id,
                    execution_id=execution_context.execution_id,
                    database_type="postgres",
                    operation=self._extract_postgres_operation(query),
                    query_or_command=sanitized_query,
                    parameters=contextualized_params,
                    execution_time=execution_time,
                    success=True,
                    execution_context=execution_context.dict()
                )
                
                return PostgresQueryResponse(
                    success=True,
                    execution_time=execution_time,
                    operation_id=operation_id,
                    data=data,
                    row_count=len(rows),
                    columns=columns
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_message = str(e)
            
            # Error logging
            await self.audit_logger.log_database_operation(
                user_id=user_id,
                execution_id=execution_context.execution_id,
                database_type="postgres",
                operation=self._extract_postgres_operation(query),
                query_or_command=query,
                parameters=params,
                execution_time=execution_time,
                success=False,
                error_message=error_message,
                execution_context=execution_context.dict()
            )
            
            raise Exception(f"PostgreSQL query execution failed: {error_message}")
    
    async def elasticsearch_search(self, user_id: int, index: str, query: Dict[str, Any],
                                 size: int = 10, from_: int = 0,
                                 execution_context: Optional[ExecutionContext] = None) -> ElasticsearchResponse:
        """Execute Elasticsearch search with user context."""
        
        operation_id = str(uuid.uuid4())
        start_time = time.time()
        
        if execution_context is None:
            execution_context = ExecutionContext(
                user_id=user_id,
                execution_id=operation_id
            )
        
        try:
            # 1. Check permissions
            can_execute, reason = await self.permission_manager.can_execute_operation(
                user_id=user_id,
                database_type="elasticsearch",
                operation="search",
                query_or_command=json.dumps(query),
                context={"index": index}
            )
            
            if not can_execute:
                raise PermissionError(f"Permission denied: {reason}")
            
            # 2. Add user filter to query
            user_filtered_query = self._add_user_filter_to_es_query(query, user_id)
            
            # 3. Ensure index name includes user scope
            scoped_index = self._get_user_scoped_index(index, user_id)
            
            # 4. Execute search
            result = await self.db_manager.elasticsearch.search(
                index=scoped_index,
                body={
                    "query": user_filtered_query,
                    "size": size,
                    "from": from_
                }
            )
            
            execution_time = time.time() - start_time
            
            # 5. Audit logging
            await self.audit_logger.log_database_operation(
                user_id=user_id,
                execution_id=execution_context.execution_id,
                database_type="elasticsearch",
                operation="search",
                query_or_command=json.dumps(user_filtered_query),
                parameters={"index": scoped_index, "size": size, "from": from_},
                execution_time=execution_time,
                success=True,
                execution_context=execution_context.dict()
            )
            
            return ElasticsearchResponse(
                success=True,
                execution_time=execution_time,
                operation_id=operation_id,
                data=result,
                total_hits=result.get("hits", {}).get("total", {}).get("value", 0),
                max_score=result.get("hits", {}).get("max_score")
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_message = str(e)
            
            await self.audit_logger.log_database_operation(
                user_id=user_id,
                execution_id=execution_context.execution_id,
                database_type="elasticsearch",
                operation="search",
                query_or_command=json.dumps(query),
                parameters={"index": index, "size": size, "from": from_},
                execution_time=execution_time,
                success=False,
                error_message=error_message,
                execution_context=execution_context.dict()
            )
            
            raise Exception(f"Elasticsearch search failed: {error_message}")
    
    async def execute_neo4j_query(self, user_id: int, query: str, params: Dict[str, Any],
                                database: Optional[str] = None,
                                execution_context: Optional[ExecutionContext] = None) -> Neo4jQueryResponse:
        """Execute Neo4j query with user context."""
        
        operation_id = str(uuid.uuid4())
        start_time = time.time()
        
        if execution_context is None:
            execution_context = ExecutionContext(
                user_id=user_id,
                execution_id=operation_id
            )
        
        try:
            # 1. Check permissions
            can_execute, reason = await self.permission_manager.can_execute_operation(
                user_id=user_id,
                database_type="neo4j",
                operation=self._extract_neo4j_operation(query),
                query_or_command=query,
                context={"params": params}
            )
            
            if not can_execute:
                raise PermissionError(f"Permission denied: {reason}")
            
            # 2. Add user context to query parameters
            contextualized_params = self._add_user_context_to_params(params, user_id)
            
            # 3. Execute query
            async with self.db_manager.get_neo4j_session() as session:
                result = await session.run(query, contextualized_params)
                records = [record.data() for record in await result.data()]
                summary = await result.consume()
                
                execution_time = time.time() - start_time
                
                # 4. Audit logging
                await self.audit_logger.log_database_operation(
                    user_id=user_id,
                    execution_id=execution_context.execution_id,
                    database_type="neo4j",
                    operation=self._extract_neo4j_operation(query),
                    query_or_command=query,
                    parameters=contextualized_params,
                    execution_time=execution_time,
                    success=True,
                    execution_context=execution_context.dict()
                )
                
                return Neo4jQueryResponse(
                    success=True,
                    execution_time=execution_time,
                    operation_id=operation_id,
                    data=records,
                    summary={
                        "query_type": summary.query_type,
                        "counters": summary.counters.__dict__ if summary.counters else {},
                        "result_available_after": summary.result_available_after,
                        "result_consumed_after": summary.result_consumed_after
                    }
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_message = str(e)
            
            await self.audit_logger.log_database_operation(
                user_id=user_id,
                execution_id=execution_context.execution_id,
                database_type="neo4j",
                operation=self._extract_neo4j_operation(query),
                query_or_command=query,
                parameters=params,
                execution_time=execution_time,
                success=False,
                error_message=error_message,
                execution_context=execution_context.dict()
            )
            
            raise Exception(f"Neo4j query execution failed: {error_message}")
    
    async def execute_redis_command(self, user_id: int, command: str, args: List[Any],
                                  execution_context: Optional[ExecutionContext] = None) -> RedisCommandResponse:
        """Execute Redis command with user context."""
        
        operation_id = str(uuid.uuid4())
        start_time = time.time()
        
        if execution_context is None:
            execution_context = ExecutionContext(
                user_id=user_id,
                execution_id=operation_id
            )
        
        try:
            # 1. Check permissions
            can_execute, reason = await self.permission_manager.can_execute_operation(
                user_id=user_id,
                database_type="redis",
                operation=command.upper(),
                query_or_command=command,
                context={"args": args}
            )
            
            if not can_execute:
                raise PermissionError(f"Permission denied: {reason}")
            
            # 2. Add user context to Redis keys
            contextualized_args = self._add_user_context_to_redis_args(args, user_id)
            
            # 3. Execute command
            redis_client = self.db_manager.redis
            result = await redis_client.execute_command(command, *contextualized_args)
            
            execution_time = time.time() - start_time
            
            # 4. Audit logging
            await self.audit_logger.log_database_operation(
                user_id=user_id,
                execution_id=execution_context.execution_id,
                database_type="redis",
                operation=command.upper(),
                query_or_command=f"{command} {' '.join(map(str, contextualized_args))}",
                parameters={"command": command, "args": contextualized_args},
                execution_time=execution_time,
                success=True,
                execution_context=execution_context.dict()
            )
            
            return RedisCommandResponse(
                success=True,
                execution_time=execution_time,
                operation_id=operation_id,
                data=result,
                data_type=type(result).__name__
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_message = str(e)
            
            await self.audit_logger.log_database_operation(
                user_id=user_id,
                execution_id=execution_context.execution_id,
                database_type="redis",
                operation=command.upper(),
                query_or_command=f"{command} {' '.join(map(str, args))}",
                parameters={"command": command, "args": args},
                execution_time=execution_time,
                success=False,
                error_message=error_message,
                execution_context=execution_context.dict()
            )
            
            raise Exception(f"Redis command execution failed: {error_message}")
    
    # Helper methods
    def _extract_postgres_operation(self, query: str) -> str:
        """Extract operation type from PostgreSQL query."""
        query_upper = query.strip().upper()
        if query_upper.startswith('SELECT'):
            return 'SELECT'
        elif query_upper.startswith('INSERT'):
            return 'INSERT'
        elif query_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif query_upper.startswith('DELETE'):
            return 'DELETE'
        else:
            return 'UNKNOWN'
    
    def _extract_neo4j_operation(self, query: str) -> str:
        """Extract operation type from Neo4j query."""
        query_upper = query.strip().upper()
        if 'MATCH' in query_upper:
            return 'MATCH'
        elif 'CREATE' in query_upper:
            return 'CREATE'
        elif 'MERGE' in query_upper:
            return 'MERGE'
        elif 'DELETE' in query_upper:
            return 'DELETE'
        else:
            return 'UNKNOWN'
    
    def _add_user_context_to_params(self, params: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Add user context to query parameters."""
        contextualized_params = params.copy()
        contextualized_params['user_id'] = user_id
        return contextualized_params
    
    async def _sanitize_postgres_query(self, query: str, user_id: int) -> str:
        """Sanitize PostgreSQL query and add user context where needed."""
        # This is a simplified implementation
        # In production, you'd want more sophisticated query rewriting
        return query
    
    def _add_user_filter_to_es_query(self, query: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Add user filter to Elasticsearch query."""
        user_filter = {"term": {"user_id": user_id}}
        
        if "bool" in query:
            if "filter" in query["bool"]:
                query["bool"]["filter"].append(user_filter)
            else:
                query["bool"]["filter"] = [user_filter]
        else:
            query = {
                "bool": {
                    "must": [query],
                    "filter": [user_filter]
                }
            }
        
        return query
    
    def _get_user_scoped_index(self, index: str, user_id: int) -> str:
        """Get user-scoped index name."""
        if index.startswith('public_'):
            return index
        elif index.startswith(f'user_{user_id}_'):
            return index
        else:
            return f'user_{user_id}_{index}'
    
    def _add_user_context_to_redis_args(self, args: List[Any], user_id: int) -> List[Any]:
        """Add user context to Redis arguments."""
        if not args:
            return args
        
        # For Redis, we typically need to prefix keys with user context
        contextualized_args = []
        for i, arg in enumerate(args):
            if i == 0 and isinstance(arg, str):  # First argument is usually the key
                if not arg.startswith(f'user:{user_id}:') and not arg.startswith('public:'):
                    contextualized_args.append(f'user:{user_id}:{arg}')
                else:
                    contextualized_args.append(arg)
            else:
                contextualized_args.append(arg)
        
        return contextualized_args


class AuditLogger(LoggerMixin):
    """Handles audit logging for database operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def log_database_operation(self, user_id: int, execution_id: str, database_type: str,
                                   operation: str, query_or_command: str, parameters: Dict[str, Any],
                                   execution_time: float, success: bool, error_message: str = None,
                                   execution_context: Dict[str, Any] = None):
        """Log database operation to audit trail."""
        
        audit_entry = AuditLogEntry(
            user_id=user_id,
            execution_id=execution_id,
            database_type=database_type,
            operation=operation,
            query_or_command=query_or_command,
            parameters=parameters,
            execution_time=execution_time,
            success=success,
            error_message=error_message,
            execution_context=execution_context or {}
        )
        
        try:
            # Store in database
            async with self.db_manager.get_postgres_session() as session:
                await session.execute(
                    text("""
                        INSERT INTO database_audit_logs 
                        (user_id, execution_id, database_type, operation, query_or_command, 
                         parameters, execution_time, success, error_message, execution_context, timestamp)
                        VALUES (:user_id, :execution_id, :database_type, :operation, :query_or_command,
                                :parameters, :execution_time, :success, :error_message, :execution_context, :timestamp)
                    """),
                    {
                        "user_id": audit_entry.user_id,
                        "execution_id": audit_entry.execution_id,
                        "database_type": audit_entry.database_type,
                        "operation": audit_entry.operation,
                        "query_or_command": audit_entry.query_or_command,
                        "parameters": json.dumps(audit_entry.parameters),
                        "execution_time": audit_entry.execution_time,
                        "success": audit_entry.success,
                        "error_message": audit_entry.error_message,
                        "execution_context": json.dumps(audit_entry.execution_context),
                        "timestamp": audit_entry.timestamp
                    }
                )
            
            # Also log to application logger
            log_message = f"DB Operation: {database_type}.{operation} by user {user_id} - {'SUCCESS' if success else 'FAILED'}"
            if success:
                self.logger.info(log_message, extra={
                    "user_id": user_id,
                    "execution_id": execution_id,
                    "database_type": database_type,
                    "operation": operation,
                    "execution_time": execution_time
                })
            else:
                self.logger.error(log_message, extra={
                    "user_id": user_id,
                    "execution_id": execution_id,
                    "database_type": database_type,
                    "operation": operation,
                    "error_message": error_message,
                    "execution_time": execution_time
                })
                
        except Exception as e:
            self.logger.error(f"Failed to log database operation: {e}")
    
    async def get_user_audit_logs(self, user_id: int, limit: int = 100) -> List[AuditLogEntry]:
        """Get audit logs for a specific user."""
        
        try:
            async with self.db_manager.get_postgres_session() as session:
                result = await session.execute(
                    text("""
                        SELECT * FROM database_audit_logs 
                        WHERE user_id = :user_id 
                        ORDER BY timestamp DESC 
                        LIMIT :limit
                    """),
                    {"user_id": user_id, "limit": limit}
                )
                
                logs = []
                for row in result.fetchall():
                    logs.append(AuditLogEntry(
                        id=row.id,
                        user_id=row.user_id,
                        execution_id=row.execution_id,
                        database_type=row.database_type,
                        operation=row.operation,
                        query_or_command=row.query_or_command,
                        parameters=json.loads(row.parameters) if row.parameters else {},
                        execution_time=row.execution_time,
                        success=row.success,
                        error_message=row.error_message,
                        timestamp=row.timestamp,
                        execution_context=json.loads(row.execution_context) if row.execution_context else {}
                    ))
                
                return logs
                
        except Exception as e:
            self.logger.error(f"Failed to get audit logs: {e}")
            return [] 