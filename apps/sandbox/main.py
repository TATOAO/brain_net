"""
Brain_Net Sandbox FastAPI Application
Long-lived container for executing pipeline code and providing debugging information.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import asyncio
import logging
import traceback
import sys
import io
import uuid
import os
from datetime import datetime
from contextlib import redirect_stdout, redirect_stderr
import json
import httpx

# Configuration from environment variables
SANDBOX_HOST = os.getenv("SANDBOX_HOST", "0.0.0.0")
SANDBOX_PORT = int(os.getenv("SANDBOX_PORT", "8002"))
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
EXECUTION_TIMEOUT = int(os.getenv("EXECUTION_TIMEOUT", "60"))
MAX_CONCURRENT_EXECUTIONS = int(os.getenv("MAX_CONCURRENT_EXECUTIONS", "10"))
DEBUG_MODE = os.getenv("DEBUG_MODE", "true").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Configure logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL.upper()))
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Brain_Net Sandbox API",
    description="Code execution sandbox for pipeline processing and debugging",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for execution results (use Redis in production)
execution_results: Dict[str, Dict[str, Any]] = {}
active_executions: Dict[str, bool] = {}


class CodeExecutionRequest(BaseModel):
    """Request model for code execution."""
    code: str
    processor_id: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    timeout: Optional[int] = EXECUTION_TIMEOUT
    debug_mode: bool = DEBUG_MODE


class ExecutionResult(BaseModel):
    """Response model for execution results."""
    execution_id: str
    status: str  # "pending", "running", "completed", "failed", "timeout"
    output: Optional[str] = None
    error: Optional[str] = None
    debug_info: Optional[Dict[str, Any]] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    execution_time: Optional[float] = None


class ProcessorAdjustmentRequest(BaseModel):
    """Request model for processor adjustments."""
    processor_id: str
    adjustments: Dict[str, Any]
    reason: str


@app.get("/")
async def root():
    """Root endpoint with basic information."""
    return {
        "message": "Brain_Net Sandbox API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "active_executions": len(active_executions),
        "stored_results": len(execution_results),
        "configuration": {
            "host": SANDBOX_HOST,
            "port": SANDBOX_PORT,
            "backend_url": BACKEND_URL,
            "execution_timeout": EXECUTION_TIMEOUT,
            "max_concurrent_executions": MAX_CONCURRENT_EXECUTIONS,
            "debug_mode": DEBUG_MODE,
            "log_level": LOG_LEVEL
        }
    }


@app.get("/config")
async def get_configuration():
    """Get current sandbox configuration."""
    return {
        "sandbox_configuration": {
            "host": SANDBOX_HOST,
            "port": SANDBOX_PORT,
            "backend_url": BACKEND_URL,
            "execution_timeout": EXECUTION_TIMEOUT,
            "max_concurrent_executions": MAX_CONCURRENT_EXECUTIONS,
            "debug_mode": DEBUG_MODE,
            "log_level": LOG_LEVEL
        },
        "runtime_info": {
            "active_executions": len(active_executions),
            "stored_results": len(execution_results),
            "timestamp": datetime.utcnow().isoformat()
        }
    }


@app.post("/execute", response_model=ExecutionResult)
async def execute_code(
    request: CodeExecutionRequest,
    background_tasks: BackgroundTasks
):
    """Execute code in the sandbox and return execution ID."""
    execution_id = str(uuid.uuid4())
    
    # Initialize execution result
    result = ExecutionResult(
        execution_id=execution_id,
        status="pending",
        start_time=datetime.utcnow()
    )
    
    execution_results[execution_id] = result.dict()
    active_executions[execution_id] = True
    
    # Start execution in background
    background_tasks.add_task(
        _execute_code_async,
        execution_id,
        request.code,
        request.input_data,
        request.timeout,
        request.debug_mode,
        request.processor_id
    )
    
    return result


@app.get("/execution/{execution_id}", response_model=ExecutionResult)
async def get_execution_result(execution_id: str):
    """Get execution result by ID."""
    if execution_id not in execution_results:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    result = execution_results[execution_id]
    return ExecutionResult(**result)


@app.get("/executions", response_model=List[ExecutionResult])
async def list_executions(limit: int = 10, offset: int = 0):
    """List recent executions."""
    results = list(execution_results.values())
    results.sort(key=lambda x: x['start_time'], reverse=True)
    return [ExecutionResult(**r) for r in results[offset:offset+limit]]


@app.delete("/execution/{execution_id}")
async def cancel_execution(execution_id: str):
    """Cancel a running execution."""
    if execution_id not in execution_results:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    if execution_id in active_executions:
        active_executions[execution_id] = False
        execution_results[execution_id]["status"] = "cancelled"
        execution_results[execution_id]["end_time"] = datetime.utcnow().isoformat()
    
    return {"message": "Execution cancelled"}


@app.post("/adjust-processor")
async def adjust_processor(request: ProcessorAdjustmentRequest):
    """Send processor adjustment recommendations to the backend."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BACKEND_URL}/api/v1/processors/{request.processor_id}/adjust",
                json={
                    "adjustments": request.adjustments,
                    "reason": request.reason,
                    "source": "sandbox"
                }
            )
            
            if response.status_code == 200:
                return {"message": "Processor adjustment sent successfully"}
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to send adjustment: {response.text}"
                )
    except Exception as e:
        logger.error(f"Failed to send processor adjustment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send adjustment")


