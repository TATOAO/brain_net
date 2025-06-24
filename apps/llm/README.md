# Brain_Net LLM Service

The LLM service provides AI/ML capabilities for the Brain_Net platform, including:

- **Chat Completions**: Generate conversational responses using various LLM providers
- **RAG (Retrieval Augmented Generation)**: Query knowledge bases with context-aware responses
- **Document Processing**: Extract, chunk, and embed documents for search and retrieval
- **Agent Framework**: Execute complex tasks using CrewAI and LangGraph agents
- **Model Management**: Load, unload, and manage various AI models

## Features

### 🤖 Chat & Completions

- Support for OpenAI GPT models, Anthropic Claude, and local models
- Streaming responses for real-time chat experiences
- Session management and chat history
- Conversation summarization

### 📚 RAG System

- Document upload and processing (PDF, DOCX, TXT, etc.)
- Vector similarity search using Elasticsearch
- Context-aware response generation
- Collection management and reindexing

### 🔄 Agent Workflows

- **CrewAI Integration**: Multi-agent collaboration for complex tasks
- **LangGraph Workflows**: Custom agent workflows and state management
- Background task execution with status tracking
- Agent capability discovery

### 📄 Document Intelligence

- Text extraction from multiple file formats
- Intelligent document chunking and embedding
- Metadata extraction and analysis
- Batch processing capabilities

### 🎯 Model Management

- Dynamic model loading and unloading
- Model health monitoring and statistics
- Cache management for optimal performance
- Support for multiple embedding models

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│   FastAPI App   │◄──►│    Services     │◄──►│   Data Layer    │
│                 │    │                 │    │                 │
│  • Chat API     │    │  • ChatService  │    │  • PostgreSQL   │
│  • RAG API      │    │  • RAGService   │    │  • Elasticsearch│
│  • Agents API   │    │  • AgentService │    │  • Neo4j        │
│  • Docs API     │    │  • DocService   │    │  • Redis        │
│  • Models API   │    │  • ModelService │    │  • MinIO        │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Quick Start

### Development Setup

1. **Clone and navigate to the LLM service:**

   ```bash
   cd apps/llm
   ```
2. **Create virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```
4. **Set environment variables:**

   ```bash
   cp ../../env.example .env
   # Edit .env with your configuration
   ```
5. **Run the service:**

   ```bash
   python main.py
   ```

### Docker Deployment

1. **Build the image:**

   ```bash
   docker build -f apps/llm/Dockerfile -t brain-net-llm .
   ```
2. **Run with docker-compose:**

   ```bash
   cd docker
   docker-compose up llm-service
   ```

## API Endpoints

### Chat Completions

- `POST /api/v1/chat/completions` - Generate chat completion
- `POST /api/v1/chat/completions/stream` - Streaming completion
- `GET /api/v1/chat/history/{session_id}` - Get chat history

### RAG Operations

- `POST /api/v1/rag/query` - Perform RAG query
- `POST /api/v1/rag/upload` - Upload document
- `POST /api/v1/rag/search` - Search documents

### Agent Execution

- `POST /api/v1/agents/execute` - Execute single agent
- `POST /api/v1/agents/crew/execute` - Execute CrewAI crew
- `POST /api/v1/agents/workflow/execute` - Execute LangGraph workflow

### Document Processing

- `POST /api/v1/documents/process` - Process document
- `POST /api/v1/documents/embeddings` - Generate embeddings
- `GET /api/v1/documents/supported-formats` - List supported formats

### Model Management

- `GET /api/v1/models/available` - List available models
- `POST /api/v1/models/load` - Load model
- `DELETE /api/v1/models/unload/{model_name}` - Unload model

## Configuration

Key environment variables:

```bash
# LLM Providers
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
DEFAULT_LLM_MODEL=gpt-3.5-turbo
DEFAULT_EMBEDDING_MODEL=text-embedding-ada-002

# Vector Store
VECTOR_STORE_TYPE=elasticsearch
VECTOR_DIMENSION=1536
SIMILARITY_THRESHOLD=0.7

# RAG Settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_CONTEXT_LENGTH=4000

# Agent Settings
CREWAI_ENABLED=true
LANGRAPH_ENABLED=true
MAX_AGENT_ITERATIONS=10
AGENT_TIMEOUT=300

# Performance
MAX_CONCURRENT_REQUESTS=10
MODEL_CACHE_SIZE=3
EMBEDDING_BATCH_SIZE=100
```

## Health Checks

- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed service health including models and vector store

## Development

### Adding New Features

1. **New API Endpoint:**

   - Add route in `app/api/v1/routes/`
   - Create corresponding schema in `app/schemas/`
   - Implement service logic in `app/services/`
2. **New Agent Type:**

   - Extend `AgentService` class
   - Add agent configuration
   - Update available agents list
3. **New Document Type:**

   - Add processor in `DocumentService`
   - Update supported formats
   - Add tests for new format

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_chat.py
```

## Monitoring

The service includes built-in monitoring:

- Prometheus metrics endpoint
- Structured logging with request tracing
- Model performance tracking
- Resource usage monitoring

## Troubleshooting

### Common Issues

1. **Model Loading Errors:**

   - Check API keys are set correctly
   - Verify model name is supported
   - Monitor memory usage
2. **Vector Store Connection:**

   - Ensure Elasticsearch is running
   - Check network connectivity
   - Verify index configuration
3. **Document Processing:**

   - Check file format is supported
   - Verify file size limits
   - Review chunking parameters

### Logs

Service logs are available in:

- Console output (development)
- `logs/llm_service.log` (file-based)
- Docker logs (containerized deployment)

## Contributing

Please refer to the main project README for contribution guidelines.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
