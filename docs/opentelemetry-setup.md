# OpenTelemetry Setup for Brain_Net

This document explains the OpenTelemetry (OTel) observability setup for the Brain_Net project.

## Overview

OpenTelemetry provides comprehensive observability for your distributed system by collecting:
- **Traces**: Request flows across services
- **Metrics**: Performance measurements and counters
- **Logs**: Structured logging with trace correlation

## Architecture

```
Your Services → OTel Collector → Jaeger (traces) + Prometheus (metrics)
                              ↓
                           Grafana (visualization)
```

## Quick Start

### 1. Start Observability Stack

```bash
cd docker
./start-observability.sh start
```

This will start:
- **Jaeger**: Trace storage and UI
- **OpenTelemetry Collector**: Data processing and routing
- **Prometheus**: Metrics collection (already running)
- **Grafana**: Dashboards and visualization (already running)

### 2. Start Your Services

```bash
# Start all services including observability
docker-compose -f docker-compose.yml -f docker-compose.observability.yml up -d

# Or start just your application services (OTel will be disabled)
docker-compose up -d
```

### 3. Access Dashboards

- **Jaeger UI**: http://localhost:16686 - View distributed traces
- **Prometheus**: http://localhost:9090 - Query metrics
- **Grafana**: http://localhost:3001 - Dashboards (admin/admin)
- **OTel Collector zPages**: http://localhost:55679 - Collector status

## Configuration

### Environment Variables

The following environment variables control OpenTelemetry:

```bash
# Enable/disable OpenTelemetry
OTEL_ENABLED=true                    # Enable OTel instrumentation
OTEL_REQUIRED=false                  # Fail if OTel setup fails

# OpenTelemetry Collector endpoint
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317

# Service identification
OTEL_SERVICE_NAME=brain_net_backend  # Service name in traces
OTEL_SERVICE_VERSION=1.0.0          # Service version
ENVIRONMENT=development              # Deployment environment
```

### Service Configuration

Each service has its own OTel configuration in `app/core/telemetry.py`:

- **Backend Service**: `brain_net_backend`
- **LLM Service**: `brain_net_llm`

## Features

### Automatic Instrumentation

The following libraries are automatically instrumented:

- **FastAPI**: HTTP requests and responses
- **SQLAlchemy/AsyncPG**: Database queries
- **Redis**: Cache operations
- **HTTP Clients**: HTTPX and Requests
- **Logging**: Correlated log messages

### Custom Instrumentation

#### Creating Custom Spans

```python
from app.core.telemetry import get_tracer

tracer = get_tracer()

# Simple span
with tracer.start_as_current_span("my_operation") as span:
    span.set_attribute("user.id", user_id)
    span.add_event("Processing started")
    # Your code here
    span.add_event("Processing completed")
```

#### Recording Custom Metrics

```python
from app.core.telemetry import get_meter

meter = get_meter()

# Create metrics
request_counter = meter.create_counter(
    name="my_requests_total",
    description="Total requests processed"
)

response_time = meter.create_histogram(
    name="my_response_time_seconds",
    description="Response time in seconds"
)

# Record metrics
request_counter.add(1, {"endpoint": "/api/users"})
response_time.record(0.145, {"status": "success"})
```

### Example Services

See comprehensive examples in:
- `apps/backend/app/services/telemetry_example.py`
- `apps/llm/app/services/telemetry_example.py`

## Use Cases

### 1. Debugging Distributed Requests

When a user reports an issue:
1. Go to Jaeger UI
2. Search by service name and time range
3. Find the specific trace
4. See the complete request flow across services
5. Identify bottlenecks or errors

### 2. Performance Monitoring

Track key metrics:
- API response times
- Database query performance
- LLM request latency
- Token usage and costs
- Error rates

### 3. Business Intelligence

Monitor business metrics:
- User activity patterns
- Feature usage
- Document processing volumes
- AI model performance

## Trace Examples

### Backend Service Trace
```
User Request (3.2s)
├── Validate Request (0.1s)
├── Fetch User Data (0.2s) 
│   └── Database Query (0.18s)
├── Process Business Logic (2.5s)
│   ├── Data Processing (0.15s)
│   ├── LLM Service Call (2.0s)  ← External service
│   └── Cache Update (0.05s)
└── Response Generation (0.3s)
```

