"""
Sandbox API Routes for Brain_Net Backend
Provides endpoints for AI agents to interact with Python sandboxes.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import json
import asyncio
from io import StringIO

from app.services.sandbox_service import SandboxService, get_sandbox_service
from app.services.auth import get_current_user
from app.core.sandbox import SandboxConfig, ExecutionResult, SandboxStatus
from apps.shared.models import User


router = APIRouter(prefix="/sandbox", tags=["sandbox"])


# Request/Response Models
class SandboxCreateRequest(BaseModel):
    """Request model for creating a new sandbox."""
    max_execution_time: int = Field(default=30, ge=1, le=300)
    max_memory_mb: int = Field(default=256, ge=64, le=1024)
    enable_debugging: bool = Field(default=True)
    save_intermediate_results: bool = Field(default=True)
    allowed_modules: List[str] = Field(default_factory=lambda: [
        'json', 'datetime', 'math', 'random', 'collections', 'itertools',
        'functools', 'operator', 're', 'string', 'uuid', 'hashlib',
        'base64', 'urllib.parse', 'typing', 'dataclasses', 'enum',
        'asyncio', 'pandas', 'numpy', 'requests', 'aiohttp'
    ])


class CodeExecutionRequest(BaseModel):
    """Request model for code execution."""
    code: str = Field(..., description="Python code to execute")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context variables")


class DatabaseQueryRequest(BaseModel):
    """Request model for database queries."""
    query: str = Field(..., description="SQL query to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Query parameters")


class ProcessorTemplateRequest(BaseModel):
    """Request model for processor template creation."""
    processor_type: str = Field(default="data_processor", description="Type of processor template")


class SandboxResponse(BaseModel):
    """Response model for sandbox operations."""
    sandbox_id: str
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None


class ExecutionResponse(BaseModel):
    """Response model for code execution."""
    execution_id: str
    status: str
    result: Any = None
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None
    execution_time: float = 0.0
    debug_info: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime


# Sandbox Management Endpoints
@router.post("/create", response_model=SandboxResponse)
async def create_sandbox(
    request: SandboxCreateRequest,
    current_user: User = Depends(get_current_user),
    service: SandboxService = Depends(get_sandbox_service)
):
    """Create a new sandbox for AI agent interaction."""
    try:
        config = request.dict()
        sandbox_id = await service.create_agent_sandbox(current_user.id, config)
        
        return SandboxResponse(
            sandbox_id=sandbox_id,
            status="created",
            message="Sandbox created successfully",
            data={"config": config}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create sandbox: {str(e)}")


@router.get("/{sandbox_id}/status", response_model=SandboxResponse)
async def get_sandbox_status(
    sandbox_id: str,
    current_user: User = Depends(get_current_user),
    service: SandboxService = Depends(get_sandbox_service)
):
    """Get current status and state of a sandbox."""
    try:
        state = await service.get_sandbox_state(sandbox_id)
        
        return SandboxResponse(
            sandbox_id=sandbox_id,
            status="active",
            message="Sandbox state retrieved successfully",
            data=state
        )
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Sandbox not found: {str(e)}")


@router.delete("/{sandbox_id}")
async def cleanup_sandbox(
    sandbox_id: str,
    current_user: User = Depends(get_current_user),
    service: SandboxService = Depends(get_sandbox_service)
):
    """Clean up and remove a sandbox."""
    try:
        await service.cleanup_sandbox(sandbox_id)
        
        return {"message": f"Sandbox {sandbox_id} cleaned up successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup sandbox: {str(e)}")


# Code Execution Endpoints
@router.post("/{sandbox_id}/execute", response_model=ExecutionResponse)
async def execute_code(
    sandbox_id: str,
    request: CodeExecutionRequest,
    current_user: User = Depends(get_current_user),
    service: SandboxService = Depends(get_sandbox_service)
):
    """Execute Python code in a sandbox."""
    try:
        result = await service.execute_code(sandbox_id, request.code, request.context)
        
        return ExecutionResponse(
            execution_id=result.execution_id,
            status=result.status,
            result=result.result,
            stdout=result.stdout,
            stderr=result.stderr,
            error=result.error,
            execution_time=result.execution_time,
            debug_info=result.debug_info,
            timestamp=result.created_at
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute code: {str(e)}")


@router.post("/{sandbox_id}/debug")
async def debug_code(
    sandbox_id: str,
    request: CodeExecutionRequest,
    current_user: User = Depends(get_current_user),
    service: SandboxService = Depends(get_sandbox_service)
):
    """Debug code execution step by step."""
    try:
        async def debug_stream():
            async for debug_info in service.debug_code(sandbox_id, request.code):
                yield f"data: {json.dumps(debug_info)}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            debug_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/plain"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to debug code: {str(e)}")


# Database Access Endpoints
@router.post("/{sandbox_id}/database/query")
async def query_database(
    sandbox_id: str,
    request: DatabaseQueryRequest,
    current_user: User = Depends(get_current_user),
    service: SandboxService = Depends(get_sandbox_service)
):
    """Execute a database query through the sandbox."""
    try:
        result = await service.query_database(sandbox_id, request.query, request.parameters)
        
        return {
            "query": request.query,
            "parameters": request.parameters,
            "results": result,
            "count": len(result),
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute database query: {str(e)}")


@router.get("/{sandbox_id}/database/schema")
async def get_database_schema(
    sandbox_id: str,
    current_user: User = Depends(get_current_user),
    service: SandboxService = Depends(get_sandbox_service)
):
    """Get database schema information."""
    try:
        schema = await service.get_database_schema(sandbox_id)
        
        return {
            "sandbox_id": sandbox_id,
            "schema": schema,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get database schema: {str(e)}")


# Processor Template Endpoints
@router.post("/{sandbox_id}/templates/processor")
async def create_processor_template(
    sandbox_id: str,
    request: ProcessorTemplateRequest,
    current_user: User = Depends(get_current_user),
    service: SandboxService = Depends(get_sandbox_service)
):
    """Create a processor template for the user to modify."""
    try:
        template_code = await service.create_processor_template(sandbox_id, request.processor_type)
        
        return {
            "sandbox_id": sandbox_id,
            "processor_type": request.processor_type,
            "template_code": template_code,
            "instructions": "Modify this template to create your custom processor",
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create processor template: {str(e)}")


# Agent Helper Endpoints
@router.get("/{sandbox_id}/help/functions")
async def get_available_functions(
    sandbox_id: str,
    current_user: User = Depends(get_current_user),
    service: SandboxService = Depends(get_sandbox_service)
):
    """Get list of available functions in the sandbox."""
    try:
        help_info = {
            "database_functions": {
                "db_query(query, parameters)": "Execute SQL query with parameters",
                "db_tables()": "Get list of available tables",
                "db_schema(table_name)": "Get schema for a specific table"
            },
            "debug_functions": {
                "debug(message, level)": "Log debug message with level",
                "inspect_var(name, value)": "Inspect a variable and track its history",
                "get_debug_info()": "Get debug summary information"
            },
            "built_in_functions": {
                "print(*args)": "Print output (captured in stdout)",
                "len(obj)": "Get length of object",
                "type(obj)": "Get type of object",
                "str(obj)": "Convert to string",
                "repr(obj)": "Get string representation",
                "list(iterable)": "Create list from iterable",
                "dict(**kwargs)": "Create dictionary",
                "range(start, stop, step)": "Create range object",
                "enumerate(iterable)": "Enumerate with indices",
                "zip(*iterables)": "Zip multiple iterables"
            },
            "allowed_modules": [
                "json", "datetime", "math", "random", "collections", "itertools",
                "functools", "operator", "re", "string", "uuid", "hashlib",
                "base64", "urllib.parse", "typing", "dataclasses", "enum",
                "asyncio", "pandas", "numpy", "requests", "aiohttp"
            ],
            "examples": {
                "basic_query": "results = await db_query('SELECT * FROM users LIMIT 10')",
                "parameterized_query": "results = await db_query('SELECT * FROM users WHERE id = :id', {'id': 1})",
                "debug_logging": "debug('Processing data...', 'INFO')",
                "variable_inspection": "inspect_var('my_var', my_variable)"
            }
        }
        
        return help_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get function help: {str(e)}")


@router.get("/{sandbox_id}/help/examples")
async def get_code_examples(
    sandbox_id: str,
    current_user: User = Depends(get_current_user),
    service: SandboxService = Depends(get_sandbox_service)
):
    """Get code examples for common tasks."""
    try:
        examples = {
            "basic_data_processing": {
                "title": "Basic Data Processing",
                "description": "Process data from database and analyze",
                "code": """
