# Brain Net Frontend - Health Dashboard

A Next.js React application that monitors the health status of all Brain Net backend services.

## Features

- **Real-time Health Monitoring**: Displays health status of all backend services (PostgreSQL, Elasticsearch, Neo4j, MinIO, Redis)
- **Auto-refresh**: Updates health data every 10 seconds automatically
- **Responsive Design**: Modern, clean UI that works on desktop and mobile
- **Detailed Information**: Shows response times, timestamps, and detailed service information
- **Status Indicators**: Clear visual indicators for healthy/unhealthy services

## Prerequisites

- Node.js 18+ 
- pnpm (installed globally)
- Brain Net backend running on localhost:8000

## Setup

1. **Install dependencies**:
   ```bash
   pnpm install
   ```

2. **Start the development server**:
   ```bash
   pnpm dev
   ```

3. **Open your browser** and navigate to http://localhost:3000

## Backend Integration

The frontend connects to the Brain Net backend API running on `localhost:8000` and calls the following endpoints:

- `/health/detailed` - Gets overall system status and all service health checks
- Individual service health endpoints are displayed in the UI

## Services Monitored

- **PostgreSQL** - Primary database
- **Elasticsearch** - Search and indexing
- **Neo4j** - Graph database
- **MinIO** - Object storage
- **Redis** - Caching layer

## Build for Production

```bash
pnpm build
pnpm start
```

## Docker Support

The included Dockerfile can be used to run the frontend in a container:

```bash
docker build -t brain-net-frontend .
docker run -p 3000:3000 brain-net-frontend
```

## Configuration

The frontend automatically proxies API requests to the backend through Next.js rewrites configured in `next.config.js`. If your backend runs on a different host/port, update the configuration there. 