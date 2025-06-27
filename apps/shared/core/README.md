# Document Processor Interface

This module provides an abstract interface for document processing plugins that enables users to:

1. **Select from available processors** in the frontend
2. **Chain processors together** in processing pipelines
3. **Implement custom processors** by extending the base classes

## Architecture Overview

The processor interface consists of several key components:

- **BaseDocumentProcessor**: Abstract base class for all processors
- **BaseChunker**: Specialized base class for text chunking processors
- **BaseNERProcessor**: Specialized base class for Named Entity Recognition processors
- **ProcessorRegistry**: Manages available processors
- **ProcessingPipeline**: Executes chains of processors
- **DocumentProcessorService**: High-level service for integration

## Basic Usage

### Using the Service

```python
from apps.shared.core.processor_service import document_processor_service

# Get available processors
processors = document_processor_service.get_available_processors()

# Process a document
processed_doc = await document_processor_service.process_user_document(
    user=user,
    user_file=user_file,
    document_content=content,
    processing_config={
        "pipeline": [
            {
                "processor_id": "metadata_extractor",
                "parameters": {"extract_stats": True}
            },
            {
                "processor_id": "fixed_size_chunker", 
                "parameters": {"chunk_size": 1000, "overlap": 200}
            }
        ]
    }
)
```

## Creating Custom Processors

### 1. Basic Custom Processor

```python
from apps.shared.core.processor import BaseDocumentProcessor, ProcessorConfig, ProcessingType

class MyCustomProcessor(BaseDocumentProcessor):
    def __init__(self, config: ProcessorConfig = None):
        if config is None:
            config = ProcessorConfig(
                processor_id="my_custom_processor",
                processing_type=ProcessingType.CUSTOM,
                name="My Custom Processor",
                description="Does custom processing"
            )
        super().__init__(config)
    
    async def process(self, document, context, **kwargs):
        # Your processing logic here
        result = ProcessingResult(
            processor_id=self.processor_id,
            processing_type=self.processing_type,
            status=ProcessingStatus.COMPLETED,
            input_document_id=document.document_id,
            output_data={"processed": True}
        )
        return result
    
    def get_supported_formats(self):
        return [DocumentFormat.TEXT, DocumentFormat.PDF]
    
    def get_required_parameters(self):
        return {}
    
    def get_optional_parameters(self):
        return {"param1": {"type": "str", "default": "value"}}
```

### 2. Custom Chunker

```python
from apps.shared.core.processor import BaseChunker

class MyCustomChunker(BaseChunker):
    async def chunk_text(self, text, chunk_size=1000, overlap=200, **kwargs):
        # Your chunking logic here
        chunks = []
        # ... implement chunking
        return chunks
```

### 3. Custom NER Processor

```python
from apps.shared.core.processor import BaseNERProcessor

class MyCustomNER(BaseNERProcessor):
    async def extract_entities(self, text, entity_types=None, **kwargs):
        # Your NER logic here
        entities = []
        # ... implement entity extraction
        return entities
```

## Available Processing Types

- `CHUNKING`: Split documents into smaller pieces
- `NER`: Named Entity Recognition
- `METADATA_EXTRACTION`: Extract document metadata
- `TEXT_EXTRACTION`: Extract raw text from documents
- `SUMMARIZATION`: Generate document summaries
- `KEYWORD_EXTRACTION`: Extract key phrases
- `SENTIMENT_ANALYSIS`: Analyze document sentiment
- `LANGUAGE_DETECTION`: Detect document language
- `STRUCTURE_ANALYSIS`: Analyze document structure
- `EMBEDDING_GENERATION`: Generate text embeddings
- `CLASSIFICATION`: Classify documents
- `CUSTOM`: Custom processing logic

## Supported Document Formats

- `TEXT`: Plain text files
- `PDF`: PDF documents
- `DOCX`: Microsoft Word documents
- `HTML`: HTML files
- `MARKDOWN`: Markdown files
- `JSON`: JSON documents
- `CSV`: CSV files
- `XLSX`: Excel spreadsheets

## Frontend Integration

The processor interface is designed to be easily integrated with frontend applications:

### 1. Get Available Processors

```javascript
// GET /api/processors
{
  "chunking": [
    {
      "processor_id": "fixed_size_chunker",
      "name": "Fixed Size Chunker",
      "description": "Splits text into fixed-size chunks",
      "required_parameters": {...},
      "optional_parameters": {...}
    }
  ],
  "ner": [...],
  ...
}
```

### 2. Submit Processing Request

```javascript
// POST /api/process-document
{
  "file_hash": "abc123...",
  "pipeline": [
    {
      "processor_id": "fixed_size_chunker",
      "parameters": {
        "chunk_size": 1000,
        "overlap": 200
      }
    }
  ]
}
```

## Pipeline Configuration

Pipelines allow chaining multiple processors together:

```python
pipeline_config = [
    {
        "processor_id": "metadata_extractor",
        "parameters": {"extract_stats": True},
        "stop_on_error": True
    },
    {
        "processor_id": "fixed_size_chunker",
        "parameters": {"chunk_size": 800, "overlap": 150}
    },
    {
        "processor_id": "simple_ner",
        "parameters": {"entity_types": ["PERSON", "EMAIL"]}
    }
]
```

## Error Handling

The processor interface includes comprehensive error handling:

- **Input validation**: Validate document format and required parameters
- **Processing errors**: Capture and report processing failures
- **Pipeline errors**: Handle errors in multi-step pipelines
- **Status tracking**: Track processing status throughout the pipeline

## Extension Points

The interface provides several extension points for customization:

1. **Custom Processing Types**: Add new processing categories
2. **Custom Document Formats**: Support additional file types
3. **Custom Parameter Types**: Add new parameter validation types
4. **Custom Validation**: Implement custom input validation
5. **Custom Preprocessing/Postprocessing**: Add pre/post processing hooks

## Best Practices

1. **Always validate inputs** before processing
2. **Use meaningful processor IDs** and descriptions
3. **Document required and optional parameters** clearly
4. **Handle errors gracefully** and provide useful error messages
5. **Use appropriate confidence scores** for probabilistic outputs
6. **Keep processors focused** on single responsibilities
7. **Test processors thoroughly** with various input formats 