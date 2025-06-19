# Brain_Net Architecture Documentation

## System Overview

Brain_Net is designed as a microservices-based architecture that provides intelligent document processing, retrieval accuracy monitoring, and real-time visualization capabilities.

## Architecture Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   AI/ML Layer   │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (LangChain)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │  Elasticsearch  │    │     MinIO       │
│   (Metadata)    │    │   (Search)      │    │   (Storage)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│     Neo4j       │    │   Monitoring    │
│  (Knowledge     │    │   (Prometheus   │
│     Graph)      │    │    + Grafana)   │
└─────────────────┘    └─────────────────┘
```

## Component Details

### 1. Frontend Layer (Next.js + React + TypeScript)

#### Core Features
- **Document Management Dashboard**: Upload, view, and manage documents
- **Real-time Processing Visualization**: Live status updates and progress tracking
- **Query Testing Interface**: Interactive query generation and testing
- **Analytics Dashboard**: Retrieval accuracy metrics and insights
- **Knowledge Graph Visualization**: Interactive graph view of document relationships

#### Key Components
```typescript
// Core page components
- pages/
  ├── dashboard/          # Main dashboard
  ├── documents/          # Document management
  ├── queries/           # Query testing interface
  ├── analytics/         # Analytics and metrics
  └── knowledge-graph/   # Graph visualization

// Shared components
- components/
  ├── DocumentUploader/  # File upload component
  ├── ProcessingStatus/  # Real-time status display
  ├── QueryTester/       # Interactive query testing
  ├── AnalyticsChart/    # Data visualization
  └── KnowledgeGraph/    # Graph visualization
```

### 2. Backend Layer (FastAPI + Python)

#### Core Services

**Document Processing Service**
```python
# Main processing pipeline
class DocumentProcessor:
    - parse_documents()      # Parse various file formats
    - chunk_documents()      # Intelligent chunking
    - extract_metadata()     # Metadata extraction
    - generate_embeddings()  # Vector embeddings
```

**Query Generation Service**
```python
# Intelligent query generation
class QueryGenerator:
    - generate_test_queries()    # Create test queries
    - validate_queries()         # Query validation
    - categorize_queries()       # Query categorization
```

**Retrieval Monitoring Service**
```python
# Accuracy monitoring
class RetrievalMonitor:
    - track_accuracy()           # Real-time accuracy tracking
    - detect_bad_cases()         # Bad case detection
    - generate_reports()         # Performance reports
```

**API Endpoints**
```python
# RESTful API structure
/api/v1/
├── documents/           # Document CRUD operations
├── processing/          # Processing status and control
├── queries/            # Query generation and testing
├── analytics/          # Analytics and metrics
└── knowledge-graph/    # Graph operations
```

### 3. AI/ML Layer (LangChain)

#### Core Components

**Document Understanding**
```python
# LangChain-based document processing
class DocumentUnderstanding:
    - extract_entities()         # Named entity recognition
    - identify_topics()          # Topic modeling
    - generate_summaries()       # Document summarization
    - create_relationships()     # Relationship extraction
```

**Query Intelligence**
```python
# Intelligent query handling
class QueryIntelligence:
    - generate_queries()         # LLM-powered query generation
    - enhance_queries()          # Query optimization
    - validate_retrieval()       # Retrieval validation
```

**Retrieval Enhancement**
```python
# Advanced retrieval capabilities
class RetrievalEnhancement:
    - semantic_search()          # Semantic similarity
    - hybrid_search()            # Hybrid search (keyword + semantic)
    - reranking()               # Result reranking
```

### 4. Database Layer

#### PostgreSQL (Primary Database)
```sql
-- Core tables
documents (
    id, title, content, file_path, 
    created_at, updated_at, status
)

chunks (
    id, document_id, content, 
    embedding, metadata, chunk_index
)

queries (
    id, content, category, 
    generated_at, accuracy_score
)

retrieval_results (
    id, query_id, chunk_id, 
    relevance_score, retrieved_at
)