# Get data from database
users = await db_query('SELECT * FROM users LIMIT 100')
debug(f'Retrieved {len(users)} users', 'INFO')

# Process the data
processed_data = []
for user in users:
    user_data = {
        'id': user['id'],
        'name': user.get('name', 'Unknown'),
        'email': user.get('email', ''),
        'created_at': user.get('created_at')
    }
    processed_data.append(user_data)
    
debug(f'Processed {len(processed_data)} users', 'INFO')
inspect_var('processed_data', processed_data[:5])  # Inspect first 5

# Set result
__result__ = {
    'total_users': len(users),
    'processed_count': len(processed_data),
    'sample_data': processed_data[:3]
}
"""
            },
            "text_analysis": {
                "title": "Text Analysis",
                "description": "Analyze text content from database",
                "code": """
import re
from collections import Counter

# Get text data
articles = await db_query('SELECT title, content FROM articles LIMIT 50')
debug(f'Retrieved {len(articles)} articles', 'INFO')

# Analyze text
word_counts = Counter()
total_words = 0

for article in articles:
    # Combine title and content
    text = f"{article.get('title', '')} {article.get('content', '')}"
    
    # Extract words
    words = re.findall(r'\\b\\w+\\b', text.lower())
    word_counts.update(words)
    total_words += len(words)

