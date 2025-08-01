# Use Python 3.11 slim image
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

# Accept build arguments for mirrors
ARG APT_MIRROR=""
ARG APT_SECURITY_MIRROR=""

# Configure APT mirrors if provided
RUN if [ -n "$APT_MIRROR" ]; then \
        echo "Configuring APT mirror: $APT_MIRROR"; \
        echo "deb http://$APT_MIRROR bookworm main" > /etc/apt/sources.list && \
        echo "deb http://$APT_MIRROR bookworm-updates main" >> /etc/apt/sources.list; \
        if [ -n "$APT_SECURITY_MIRROR" ]; then \
            echo "deb http://$APT_SECURITY_MIRROR bookworm-security main" >> /etc/apt/sources.list; \
        fi; \
    fi

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster package installation
RUN if [ -n "$PYPI_INDEX_URL" ]; then \
        if [ -n "$PYPI_TRUSTED_HOST" ]; then \
            pip install  uv -i $PYPI_INDEX_URL --trusted-host $PYPI_TRUSTED_HOST; \
        else \
            pip install  uv -i $PYPI_INDEX_URL; \
        fi; \
    else \
        pip install uv; \
    fi

# Copy requirements first for better caching
COPY apps/sandbox/requirements.txt .

# Set default PyPI index URL - can be overridden with build args
ARG PYPI_INDEX_URL=""
ARG PYPI_TRUSTED_HOST=""
ARG GITHUB_TOKEN=""

RUN apt-get update && apt-get install -y git

RUN git config --global http.postBuffer 524288000 && \
    git config --global http.version HTTP/1.1 && \
    git config --global http.lowSpeedLimit 0 && \
    git config --global http.lowSpeedTime 999999

# Configure git credentials if GitHub token is provided
RUN if [ -n "$GITHUB_TOKEN" ]; then \
        git config --global credential.helper store && \
        echo "https://$GITHUB_TOKEN@github.com" > ~/.git-credentials; \
    fi

# Install Python dependencies using uv (much faster than pip)
# Only add -i flag if PYPI_INDEX_URL is provided
RUN if [ -n "$PYPI_INDEX_URL" ]; then \
        if [ -n "$PYPI_TRUSTED_HOST" ]; then \
            uv pip install --system -r requirements.txt -i $PYPI_INDEX_URL --trusted-host $PYPI_TRUSTED_HOST; \
        else \
            uv pip install --system -r requirements.txt -i $PYPI_INDEX_URL; \
        fi; \
    else \
        uv pip install --system -r requirements.txt; \
    fi

# Copy shared models and apps package structure
COPY apps/__init__.py /app/apps/__init__.py
COPY apps/shared /app/apps/shared

# Copy application code
COPY apps/sandbox/ .

# Create logs directory
RUN mkdir -p logs tmp

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port (internal container port is always 8002)
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"] 