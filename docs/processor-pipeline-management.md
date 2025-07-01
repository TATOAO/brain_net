# Processor Pipeline Management System

## Overview

The Brain_Net application now includes a comprehensive processor pipeline management system that allows users to:

- Create custom processors using the `AsyncProcessor` framework
- Build processing pipelines by combining processors in sequence
- Execute pipelines on uploaded files
- Track execution history and results
- Save processed data using `after_process` callbacks

## Database Models

### UserProcessor
Stores user-defined and built-in processors with their code, configuration, and metadata.

**Key Fields:**
- `processor_code`: Python code implementing AsyncProcessor
- `config_schema`: JSON schema for processor configuration
- `processing_capabilities`: List of what the processor can do
- `input_types` / `output_types`: Supported data types
- `usage_count`: Track how often the processor is used

### UserPipeline
Defines processing pipelines as sequences of processors.

**Key Fields:**
- `processor_sequence`: Ordered list of processor IDs and configurations
- `global_config`: Pipeline-wide settings
- `execution_count`: Track pipeline usage
- `parallel_execution`: Whether to run processors in parallel

### PipelineExecution
Tracks individual pipeline executions with timing, status, and results.

**Key Fields:**
- `execution_id`: Unique identifier for the execution
- `status`: running, completed, failed
- `result_data`: Final processed output
- `processor_outputs`: Intermediate results from each step
- `storage_path`: Where processed data is stored

## API Endpoints

### Processors
```
GET    /api/processors                    # List user processors
POST   /api/processors                    # Create new processor
GET    /api/processors/{id}               # Get specific processor
PUT    /api/processors/{id}               # Update processor
DELETE /api/processors/{id}               # Delete processor
GET    /api/processors/templates          # Get processor templates
```

### Pipelines
```
GET    /api/processors/pipelines          # List user pipelines
POST   /api/processors/pipelines          # Create new pipeline
GET    /api/processors/pipelines/{id}     # Get specific pipeline
PUT    /api/processors/pipelines/{id}     # Update pipeline
DELETE /api/processors/pipelines/{id}     # Delete pipeline
POST   /api/processors/pipelines/{id}/execute  # Execute pipeline
```

### Executions
```
GET    /api/processors/executions         # List executions
GET    /api/processors/executions/{id}    # Get execution details
```

## Creating Custom Processors

### Basic Structure

All processors must inherit from `AsyncProcessor` and implement the `process` method:

```python
from processor_pipeline import AsyncProcessor
from typing import AsyncGenerator, Any, List

class CustomProcessor(AsyncProcessor):
    """Your custom processor description."""
    
    meta = {
        "name": "custom_processor",
        "input_type": "str",
        "output_type": "List[str]"
    }
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.param1 = config.get('param1', 'default_value')
    
    async def process(self, data: AsyncGenerator[Any, None]) -> AsyncGenerator[List[str], None]:
        async for input_data in data:
            # Process the input data
            result = self.do_processing(input_data)
            yield result
    
    def do_processing(self, data):
        # Your processing logic here
        return processed_data
```

### After Process Callbacks

The `after_process` callback is automatically called after each processing step to save intermediate results:

```python
async def after_process(self, input_data: Any, output_data: Any, 
                       execution_id: str, step_index: int, *args, **kwargs) -> None:
    """
    This callback is automatically invoked with comprehensive metadata.
    Use it to save processed data to appropriate storage systems.
    """
    
    # The system automatically provides:
    # - execution_id: Unique identifier for this pipeline run
    # - step_index: Position of this processor in the pipeline
    # - input_data: Data that was fed into this processor
    # - output_data: Data produced by this processor
    
    # Example storage routing based on processor type:
    if 'chunker' in self.meta.get('name', ''):
        # Save chunks to document store
        await save_to_document_store(output_data, execution_id, step_index)
    
    elif 'vector' in self.meta.get('name', ''):
        # Save vectors to vector database
        await save_to_vector_db(output_data, execution_id, step_index)
    
    elif 'entity' in self.meta.get('name', ''):
        # Save entities to graph database
        await save_to_graph_db(output_data, execution_id, step_index)
```

### Storage Integration Hints

The system provides hints for future storage integration:

1. **MinIO for file data**: Save large processed files, documents, images
2. **Vector databases for embeddings**: Save vector representations for similarity search
3. **Graph databases for relationships**: Save extracted entities and their relationships
4. **Analytics databases for metrics**: Save processing statistics and performance data

## Frontend Component

The `ProcessorPipelineManager` component provides a comprehensive UI for:

### Processor Management
- Create custom processors with code editor
- View existing processors with status badges
- Edit processor code and configuration
- Template library for common processors

### Pipeline Builder
- Drag-and-drop pipeline creation
- Visual pipeline flow representation
- Configuration management for each step
- Pipeline validation and testing