users (
    id, username, email, 
    created_at, preferences
)
```

#### Elasticsearch (Search Engine)
```json
// Document index mapping
{
  "mappings": {
    "properties": {
      "content": {"type": "text", "analyzer": "standard"},
      "title": {"type": "text", "analyzer": "standard"},
      "metadata": {"type": "object"},
      "embedding": {"type": "dense_vector", "dims": 1536}
    }
  }
}
```

#### Neo4j (Knowledge Graph)
```cypher
// Graph schema
(:Document)-[:CONTAINS]->(:Chunk)
(:Chunk)-[:SIMILAR_TO]->(:Chunk)
(:Document)-[:RELATED_TO]->(:Document)
(:Entity)-[:MENTIONED_IN]->(:Chunk)
(:Topic)-[:DISCUSSED_IN]->(:Document)
```

#### MinIO (Object Storage)
```
// Storage structure
brain-net/
├── documents/           # Original uploaded files
├── processed/           # Processed document artifacts
├── embeddings/          # Vector embeddings
├── models/             # Trained models
└── exports/            # Data exports
```

## Data Flow

### 1. Document Processing Flow
```
1. User uploads document → Frontend
2. Frontend → Backend API
3. Backend → Document Processor
4. Document Processor → LangChain (understanding)
5. LangChain → Chunking Service
6. Chunking Service → Embedding Generation
7. Embeddings → Elasticsearch + PostgreSQL
8. Metadata → Neo4j (knowledge graph)
9. Original file → MinIO
10. Status updates → Frontend (real-time)
```

### 2. Query Processing Flow
```
1. User submits query → Frontend
2. Frontend → Backend API
3. Backend → Query Processor
4. Query Processor → Elasticsearch (search)
5. Elasticsearch → Results
6. Results → Reranking Service
7. Reranking → Accuracy Evaluation
8. Results + Accuracy → Frontend
9. Metrics → Analytics Database
```

### 3. Monitoring Flow
```
1. System events → Event Bus
2. Event Bus → Monitoring Service
3. Monitoring Service → Prometheus
4. Prometheus → Grafana (visualization)
5. Alerts → Notification Service
```

## Security Architecture

### Authentication & Authorization
- JWT-based authentication
- Role-based access control (RBAC)
- API key management for external integrations

### Data Security
- Encryption at rest (AES-256)
- Encryption in transit (TLS 1.3)
- Secure file upload validation
- Input sanitization and validation

### Network Security
- API rate limiting
- CORS configuration
- Request validation
- SQL injection prevention

## Scalability Considerations

### Horizontal Scaling
- Stateless backend services
- Load balancer support
- Database connection pooling
- Cache layer (Redis)

### Performance Optimization
- Async processing for heavy operations
- Background job queues (Celery)
- CDN for static assets
- Database indexing strategies

### Monitoring & Observability
- Application metrics (Prometheus)
- Distributed tracing (Jaeger)
- Log aggregation (ELK Stack)
- Health checks and alerts

## Deployment Architecture

### Development Environment
```yaml
# docker-compose.dev.yml
services:
  frontend:     # Next.js dev server
  backend:      # FastAPI with hot reload
  postgres:     # Local PostgreSQL
  elasticsearch: # Local Elasticsearch
  neo4j:        # Local Neo4j
  minio:        # Local MinIO
```

### Production Environment
```yaml
# docker-compose.prod.yml
services:
  nginx:        # Reverse proxy
  frontend:     # Built Next.js app
  backend:      # Production FastAPI
  postgres:     # Managed PostgreSQL
  elasticsearch: # Managed Elasticsearch
  neo4j:        # Managed Neo4j
  minio:        # Managed MinIO
  redis:        # Cache layer
  prometheus:   # Metrics
  grafana:      # Monitoring
```

## Configuration Management

### Environment Variables
```bash
# Backend Configuration
DATABASE_URL=postgresql://user:pass@host:port/db
ELASTICSEARCH_URL=http://localhost:9200
NEO4J_URI=bolt://localhost:7687
MINIO_ENDPOINT=localhost:9000
OPENAI_API_KEY=your-api-key

# Frontend Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Feature Flags
- Query generation enabled/disabled
- Real-time processing on/off
- Analytics collection preferences
- Experimental features toggle

This architecture provides a robust, scalable foundation for your intelligent knowledge base system with comprehensive monitoring, security, and performance optimization capabilities. 