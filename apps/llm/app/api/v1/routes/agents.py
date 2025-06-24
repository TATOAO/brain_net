"""
Agents API routes for Brain_Net LLM Service
Supports CrewAI and LangGraph agents
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List

from app.schemas.agents import (
    AgentRequest, AgentResponse, AgentTaskRequest, AgentTaskResponse,
    CrewRequest, CrewResponse, WorkflowRequest, WorkflowResponse
)
from app.services.agents import AgentService
from app.core.dependencies import get_agent_service

router = APIRouter()


@router.post("/execute", response_model=AgentResponse)
async def execute_agent(
    request: AgentRequest,
    agent_service: AgentService = Depends(get_agent_service)
) -> AgentResponse:
    """Execute a single agent task."""
    try:
        response = await agent_service.execute_agent(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")


@router.post("/crew/execute", response_model=CrewResponse)
async def execute_crew(
    request: CrewRequest,
    agent_service: AgentService = Depends(get_agent_service)
) -> CrewResponse:
    """Execute a CrewAI crew with multiple agents."""
    try:
        response = await agent_service.execute_crew(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Crew execution failed: {str(e)}")


@router.post("/workflow/execute", response_model=WorkflowResponse)
async def execute_workflow(
    request: WorkflowRequest,
    agent_service: AgentService = Depends(get_agent_service)
) -> WorkflowResponse:
    """Execute a LangGraph workflow."""
    try:
        response = await agent_service.execute_workflow(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")


@router.post("/tasks", response_model=AgentTaskResponse)
async def create_agent_task(
    request: AgentTaskRequest,
    background_tasks: BackgroundTasks,
    agent_service: AgentService = Depends(get_agent_service)
) -> AgentTaskResponse:
    """Create and queue an agent task for background execution."""
    try:
        task_id = await agent_service.create_task(request)
        background_tasks.add_task(agent_service.execute_background_task, task_id)
        
        return AgentTaskResponse(
            task_id=task_id,
            status="queued",
            message="Task created and queued for execution"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task creation failed: {str(e)}")


@router.get("/tasks/{task_id}", response_model=AgentTaskResponse)
async def get_task_status(
    task_id: str,
    agent_service: AgentService = Depends(get_agent_service)
) -> AgentTaskResponse:
    """Get the status of an agent task."""
    try:
        task_status = await agent_service.get_task_status(task_id)
        return task_status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


@router.get("/tasks/{task_id}/result")
async def get_task_result(
    task_id: str,
    agent_service: AgentService = Depends(get_agent_service)
) -> dict:
    """Get the result of a completed agent task."""
    try:
        result = await agent_service.get_task_result(task_id)
        return {"task_id": task_id, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task result: {str(e)}")


@router.get("/available")
async def list_available_agents(
    agent_service: AgentService = Depends(get_agent_service)
) -> dict:
    """List all available agent types and their capabilities."""
    try:
        agents = await agent_service.list_available_agents()
        return {"available_agents": agents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")


@router.delete("/tasks/{task_id}")
async def cancel_task(
    task_id: str,
    agent_service: AgentService = Depends(get_agent_service)
) -> dict:
    """Cancel a queued or running agent task."""
    try:
        await agent_service.cancel_task(task_id)
        return {"message": f"Task {task_id} cancelled successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}") 