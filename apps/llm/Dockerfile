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

# Create non-root user
RUN useradd --create-home --shell /bin/bash llm && \
    chown -R llm:llm /app
USER llm

# Create directories
RUN mkdir -p /app/logs /app/data /app/models /app/cache

# Copy requirements first for better caching
COPY --chown=llm:llm apps/llm/requirements.txt /app/

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

# Add user's pip bin to PATH
ENV PATH="/home/llm/.local/bin:${PATH}"

# Copy application code
COPY --chown=llm:llm apps/llm/ /app/
COPY --chown=llm:llm apps/shared/ /app/apps/shared/

# Create startup script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Create logs directory if it doesn'\''t exist\n\
mkdir -p /app/logs\n\
\n\
# Download spacy model if needed\n\
python -c "import spacy; spacy.cli.download('\''en_core_web_sm'\'')" 2>/dev/null || true\n\
\n\
# Start the application\n\
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload\n\
' > /app/start.sh && chmod +x /app/start.sh

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Set default command
CMD ["/app/start.sh"] 