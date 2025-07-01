"""
Processor and Pipeline models for the Brain_Net application.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from sqlmodel import SQLModel, Field, Column, DateTime, JSON, Text, Relationship
from sqlalchemy.sql import func


class ProcessorStatus(str, Enum):
    """Status of a processor."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    TESTING = "testing"


class ProcessorType(str, Enum):
    """Type of processor."""
    BUILTIN = "builtin"
    USER_DEFINED = "user_defined"
    CUSTOM = "custom"


class PipelineStatus(str, Enum):
    """Status of a pipeline."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class UserProcessor(SQLModel, table=True):
    """Model for user-defined processors."""
    __tablename__ = "user_processors"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    name: str = Field(max_length=255, index=True)
    description: Optional[str] = Field(default=None, max_length=1000)
    processor_type: ProcessorType = Field(default=ProcessorType.USER_DEFINED)
    status: ProcessorStatus = Field(default=ProcessorStatus.ACTIVE)
    
    # Processor code and configuration
    processor_code: str = Field(sa_column=Column(Text))  # Python code for the processor
    config_schema: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))  # JSON schema for configuration
    default_config: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))  # Default configuration
    
    # Processing metadata
    input_types: List[str] = Field(default=[], sa_column=Column(JSON))  # Supported input types
    output_types: List[str] = Field(default=[], sa_column=Column(JSON))  # Supported output types
    processing_capabilities: List[str] = Field(default=[], sa_column=Column(JSON))  # What this processor can do
    
    # Usage tracking
    usage_count: int = Field(default=0)
    last_used: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    
    # Version control
    version: str = Field(default="1.0.0", max_length=50)
    is_template: bool = Field(default=False)  # Whether this is a template for others to use
    
    # Metadata
    created_at: Optional[datetime] = Field(
        default=None, 
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: Optional[datetime] = Field(
        default=None, 
        sa_column=Column(DateTime(timezone=True), onupdate=func.now())
    )
    
    # Relationships
    pipelines: List["UserPipeline"] = Relationship(back_populates="processors")


class UserPipeline(SQLModel, table=True):
    """Model for user-defined processing pipelines."""
    __tablename__ = "user_pipelines"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    name: str = Field(max_length=255, index=True)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: PipelineStatus = Field(default=PipelineStatus.ACTIVE)
    
    # Pipeline configuration
    processor_sequence: List[Dict[str, Any]] = Field(sa_column=Column(JSON))  # Ordered list of processor configs
    global_config: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))  # Global pipeline settings
    
    # Execution metadata
    parallel_execution: bool = Field(default=False)  # Whether to run processors in parallel where possible
    max_retry_attempts: int = Field(default=3)
    timeout_seconds: Optional[int] = Field(default=None)
    
    # Usage tracking
    execution_count: int = Field(default=0)
    last_executed: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    average_execution_time: Optional[float] = Field(default=None)  # in seconds
    
    # Version control
    version: str = Field(default="1.0.0", max_length=50)
    is_template: bool = Field(default=False)  # Whether this is a template for others to use
    
    # Metadata
    created_at: Optional[datetime] = Field(
        default=None, 
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: Optional[datetime] = Field(
        default=None, 
        sa_column=Column(DateTime(timezone=True), onupdate=func.now())
    )
    
    # Relationships
    processors: List[UserProcessor] = Relationship(back_populates="pipelines")
    executions: List["PipelineExecution"] = Relationship(back_populates="pipeline")


class PipelineExecution(SQLModel, table=True):
    """Model for tracking pipeline executions."""
    __tablename__ = "pipeline_executions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    pipeline_id: int = Field(foreign_key="user_pipelines.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    file_hash: str = Field(index=True, max_length=64)  # File being processed
    
    # Execution details
    execution_id: str = Field(max_length=100, unique=True, index=True)  # Unique execution identifier
    status: PipelineStatus = Field(default=PipelineStatus.RUNNING)
    
    # Timing
    started_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    completed_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    execution_time: Optional[float] = Field(default=None)  # Total execution time in seconds
    
    # Results and metadata
    result_data: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))  # Final processed data
    processor_outputs: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))  # Individual processor outputs
    error_details: Optional[str] = Field(default=None, sa_column=Column(Text))  # Error information if failed
    
    # Configuration used
    pipeline_config_snapshot: Dict[str, Any] = Field(sa_column=Column(JSON))  # Snapshot of pipeline config at execution time
    
    # Metadata storage hints for future integration
    storage_path: Optional[str] = Field(default=None, max_length=500)  # Path where processed data is stored
    storage_format: Optional[str] = Field(default=None, max_length=50)  # Format of stored data
    
    created_at: Optional[datetime] = Field(
        default=None, 
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    
    # Relationships
    pipeline: UserPipeline = Relationship(back_populates="executions")


# Read schemas for API responses
class UserProcessorRead(SQLModel):
    """Schema for reading processor information."""
    id: int
    name: str
    description: Optional[str]
    processor_type: ProcessorType
    status: ProcessorStatus
    input_types: List[str]
    output_types: List[str]
    processing_capabilities: List[str]
    usage_count: int
    version: str
    is_template: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class UserPipelineRead(SQLModel):
    """Schema for reading pipeline information."""
    id: int
    name: str
    description: Optional[str]
    status: PipelineStatus
    processor_sequence: List[Dict[str, Any]]
    execution_count: int
    version: str
    is_template: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class PipelineExecutionRead(SQLModel):
    """Schema for reading pipeline execution information."""
    id: int
    pipeline_id: int
    file_hash: str
    execution_id: str
    status: PipelineStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    execution_time: Optional[float]
    error_details: Optional[str]
    storage_path: Optional[str]
    storage_format: Optional[str]


# Create schemas for API requests
class UserProcessorCreate(SQLModel):
    """Schema for creating a new processor."""
    name: str
    description: Optional[str] = None
    processor_code: str
    config_schema: Optional[Dict[str, Any]] = None
    default_config: Optional[Dict[str, Any]] = None
    input_types: List[str] = []
    output_types: List[str] = []
    processing_capabilities: List[str] = []
    version: str = "1.0.0"
    is_template: bool = False


class UserPipelineCreate(SQLModel):
    """Schema for creating a new pipeline."""
    name: str
    description: Optional[str] = None
    processor_sequence: List[Dict[str, Any]]
    global_config: Optional[Dict[str, Any]] = None
    parallel_execution: bool = False
    max_retry_attempts: int = 3
    timeout_seconds: Optional[int] = None
    version: str = "1.0.0"
    is_template: bool = False


class ProcessorExecutionRequest(SQLModel):
    """Schema for requesting processor execution."""
    pipeline_id: int
    file_hash: str
    custom_config: Optional[Dict[str, Any]] = None


# List schemas
class UserProcessorList(SQLModel):
    """Schema for listing user processors."""
    processors: List[UserProcessorRead]
    total_count: int


class UserPipelineList(SQLModel):
    """Schema for listing user pipelines."""
    pipelines: List[UserPipelineRead]
    total_count: int


class PipelineExecutionList(SQLModel):
    """Schema for listing pipeline executions."""
    executions: List[PipelineExecutionRead]
    total_count: int 