# Brain_Net Sandbox Service

A long-lived Docker container with FastAPI interface for executing pipeline code in a controlled sandbox environment. The sandbox provides debugging information and processor adjustment capabilities to help AI systems regenerate and improve code.

## Features

- **Secure Code Execution**: Execute Python code in a sandboxed environment with timeout controls
- **Debug Information**: Capture detailed execution information including variables, stdout/stderr, and exceptions
- **Processor Adjustment**: Send processor improvement suggestions back to the main backend
- **Asynchronous Execution**: Non-blocking code execution with result tracking
- **RESTful API**: Clean FastAPI interface for integration with other services
- **Health Monitoring**: Built-in health checks and monitoring endpoints

## API Endpoints

### Core Endpoints

- `GET /` - Root endpoint with service information
- `GET /health` - Health check with execution statistics
- `GET /docs` - Interactive API documentation (Swagger UI)

### Code Execution

- `POST /execute` - Execute code in sandbox
- `GET /execution/{execution_id}` - Get execution result by ID
- `GET /executions` - List recent executions (paginated)
- `DELETE /execution/{execution_id}` - Cancel running execution

### Debugging

- `GET /debug/{execution_id}` - Get detailed debug information
- `POST /adjust-processor` - Send processor adjustment recommendations

## Request/Response Models

### Code Execution Request

```json
{
  "code": "print('Hello, World!')",
  "processor_id": "optional-processor-id",
  "input_data": {
    "key": "value"
  },
  "timeout": 30,
  "debug_mode": true
}
```

### Execution Result

```json
{
  "execution_id": "uuid-string",
  "status": "completed",
  "output": "Hello, World!\n",
  "error": null,
  "debug_info": {
    "variables_after": {},
    "exceptions": []
  },
  "start_time": "2024-01-01T00:00:00Z",
  "end_time": "2024-01-01T00:00:01Z",
  "execution_time": 1.0
}
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

### Running with Docker

1. Build and run the sandbox container:

```bash
docker-compose up --build
```

2. The sandbox will be available at `http://localhost:8001`

3. Access the API documentation at `http://localhost:8001/docs`

### Running Locally

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start the application:

```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

## Usage Examples

### Execute Simple Code

```bash
curl -X POST "http://localhost:8001/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "result = 2 + 2\nprint(f\"Result: {result}\")",
    "debug_mode": true
  }'
```

### Check Execution Status

```bash
curl "http://localhost:8001/execution/{execution_id}"
```

### Get Debug Information

```bash
curl "http://localhost:8001/debug/{execution_id}"
```

### Send Processor Adjustment

```bash
curl -X POST "http://localhost:8001/adjust-processor" \
  -H "Content-Type: application/json" \
  -d '{
    "processor_id": "processor-123",
    "adjustments": {
      "parameter_x": "new_value",
      "optimization": "enabled"
    },
    "reason": "Performance improvement based on execution results"
  }'
```

## Security Considerations

- **Non-root User**: Container runs as a non-root user for security
- **Restricted Python**: Uses RestrictedPython for safer code execution
- **Timeout Controls**: Configurable execution timeouts prevent runaway processes
- **Resource Limits**: Consider setting Docker resource limits in production
- **Network Isolation**: Use Docker networks for service isolation

## Configuration

Environment variables:

- `BACKEND_URL`: URL of the main backend service (default: http://backend:8000)
- `LOG_LEVEL`: Logging level (default: INFO)
- `EXECUTION_TIMEOUT`: Default execution timeout in seconds (default: 60)
- `MAX_CONCURRENT_EXECUTIONS`: Maximum concurrent executions (default: 10)

## Integration with Backend

The sandbox communicates with the main backend service via HTTP requests:

- Sends processor adjustment recommendations
- Can fetch processor definitions and configurations
- Integrates with the main authentication and authorization system

## Development

### Project Structure

```
apps/sandbox/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container configuration
├── docker-compose.yml  # Service orchestration
└── README.md           # This file
```

### Adding New Features

1. **New Endpoints**: Add routes to `main.py`
2. **Models**: Define Pydantic models for request/response validation
3. **Security**: Implement additional sandboxing features as needed
4. **Integration**: Update backend communication endpoints

## Monitoring and Logging

- **Health Checks**: Built-in health check endpoints
- **Execution Metrics**: Track execution statistics and performance
- **Error Logging**: Comprehensive error logging with stack traces
- **Debug Information**: Detailed execution debugging for AI feedback

## Production Deployment

### Security Hardening

1. **Resource Limits**: Set memory and CPU limits
2. **Network Policies**: Restrict network access
3. **Volume Mounts**: Use read-only mounts where possible
4. **User Permissions**: Ensure proper user/group permissions

### Scaling

1. **Load Balancing**: Use multiple sandbox instances
2. **Shared Storage**: Use Redis or database for execution results
3. **Queue System**: Implement job queues for high-throughput scenarios

## Troubleshooting

### Common Issues

1. **Timeout Errors**: Increase execution timeout or optimize code
2. **Memory Issues**: Set appropriate Docker memory limits
3. **Network Connectivity**: Ensure backend service is accessible
4. **Permission Errors**: Check file permissions and user configuration

### Debug Mode

Enable debug mode for detailed execution information:

```json
{
  "code": "your_code_here",
  "debug_mode": true
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 