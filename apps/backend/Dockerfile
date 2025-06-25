# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

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
            pip install --no-cache-dir uv -i $PYPI_INDEX_URL --trusted-host $PYPI_TRUSTED_HOST; \
        else \
            pip install --no-cache-dir uv -i $PYPI_INDEX_URL; \
        fi; \
    else \
        pip install --no-cache-dir uv; \
    fi

# Copy requirements first for better caching
COPY apps/backend/requirements.txt .

# Set default PyPI index URL - can be overridden with build args
ARG PYPI_INDEX_URL=""
ARG PYPI_TRUSTED_HOST=""

# Install Python dependencies using uv (much faster than pip)
# Only add -i flag if PYPI_INDEX_URL is provided
RUN if [ -n "$PYPI_INDEX_URL" ]; then \
        if [ -n "$PYPI_TRUSTED_HOST" ]; then \
            uv pip install --system --no-cache -r requirements.txt -i $PYPI_INDEX_URL --trusted-host $PYPI_TRUSTED_HOST; \
        else \
            uv pip install --system --no-cache -r requirements.txt -i $PYPI_INDEX_URL; \
        fi; \
    else \
        uv pip install --system --no-cache -r requirements.txt; \
    fi

# Copy shared models and apps package structure
COPY apps/__init__.py /app/apps/__init__.py
COPY apps/shared /app/apps/shared

# Copy application code
COPY apps/backend/ .

# Create logs directory
RUN mkdir -p logs

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 