# Get most common words
most_common = word_counts.most_common(20)
debug(f'Most common words: {most_common[:5]}', 'INFO')

# Set result
__result__ = {
    'total_articles': len(articles),
    'total_words': total_words,
    'unique_words': len(word_counts),
    'most_common_words': most_common,
    'avg_words_per_article': total_words / len(articles) if articles else 0
}
"""
            },
            "knowledge_extraction": {
                "title": "Knowledge Extraction",
                "description": "Extract knowledge from documents",
                "code": """
import json
from datetime import datetime

# Get document data
documents = await db_query('SELECT * FROM documents WHERE processed = false LIMIT 10')
debug(f'Retrieved {len(documents)} unprocessed documents', 'INFO')

# Extract knowledge
extracted_knowledge = []

for doc in documents:
    knowledge = {
        'document_id': doc['id'],
        'title': doc.get('title', ''),
        'key_concepts': [],
        'entities': [],
        'summary': '',
        'processed_at': datetime.utcnow().isoformat()
    }
    
    content = doc.get('content', '')
    
    # Extract key concepts (simple approach)
    words = content.lower().split()
    # Filter for potential concepts (words > 3 chars)
    concepts = [word for word in words if len(word) > 3]
    knowledge['key_concepts'] = list(set(concepts))[:10]  # Top 10 unique
    
    # Extract entities (emails, numbers, etc.)
    emails = re.findall(r'\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b', content)
    numbers = re.findall(r'\\b\\d+\\b', content)
    
    knowledge['entities'] = {
        'emails': emails,
        'numbers': numbers[:10]  # First 10 numbers
    }
    
    # Simple summary (first 200 chars)
    knowledge['summary'] = content[:200] + '...' if len(content) > 200 else content
    
    extracted_knowledge.append(knowledge)
    
    # Update processed status
    await db_query(
        'UPDATE documents SET processed = true WHERE id = :id',
        {'id': doc['id']}
    )

debug(f'Extracted knowledge from {len(extracted_knowledge)} documents', 'INFO')
inspect_var('sample_knowledge', extracted_knowledge[0] if extracted_knowledge else None)

# Set result
__result__ = {
    'processed_documents': len(extracted_knowledge),
    'extracted_knowledge': extracted_knowledge,
    'timestamp': datetime.utcnow().isoformat()
}
"""
            },
            "pipeline_debugging": {
                "title": "Pipeline Debugging",
                "description": "Debug a processing pipeline",
                "code": """
# Debug a multi-step pipeline
debug('Starting pipeline debugging', 'INFO')

# Step 1: Data Collection
debug('Step 1: Collecting data', 'INFO')
raw_data = await db_query('SELECT * FROM raw_data LIMIT 5')
inspect_var('raw_data', raw_data)

# Step 2: Data Validation
debug('Step 2: Validating data', 'INFO')
valid_data = []
for item in raw_data:
    if item.get('id') and item.get('content'):
        valid_data.append(item)
        debug(f'Valid item: {item["id"]}', 'DEBUG')
    else:
        debug(f'Invalid item: {item}', 'WARNING')

inspect_var('valid_data', valid_data)

# Step 3: Data Transformation
debug('Step 3: Transforming data', 'INFO')
transformed_data = []
for item in valid_data:
    transformed_item = {
        'id': item['id'],
        'content_length': len(item['content']),
        'word_count': len(item['content'].split()),
        'transformed_at': datetime.utcnow().isoformat()
    }
    transformed_data.append(transformed_item)
    debug(f'Transformed item {item["id"]}', 'DEBUG')

inspect_var('transformed_data', transformed_data)

# Step 4: Results
debug('Step 4: Finalizing results', 'INFO')
debug('Pipeline completed successfully', 'INFO')

