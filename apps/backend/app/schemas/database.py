"""
Database API schemas for request and response validation.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class ExecutionContext(BaseModel):
    """Context information for database operations."""
    user_id: int
    execution_id: str
    pipeline_id: Optional[int] = None
    processor_id: Optional[int] = None
    step_index: Optional[int] = None
    debug_level: str = "info"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DatabaseOperationResponse(BaseModel):
    """Base response for database operations."""
    success: bool
    execution_time: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    operation_id: str


# PostgreSQL Schemas
class PostgresQueryRequest(BaseModel):
    """Request schema for PostgreSQL query execution."""
    query: str = Field(..., description="SQL query to execute")
    params: Dict[str, Any] = Field(default_factory=dict, description="Query parameters")
    execution_context: Optional[ExecutionContext] = None


class PostgresQueryResponse(DatabaseOperationResponse):
    """Response schema for PostgreSQL query execution."""
    data: List[Dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    columns: List[str] = Field(default_factory=list)


# Elasticsearch Schemas
class ElasticsearchRequest(BaseModel):
    """Request schema for Elasticsearch operations."""
    index: str = Field(..., description="Elasticsearch index name")
    query: Dict[str, Any] = Field(..., description="Elasticsearch query")
    size: int = Field(default=10, ge=1, le=1000, description="Number of results to return")
    from_: int = Field(default=0, ge=0, alias="from", description="Starting offset")
    execution_context: Optional[ExecutionContext] = None


class ElasticsearchResponse(DatabaseOperationResponse):
    """Response schema for Elasticsearch operations."""
    data: Dict[str, Any] = Field(default_factory=dict)
    total_hits: int = 0
    max_score: Optional[float] = None


# Neo4j Schemas
class Neo4jQueryRequest(BaseModel):
    """Request schema for Neo4j query execution."""
    query: str = Field(..., description="Cypher query to execute")
    params: Dict[str, Any] = Field(default_factory=dict, description="Query parameters")
    database: Optional[str] = None
    execution_context: Optional[ExecutionContext] = None


class Neo4jQueryResponse(DatabaseOperationResponse):
    """Response schema for Neo4j query execution."""
    data: List[Dict[str, Any]] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)


# Redis Schemas
class RedisCommandRequest(BaseModel):
    """Request schema for Redis command execution."""
    command: str = Field(..., description="Redis command to execute")
    args: List[Any] = Field(default_factory=list, description="Command arguments")
    execution_context: Optional[ExecutionContext] = None


class RedisCommandResponse(DatabaseOperationResponse):
    """Response schema for Redis command execution."""
    data: Any = None
    data_type: str = "unknown"


# MinIO Schemas
class MinIOOperationRequest(BaseModel):
    """Request schema for MinIO operations."""
    operation: str = Field(..., description="MinIO operation (get, put, delete, list)")
    bucket: str = Field(..., description="S3 bucket name")
    object_key: Optional[str] = None
    content: Optional[bytes] = None
    metadata: Dict[str, str] = Field(default_factory=dict)
    execution_context: Optional[ExecutionContext] = None


class MinIOOperationResponse(DatabaseOperationResponse):
    """Response schema for MinIO operations."""
    data: Any = None
    metadata: Dict[str, str] = Field(default_factory=dict)
    object_info: Dict[str, Any] = Field(default_factory=dict)


# Audit Log Schemas
class AuditLogEntry(BaseModel):
    """Audit log entry for database operations."""
    id: Optional[int] = None
    user_id: int
    execution_id: str
    database_type: str
    operation: str
    query_or_command: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    execution_time: float
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    execution_context: Dict[str, Any] = Field(default_factory=dict)


# Batch Operation Schemas
class BatchOperationRequest(BaseModel):
    """Request schema for batch database operations."""
    operations: List[Dict[str, Any]] = Field(..., description="List of operations to execute")
    execution_context: Optional[ExecutionContext] = None
    continue_on_error: bool = Field(default=False, description="Continue processing if one operation fails")


class BatchOperationResponse(DatabaseOperationResponse):
    """Response schema for batch database operations."""
    results: List[Dict[str, Any]] = Field(default_factory=list)
    successful_operations: int = 0
    failed_operations: int = 0
    errors: List[str] = Field(default_factory=list)


# Permission Check Schemas
class PermissionCheckRequest(BaseModel):
    """Request schema for permission validation."""
    user_id: int
    database_type: str
    operation: str
    resource: str
    context: Dict[str, Any] = Field(default_factory=dict)


class PermissionCheckResponse(BaseModel):
    """Response schema for permission validation."""
    allowed: bool
    reason: Optional[str] = None
    required_permissions: List[str] = Field(default_factory=list)
    user_permissions: List[str] = Field(default_factory=list) 