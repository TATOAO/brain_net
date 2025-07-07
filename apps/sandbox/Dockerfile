# Use official Python runtime as base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Sandbox configuration
ENV SANDBOX_HOST=0.0.0.0
ENV SANDBOX_PORT=8002
ENV BACKEND_URL=http://backend:8000
ENV EXECUTION_TIMEOUT=60
ENV MAX_CONCURRENT_EXECUTIONS=10
ENV DEBUG_MODE=true
ENV LOG_LEVEL=INFO

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN groupadd -r sandbox && useradd -r -g sandbox -m sandbox

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/tmp && \
    chown -R sandbox:sandbox /app

# Switch to non-root user
USER sandbox

# Expose port
EXPOSE ${SANDBOX_PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${SANDBOX_PORT}/health || exit 1

# Command to run the application
CMD ["sh", "-c", "uvicorn main:app --host ${SANDBOX_HOST} --port ${SANDBOX_PORT} --reload"] 