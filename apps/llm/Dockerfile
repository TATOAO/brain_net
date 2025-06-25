# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Accept build arguments for mirrors
ARG APT_MIRROR=""
ARG APT_SECURITY_MIRROR=""
ARG PYPI_INDEX_URL=""
ARG PYPI_TRUSTED_HOST=""

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
    build-essential \
    curl \
    software-properties-common \
    git \
    tesseract-ocr \
    poppler-utils \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster package installation
RUN pip install --no-cache-dir uv

# Copy requirements first for better caching
COPY apps/llm/requirements.txt /app/

# Install Python dependencies as root
RUN if [ -n "$PYPI_INDEX_URL" ]; then \
        if [ -n "$PYPI_TRUSTED_HOST" ]; then \
            uv pip install --system --no-cache-dir -r requirements.txt -i $PYPI_INDEX_URL --trusted-host $PYPI_TRUSTED_HOST; \
        else \
            uv pip install --system --no-cache-dir -r requirements.txt -i $PYPI_INDEX_URL; \
        fi; \
    else \
        uv pip install --system --no-cache-dir -r requirements.txt; \
    fi

# Create directories
RUN mkdir -p /app/logs /app/data /app/models /app/cache

# Copy application code
COPY apps/llm/ /app/
COPY apps/shared/ /app/apps/shared/

# Make start script executable
RUN chmod +x /app/start.sh

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Expose port
EXPOSE 8001

# Set default command
CMD ["/app/start.sh"] 