### Execution Monitoring
- Real-time execution status
- Execution history and logs
- Performance metrics and analytics
- Error tracking and debugging

## Usage Examples

### 1. Create a Text Chunker Processor

```python
# Frontend: Create processor via UI or API
processor_data = {
    "name": "Smart Text Chunker",
    "description": "Intelligent text chunking with semantic awareness",
    "processor_code": text_chunker_code,  # See migration file for example
    "input_types": ["str", "text"],
    "output_types": ["List[str]", "chunks"],
    "processing_capabilities": ["text_chunking", "semantic_splitting"]
}

# API call to create processor
response = await axios.post('/api/processors', processor_data)
```

### 2. Build a Processing Pipeline

```python
# Create pipeline with multiple steps
pipeline_data = {
    "name": "Document Analysis Pipeline",
    "description": "Extract, chunk, vectorize, and analyze documents",
    "processor_sequence": [
        {"processor_id": 1, "config": {"chunk_size": 1000}, "order": 1},
        {"processor_id": 2, "config": {"vector_size": 384}, "order": 2},
        {"processor_id": 3, "config": {"analysis_depth": "deep"}, "order": 3}
    ],
    "global_config": {
        "timeout_seconds": 600,
        "max_retry_attempts": 3
    }
}

# API call to create pipeline
response = await axios.post('/api/processors/pipelines', pipeline_data)
```

### 3. Execute Pipeline on File

```python
# Execute pipeline on uploaded file
execution_request = {
    "file_hash": "abc123def456",
    "custom_config": {
        "1": {"chunk_size": 1500},  # Override for processor 1
        "2": {"vector_size": 512}   # Override for processor 2
    }
}

# API call to execute pipeline
response = await axios.post('/api/processors/pipelines/1/execute', execution_request)
execution_id = response.data.execution_id

# Monitor execution status
status_response = await axios.get(`/api/processors/executions/${execution_id}`)
```

## Migration and Setup

### 1. Run Database Migration

```bash
cd apps/backend
source .venv/bin/activate
python migration_add_processor_tables.py
```

This will:
- Create the processor, pipeline, and execution tables
- Add sample processors and pipelines
- Set up the database schema

### 2. Add Routes to Backend Router

```python
# In apps/backend/app/api/v1/router.py
from .routes.processors import router as processors_router

app.include_router(processors_router, prefix="/api/v1")
```

### 3. Add Frontend Component

```tsx
// In your Next.js page or component
import ProcessorPipelineManager from '@/components/ProcessorPipelineManager'

export default function ProcessorsPage() {
  return (
    <div>
      <ProcessorPipelineManager />
    </div>
  )
}
```

## Best Practices

### Security
- Processor code is validated for dangerous imports
- Code execution is sandboxed
- User isolation at database level
- Input validation on all API endpoints

### Performance
- Async processing with proper error handling
- Pipeline execution tracking and monitoring
- Configurable timeouts and retry mechanisms
- Resource usage tracking

### Extensibility
- Modular processor design
- Plugin architecture support
- Template system for common processors
- Configuration schema validation

## Future Enhancements

1. **Visual Pipeline Editor**: Drag-and-drop pipeline builder
2. **Processor Marketplace**: Share and discover processors
3. **Advanced Monitoring**: Real-time metrics and dashboards
4. **Parallel Execution**: Run compatible processors in parallel
5. **Version Control**: Track processor and pipeline versions
6. **Testing Framework**: Automated testing for processors
7. **Performance Optimization**: Caching and optimization hints

## Troubleshooting

### Common Issues

        raise ValueError(f"Code validation failed: {str(e)}")
   - Verify no dangerous imports are used
   - Ensure process method is implemented

2. **Pipeline Execution Fails**
   - Check processor compatibility (output → input types)
   - Verify all processors are active
   - Check configuration parameters

3. **Storage Integration Issues**
   - Implement actual storage clients in after_process callbacks
   - Configure proper credentials for external services
   - Handle storage failures gracefully

### Debug Mode

Enable debug logging to see detailed execution information:

```python
# In processor code
async def after_process(self, input_data, output_data, execution_id, step_index, *args, **kwargs):
    print(f"[DEBUG] Step {step_index}: {self.meta.get('name')} processed {type(output_data).__name__}")
    print(f"[DEBUG] Execution ID: {execution_id}")
    print(f"[DEBUG] Output size: {len(str(output_data))}")
```

## Integration Points

The processor pipeline system integrates with:

- **File Upload System**: Process uploaded documents
- **Authentication**: User-scoped processors and pipelines
- **Storage Systems**: MinIO, vector databases, graph databases
- **Monitoring**: OpenTelemetry tracing and metrics
- **Frontend**: React components for management UI

This system provides a foundation for extensible document processing while maintaining security, performance, and usability. 