@app.get("/debug/{execution_id}")
async def get_debug_info(execution_id: str):
    """Get detailed debug information for an execution."""
    if execution_id not in execution_results:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    result = execution_results[execution_id]
    return {
        "execution_id": execution_id,
        "debug_info": result.get("debug_info", {}),
        "detailed_trace": result.get("detailed_trace", [])
    }


async def _execute_code_async(
    execution_id: str,
    code: str,
    input_data: Optional[Dict[str, Any]],
    timeout: int,
    debug_mode: bool,
    processor_id: Optional[str]
):
    """Execute code asynchronously with debugging information."""
    try:
        execution_results[execution_id]["status"] = "running"
        
        # Capture stdout and stderr
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        
        # Prepare execution environment
        exec_globals = {
            "__builtins__": __builtins__,
            "input_data": input_data or {},
            "print": print,  # Allow print statements
        }
        
        debug_info = {
            "variables_before": {},
            "variables_after": {},
            "execution_steps": [],
            "imports": [],
            "functions_defined": [],
            "exceptions": []
        }
        
        start_time = datetime.utcnow()
        
        try:
            # Execute code with timeout
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                # Parse and execute code
                compiled_code = compile(code, "<sandbox>", "exec")
                
                # Execute with timeout
                await asyncio.wait_for(
                    asyncio.create_task(_run_code_sync(compiled_code, exec_globals)),
                    timeout=timeout
                )
                
        except asyncio.TimeoutError:
            execution_results[execution_id]["status"] = "timeout"
            execution_results[execution_id]["error"] = f"Execution timed out after {timeout} seconds"
        except Exception as e:
            execution_results[execution_id]["status"] = "failed"
            execution_results[execution_id]["error"] = str(e)
            execution_results[execution_id]["traceback"] = traceback.format_exc()
            debug_info["exceptions"].append({
                "type": type(e).__name__,
                "message": str(e),
                "traceback": traceback.format_exc()
            })
        else:
            execution_results[execution_id]["status"] = "completed"
        
        # Capture output
        stdout_content = stdout_buffer.getvalue()
        stderr_content = stderr_buffer.getvalue()
        
        execution_results[execution_id]["output"] = stdout_content
        if stderr_content:
            execution_results[execution_id]["stderr"] = stderr_content
        
        # Store debug information
        if debug_mode:
            debug_info["variables_after"] = {
                k: str(v) for k, v in exec_globals.items() 
                if not k.startswith("__") and k != "input_data"
            }
            execution_results[execution_id]["debug_info"] = debug_info
        
        end_time = datetime.utcnow()
        execution_results[execution_id]["end_time"] = end_time.isoformat()
        execution_results[execution_id]["execution_time"] = (end_time - start_time).total_seconds()
        
    except Exception as e:
        logger.error(f"Execution error for {execution_id}: {str(e)}")
        execution_results[execution_id]["status"] = "failed"
        execution_results[execution_id]["error"] = f"Internal error: {str(e)}"
        execution_results[execution_id]["end_time"] = datetime.utcnow().isoformat()
    
    finally:
        # Clean up active execution
        if execution_id in active_executions:
            del active_executions[execution_id]


async def _run_code_sync(compiled_code, exec_globals):
    """Run compiled code synchronously in event loop."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, exec, compiled_code, exec_globals)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=SANDBOX_HOST, port=SANDBOX_PORT) 