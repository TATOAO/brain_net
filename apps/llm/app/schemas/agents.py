"""
Agent-related Pydantic schemas for Brain_Net LLM Service
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class AgentType(str, Enum):
    """Available agent types."""
    RESEARCH = "research"
    WRITING = "writing"
    ANALYSIS = "analysis"
    CODING = "coding"
    CUSTOM = "custom"


class TaskStatus(str, Enum):
    """Task execution status."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentRequest(BaseModel):
    """Request for single agent execution."""
    agent_type: AgentType = Field(..., description="Type of agent to execute")
    task: str = Field(..., description="Task description")
    context: Optional[str] = Field(default=None, description="Additional context")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Agent parameters")


class AgentResponse(BaseModel):
    """Response from agent execution."""
    agent_type: AgentType = Field(..., description="Type of agent executed")
    task: str = Field(..., description="Original task")
    result: str = Field(..., description="Agent execution result")
    steps: List[str] = Field(..., description="Execution steps taken")
    execution_time: float = Field(..., description="Execution time in seconds")


class CrewRequest(BaseModel):
    """Request for CrewAI crew execution."""
    crew_name: str = Field(..., description="Name of the crew configuration")
    task: str = Field(..., description="Main task for the crew")
    agents: List[Dict[str, Any]] = Field(..., description="Agent configurations")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Shared context")


class CrewResponse(BaseModel):
    """Response from CrewAI execution."""
    crew_name: str = Field(..., description="Name of the executed crew")
    task: str = Field(..., description="Original task")
    result: str = Field(..., description="Crew execution result")
    agent_results: List[Dict[str, Any]] = Field(..., description="Individual agent results")
    execution_time: float = Field(..., description="Total execution time")


class WorkflowRequest(BaseModel):
    """Request for LangGraph workflow execution."""
    workflow_name: str = Field(..., description="Name of the workflow")
    input_data: Dict[str, Any] = Field(..., description="Input data for the workflow")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Workflow configuration")


class WorkflowResponse(BaseModel):
    """Response from LangGraph workflow execution."""
    workflow_name: str = Field(..., description="Name of the executed workflow")
    result: Dict[str, Any] = Field(..., description="Workflow execution result")
    steps: List[Dict[str, Any]] = Field(..., description="Workflow steps executed")
    execution_time: float = Field(..., description="Total execution time")


class AgentTaskRequest(BaseModel):
    """Request for background agent task."""
    task_type: str = Field(..., description="Type of task")
    task_data: Dict[str, Any] = Field(..., description="Task data")
    priority: Optional[int] = Field(default=1, description="Task priority")


class AgentTaskResponse(BaseModel):
    """Response for agent task status."""
    task_id: str = Field(..., description="Unique task identifier")
    status: TaskStatus = Field(..., description="Current task status")
    message: str = Field(..., description="Status message")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Task result if completed")
    created_at: Optional[str] = Field(default=None, description="Task creation timestamp")
    completed_at: Optional[str] = Field(default=None, description="Task completion timestamp") 