### LLM Service Trace
```
RAG Query (4.1s)
├── Generate Embeddings (0.3s)
│   └── OpenAI API Call (0.28s)
├── Vector Search (0.2s)
│   └── Elasticsearch Query (0.18s)
├── Retrieve Context (0.1s)
└── Generate Response (3.5s)
    └── GPT-3.5 API Call (3.4s)
```

## Custom Metrics

### Backend Metrics
- `backend_requests_total`: Total API requests
- `backend_request_duration_seconds`: Request processing time
- `backend_database_operations_total`: Database operations
- `backend_llm_requests_total`: Requests to LLM service

### LLM Metrics
- `llm_requests_total`: LLM API calls
- `llm_tokens_used_total`: Token consumption
- `embedding_requests_total`: Embedding generations
- `vector_searches_total`: Vector database searches
- `rag_pipeline_duration_seconds`: RAG processing time

## Troubleshooting

### Common Issues

1. **Services not sending traces**
   ```bash
   # Check if collector is running
   docker logs brain_net_otel_collector
   
   # Check service logs
   docker logs brain_net_backend
   docker logs brain_net_llm
   ```

2. **No data in Jaeger**
   - Verify `OTEL_ENABLED=true`
   - Check collector endpoint configuration
   - Ensure services can reach the collector

3. **High memory usage**
   - Adjust batch processor settings in `otel-collector.yml`
   - Reduce sampling rate for high-volume services

### Debugging Commands

```bash
# Check collector health
curl http://localhost:13133

# View collector metrics
curl http://localhost:8888/metrics

# Check collector status
curl http://localhost:55679/debug/tracez

# View service telemetry
./start-observability.sh logs otel-collector
./start-observability.sh logs jaeger
```

## Development Tips

### Best Practices

1. **Meaningful Span Names**: Use descriptive operation names
2. **Rich Attributes**: Add context like user IDs, request types
3. **Error Handling**: Always record exceptions in spans
4. **Performance**: Use sampling for high-volume operations
5. **Business Context**: Include domain-specific attributes

### Example Instrumentation Patterns

```python
# Pattern 1: Context manager for operations
async with telemetry_service.trace_operation(
    "process_user_request",
    user_id=user_id,
    request_type=request_type
) as span:
    # Your code here
    span.add_event("Operation completed")

# Pattern 2: Service-to-service calls
with tracer.start_as_current_span("llm_service_call") as span:
    span.set_attributes({
        "service.name": "brain_net_llm",
        "llm.model": "gpt-3.5-turbo"
    })
    response = await llm_client.chat_completion(messages)
    span.set_attribute("llm.tokens_used", response.usage.total_tokens)

# Pattern 3: Database operations
with tracer.start_as_current_span("user_query") as span:
    span.set_attributes({
        "db.operation": "SELECT",
        "db.table": "users"
    })
    users = await db.query(User).filter(User.id == user_id).all()
    span.set_attribute("db.rows_affected", len(users))
```

## Integration with Existing Monitoring

OpenTelemetry complements your existing monitoring:

- **Prometheus**: Collects OTel metrics alongside existing metrics
- **Grafana**: Create dashboards combining OTel and existing data
- **ELK Stack**: Correlate traces with log entries using trace IDs
- **Health Checks**: Monitor OTel collector health

## Production Considerations

### Performance Impact
- Automatic instrumentation: ~1-5% overhead
- Custom instrumentation: Minimal with proper sampling
- Network overhead: Batched export minimizes impact

### Sampling
Configure sampling for high-volume services:
```yaml
# In otel-collector.yml
processors:
  probabilistic_sampler:
    sampling_percentage: 10  # Sample 10% of traces
```

### Security
- Use secure endpoints in production
- Configure authentication for collector
- Limit trace data retention
- Sanitize sensitive data in spans

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review service logs
3. Consult OpenTelemetry documentation
4. Use the management script: `./start-observability.sh status`

## References

- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [OTLP Specification](https://github.com/open-telemetry/opentelemetry-specification/blob/main/specification/protocol/otlp.md) 