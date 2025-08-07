# Brain_Net Backend

An intelligent and highly visualized RAG system for local knowledge base management with secure code execution via Docker sandbox.

## 🏗️ Architecture Overview

### Core Architecture Design

```mermaid
graph TB
    subgraph "Main Application"
        A[FastAPI Backend] --> B[Processor Service]
        A --> C[Database API Layer]
        C --> D[Authorization & Permissions]
        D --> E[Database Manager]
        E --> F[PostgreSQL]
        E --> G[Elasticsearch]
        E --> H[Neo4j]
        E --> I[Redis]
        E --> J[MinIO]
        
        A --> K[Audit Logger]
        D --> K
    end
    
    subgraph "Sandbox Container"
        L[Sandbox FastAPI] --> M[Code Executor]
        M --> N[Database HTTP Client]
        N --> O[Request Builder]
        P[Security Monitor] --> M
        Q[Resource Manager] --> M
    end
    
    O --> |HTTP + Auth| C
    C --> |Results| N
    
    B --> |Pipeline Request| L
    L --> |Results + Debug| B
```

### Key Components

#### 1. **Main Application**
- **FastAPI Backend**: Core API server handling user requests
- **Database API Layer**: HTTP API endpoints for database operations
- **Authorization System**: Permission management and access control
- **Database Manager**: Centralized database connection management
- **Audit Logger**: Comprehensive logging of all database operations

#### 2. **Sandbox Container**
- **Sandbox FastAPI**: Isolated API server for code execution
- **Code Executor**: Secure Python code execution using RestrictedPython
- **Database HTTP Client**: HTTP client for database operations via main app
- **Security Monitor**: Resource monitoring and security enforcement
- **Resource Manager**: CPU, memory, and execution time limits

## 🔐 Security Model

### Database-as-a-Service Architecture

The main innovation is **centralizing all database connections** in the main application while exposing them via HTTP APIs with comprehensive authorization. This provides:

1. **Centralized Security**: All database access controlled by main app
2. **No Direct Database Access**: Sandbox containers cannot bypass authorization
3. **Complete Audit Trail**: Every database operation logged with full context
4. **Fine-grained Permissions**: User-specific access control to tables and operations

### Security Layers

#### 1. **Code Execution Security**
- **RestrictedPython**: Safer than raw `exec()` with compile-time restrictions
- **Import Whitelisting**: Only allowed modules can be imported
- **Resource Limits**: CPU time, memory, and file system access limits
- **AST Manipulation**: Dangerous functions removed at parse time

#### 2. **Database Access Security**
- **HTTP API Gateway**: All database operations via authenticated HTTP requests
- **Query Validation**: SQL injection prevention and operation whitelisting
- **User Context Enforcement**: Automatic user_id filtering in all queries
- **Permission Matrix**: Role-based access control for different operations

#### 3. **Network Security**
- **Isolated Network**: Sandbox containers in separate Docker network
- **Minimal Attack Surface**: Only HTTP access to main app allowed
- **No Internet Access**: Prevents external data exfiltration

## 🔗 Database API Design

### API Endpoints

```
POST /api/v1/db/postgres/query     # Execute PostgreSQL query
POST /api/v1/db/elasticsearch/search # Search Elasticsearch
POST /api/v1/db/neo4j/query        # Execute Neo4j query
POST /api/v1/db/redis/command      # Execute Redis command
POST /api/v1/db/minio/operation    # MinIO file operations
```

### Authorization Model

```python
# Authentication Flow
1. Main app creates execution token for sandbox
2. Sandbox uses token for all database requests
3. Main app validates token and user permissions
4. Query executed with user context automatically added
5. All operations logged with execution context
```

### Permission Matrix

| Operation | Public Tables | User Tables | Admin Tables |
|-----------|---------------|-------------|--------------|
| SELECT    | ✅ All users  | ✅ Owner only | ❌ Admin only |
| INSERT    | ❌ Restricted | ✅ Owner only | ❌ Admin only |
| UPDATE    | ❌ Restricted | ✅ Owner only | ❌ Admin only |
| DELETE    | ❌ Restricted | ✅ Owner only | ❌ Admin only |

## 🚀 Pipeline Execution Flow

### 1. **Pipeline Request**
```python
# User requests pipeline execution
POST /api/v1/processors/pipelines/{pipeline_id}/execute
{
    "file_hash": "abc123",
    "custom_config": {...},
    "debug_level": "verbose"
}
```

### 2. **Sandbox Execution**
```python
# Main app sends request to sandbox
POST http://sandbox:8001/execute/pipeline
{
    "pipeline_config": {...},
    "input_data": {...},
    "auth_token": "jwt_token_with_permissions",
    "execution_context": {
        "user_id": 123,
        "execution_id": "uuid",
        "debug_level": "verbose"
    }
}
```