# Set result
__result__ = {
    'pipeline_steps': 4,
    'raw_count': len(raw_data),
    'valid_count': len(valid_data),
    'transformed_count': len(transformed_data),
    'debug_summary': get_debug_info()
}
"""
            }
        }
        
        return {
            "examples": examples,
            "usage_notes": [
                "Use 'debug()' function to log information at different levels",
                "Use 'inspect_var()' to track variable changes",
                "Use 'await db_query()' for database operations",
                "Set '__result__' variable to return data from execution",
                "Check debug_info in execution results for debugging information"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get code examples: {str(e)}")


# Statistics and Management
@router.get("/{sandbox_id}/history")
async def get_execution_history(
    sandbox_id: str,
    current_user: User = Depends(get_current_user),
    service: SandboxService = Depends(get_sandbox_service)
):
    """Get execution history for a sandbox."""
    try:
        history = await service.get_execution_history(sandbox_id)
        
        return {
            "sandbox_id": sandbox_id,
            "history": [
                {
                    "execution_id": result.execution_id,
                    "status": result.status,
                    "execution_time": result.execution_time,
                    "created_at": result.created_at,
                    "error": result.error,
                    "has_result": result.result is not None
                }
                for result in history
            ],
            "total_executions": len(history)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get execution history: {str(e)}")


@router.get("/statistics")
async def get_sandbox_statistics(
    current_user: User = Depends(get_current_user),
    service: SandboxService = Depends(get_sandbox_service)
):
    """Get overall sandbox usage statistics."""
    try:
        stats = await service.get_sandbox_statistics()
        
        return {
            "statistics": stats,
            "user_id": current_user.id,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.post("/cleanup-all")
async def cleanup_all_sandboxes(
    current_user: User = Depends(get_current_user),
    service: SandboxService = Depends(get_sandbox_service)
):
    """Clean up all sandboxes for the current user."""
    try:
        await service.cleanup_all_sandboxes()
        
        return {"message": "All sandboxes cleaned up successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup all sandboxes: {str(e)}")


# Agent-specific endpoints for easy integration
@router.post("/agent/quick-execute")
async def agent_quick_execute(
    request: CodeExecutionRequest,
    current_user: User = Depends(get_current_user),
    service: SandboxService = Depends(get_sandbox_service)
):
    """Quick execution for agents - creates sandbox, executes code, and cleans up."""
    try:
        # Create temporary sandbox
        sandbox_id = await service.create_agent_sandbox(current_user.id)
        
        try:
            # Execute code
            result = await service.execute_code(sandbox_id, request.code, request.context)
            
            return ExecutionResponse(
                execution_id=result.execution_id,
                status=result.status,
                result=result.result,
                stdout=result.stdout,
                stderr=result.stderr,
                error=result.error,
                execution_time=result.execution_time,
                debug_info=result.debug_info,
                timestamp=result.created_at
            )
            
        finally:
            # Clean up sandbox
            await service.cleanup_sandbox(sandbox_id)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute code: {str(e)}")


@router.post("/agent/analyze-data")
async def agent_analyze_data(
    table_name: str,
    analysis_type: str = "summary",
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    service: SandboxService = Depends(get_sandbox_service)
):
    """Agent endpoint for quick data analysis."""
    try:
        # Create temporary sandbox
        sandbox_id = await service.create_agent_sandbox(current_user.id)
        
        try:
            # Generate analysis code based on type
            if analysis_type == "summary":
                code = f"""
# Get data summary
data = await db_query('SELECT * FROM {table_name} LIMIT {limit}')
debug(f'Retrieved {{len(data)}} rows from {table_name}', 'INFO')

# Analyze data
if data:
    # Get column info
    columns = list(data[0].keys()) if data else []
    
    # Basic statistics
    row_count = len(data)
    
    # Sample data
    sample = data[:5]
    
    __result__ = {{
        'table_name': '{table_name}',
        'total_rows': row_count,
        'columns': columns,
        'sample_data': sample,
        'analysis_type': '{analysis_type}'
    }}
else:
    __result__ = {{'error': 'No data found'}}
"""
            elif analysis_type == "schema":
                code = f"""
# Get table schema
schema = await db_schema('{table_name}')
debug(f'Retrieved schema for {table_name}', 'INFO')

__result__ = {{
    'table_name': '{table_name}',
    'schema': schema,
    'column_count': len(schema),
    'analysis_type': '{analysis_type}'
}}
"""
            else:
                code = f"""
# Custom analysis
tables = await db_tables()
debug(f'Available tables: {{tables}}', 'INFO')

__result__ = {{
    'available_tables': tables,
    'requested_table': '{table_name}',
    'analysis_type': '{analysis_type}'
}}
"""
            
            # Execute analysis
            result = await service.execute_code(sandbox_id, code)
            
            return ExecutionResponse(
                execution_id=result.execution_id,
                status=result.status,
                result=result.result,
                stdout=result.stdout,
                stderr=result.stderr,
                error=result.error,
                execution_time=result.execution_time,
                debug_info=result.debug_info,
                timestamp=result.created_at
            )
            
        finally:
            # Clean up sandbox
            await service.cleanup_sandbox(sandbox_id)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze data: {str(e)}") 