#!/bin/bash

# Build script with caching optimizations
# This script uses Docker BuildKit for advanced caching features

set -e

echo "Building LLM service with caching optimizations..."

# Enable Docker BuildKit
export DOCKER_BUILDKIT=1

# Build arguments for mirrors (optional)
APT_MIRROR="${APT_MIRROR:-}"
APT_SECURITY_MIRROR="${APT_SECURITY_MIRROR:-}"
PYPI_INDEX_URL="${PYPI_INDEX_URL:-}"
PYPI_TRUSTED_HOST="${PYPI_TRUSTED_HOST:-}"

# Build with cache mounts and build arguments
docker build \
    --build-arg APT_MIRROR="$APT_MIRROR" \
    --build-arg APT_SECURITY_MIRROR="$APT_SECURITY_MIRROR" \
    --build-arg PYPI_INDEX_URL="$PYPI_INDEX_URL" \
    --build-arg PYPI_TRUSTED_HOST="$PYPI_TRUSTED_HOST" \
    --tag brain-net-llm:latest \
    --file apps/llm/Dockerfile \
    .

echo "Build completed successfully!"
echo ""
echo "Tips for faster rebuilds:"
echo "- Only modify requirements-custom.txt for experimental packages"
echo "- Keep requirements-base.txt stable for production dependencies"
echo "- Use 'docker system prune -f' occasionally to clean up unused cache" 