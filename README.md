# Brain_Net

An intelligent and highly visualized RAG (Retrieval-Augmented Generation) system for local knowledge base management.

## 🏗️ System Architecture

### Overview
Brain_Net is a comprehensive knowledge base system that intelligently manages document processing, retrieval accuracy monitoring, and provides real-time visualization through a modern web interface.

### Core Components

#### 🚀 Backend (FastAPI + Python)
- **Document Processing Pipeline**: Intelligent parsing, chunking, and indexing
- **Query Generation Engine**: Automated test query creation for accuracy validation
- **Retrieval Monitoring**: Real-time accuracy tracking and bad case detection
- **API Layer**: RESTful endpoints for frontend communication
- **LangChain Integration**: LLM-powered document understanding and processing

#### 🎨 Frontend (Next.js + React + TypeScript)
- **Modern Web Interface**: Responsive, intuitive user experience
- **Real-time Visualization**: Live processing status and analytics
- **Interactive Dashboard**: Document management and query testing
- **Analytics Dashboard**: Retrieval accuracy metrics and insights

#### 🗄️ Database Layer
- **PostgreSQL**: Primary database for metadata, user data, and structured information
- **Elasticsearch**: High-performance document indexing and full-text search
- **Neo4j**: Knowledge graph for document relationships and semantic connections
- **MinIO**: Scalable object storage for document files and artifacts

#### 🤖 AI/ML Components
- **LangChain**: LLM orchestration and document processing
- **Query Generation**: Intelligent test query creation
- **Accuracy Evaluation**: Automated retrieval quality assessment
- **Semantic Search**: Advanced document similarity and retrieval

### Key Features
- 📁 **Document Upload**: Support for multiple file formats and folder paths
- 🔍 **Intelligent Chunking**: Context-aware document segmentation
- 🎯 **Query Generation**: Automated test query creation for accuracy validation
- 📊 **Real-time Monitoring**: Live retrieval accuracy tracking
- 🎨 **Rich Visualization**: Interactive dashboards and analytics
- 🔄 **Continuous Learning**: System improvement through feedback loops

### Technology Stack
- **Backend**: FastAPI, Python 3.11+, LangChain, Pydantic
- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS
- **Databases**: PostgreSQL, Elasticsearch, Neo4j, MinIO
- **AI/ML**: LangChain, OpenAI/Anthropic APIs, Sentence Transformers
- **Infrastructure**: Docker, Docker Compose, Nginx
- **Monitoring**: Prometheus, Grafana, ELK Stack

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ and npm/yarn
- Python 3.11+

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd brain_net

# Start the entire system
docker-compose -f docker/docker-compose.yml up -d 

# Or run components individually
cd apps/backend && source .venv/bin/activate && uvicorn main:app --reload
cd apps/frontend && npm install && npm run dev
```

## 📁 Project Structure
```
brain_net/
├── apps/
│   ├── backend/           # FastAPI backend application
│   ├── frontend/          # Next.js frontend application
│   └── shared/            # Shared utilities and types
├── docker/                # Docker configurations
├── docs/                  # Documentation
└── scripts/               # Utility scripts
```

## 🔧 Configuration
Detailed configuration options and environment variables are documented in each component's README.

## 📚 Documentation
- [Backend API Documentation](./apps/backend/README.md)
- [Frontend User Guide](./apps/frontend/README.md)
- [Deployment Guide](./docs/deployment.md)
- [Architecture Details](./docs/architecture.md)