### 3. **Database Operations**
```python
# Sandbox makes database requests
POST http://main-app:8000/api/v1/db/postgres/query
Authorization: Bearer <execution_token>
{
    "query": "SELECT * FROM user_documents WHERE id = %(doc_id)s",
    "params": {"doc_id": 1},
    "execution_context": {...}
}
```

### 4. **Results & Debugging**
```python
# Sandbox returns comprehensive results
{
    "execution_id": "uuid",
    "status": "completed",
    "result": {...},
    "debug_info": {
        "steps": [...],
        "performance": {...},
        "database_operations": [...],
        "variable_snapshots": [...]
    }
}
```

## 🛠️ Technology Stack

### Backend Framework
- **FastAPI**: Modern, fast web framework
- **SQLAlchemy**: Database ORM with async support
- **Pydantic**: Data validation and serialization

### Databases
- **PostgreSQL**: Primary relational database
- **Elasticsearch**: Full-text search and analytics
- **Neo4j**: Graph database for relationships
- **Redis**: Caching and session storage
- **MinIO**: S3-compatible object storage

### Security & Monitoring
- **RestrictedPython**: Secure code execution
- **JWT**: Token-based authentication
- **OpenTelemetry**: Distributed tracing
- **Prometheus**: Metrics collection
- **Structured Logging**: JSON-formatted logs

### Container Orchestration
- **Docker**: Containerization
- **Docker Compose**: Local development
- **Kubernetes**: Production deployment (optional)

## 🔧 Development Setup

### Prerequisites
```bash
# Required services
- Docker & Docker Compose
- Python 3.11+
- Poetry (for dependency management)
```

### Local Development
```bash
# 1. Clone repository
git clone <repository-url>
cd brain-net-backend

# 2. Setup virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup environment variables
cp .env.example .env
# Edit .env with your configuration

# 5. Start services
docker-compose up -d postgres elasticsearch neo4j redis minio

# 6. Run migrations
python migrate.py

# 7. Start main application
python main.py

# 8. Start sandbox container
docker-compose up -d sandbox
```

## 📊 API Documentation

### Interactive API Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Health Checks
- **Basic Health**: `GET /health`
- **Detailed Health**: `GET /health/detailed`
- **Service-specific**: `GET /health/{service_name}`

## 🔍 Monitoring & Debugging

### Logs
- **Application Logs**: Structured JSON logs
- **Audit Logs**: Database operation logs
- **Security Logs**: Authorization and access logs

### Metrics
- **Application Metrics**: Request latency, throughput
- **Database Metrics**: Query performance, connection pools
- **Security Metrics**: Failed authentications, blocked operations

### Tracing
- **Distributed Tracing**: OpenTelemetry integration
- **Request Tracing**: End-to-end request tracking
- **Database Tracing**: Query execution traces

## 🚀 Deployment

### Docker Compose (Development)
```bash
docker-compose up -d
```

### Kubernetes (Production)
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/
```

### Environment Variables
```env
# Database Configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/brain_net
ELASTICSEARCH_URL=http://localhost:9200
NEO4J_URI=bolt://localhost:7687
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256

# Sandbox Configuration
SANDBOX_IMAGE=brain-net-sandbox:latest
SANDBOX_RESOURCE_LIMITS=cpu=1,memory=2g
```

## 📈 Performance Considerations

### Database Optimization
- **Connection Pooling**: Configured pool sizes per service
- **Query Optimization**: Indexed queries and efficient schemas
- **Caching Strategy**: Redis caching for frequently accessed data

### Sandbox Optimization
- **Container Warm-up**: Pre-loaded containers for faster execution
- **Resource Limits**: Controlled CPU and memory usage
- **Execution Timeouts**: Prevents runaway processes

## 🔒 Security Best Practices

### Code Execution
- **RestrictedPython**: Compile-time security restrictions
- **Import Filtering**: Whitelist of allowed modules
- **Resource Limits**: CPU, memory, and time constraints

### Database Access
- **Query Validation**: SQL injection prevention
- **User Context**: Automatic user filtering
- **Audit Logging**: Complete operation history

### Network Security
- **Network Isolation**: Separate Docker networks
- **Minimal Exposure**: Only required ports exposed
- **TLS Encryption**: HTTPS for all communications

## 🧪 Testing

### Unit Tests
```bash
pytest tests/unit/
```

### Integration Tests
```bash
pytest tests/integration/
```

### Security Tests
```bash
pytest tests/security/
```

## 📋 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Run security checks
5. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
