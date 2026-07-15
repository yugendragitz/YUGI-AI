# =============================================================================
# YUGI-AI Backend — Multi-Stage Dockerfile
# =============================================================================
# Stages:
#   1. base:        Common Python setup, non-root user, system dependencies
#   2. development: Hot reload with uvicorn --reload, source mounted via volume
#   3. production:  Optimized image with gunicorn, no dev dependencies
#
# Build targets:
#   docker build --target development -t yugi-backend:dev .
#   docker build --target production -t yugi-backend:prod .
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Base — Common setup for all stages
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS base

# Metadata labels
LABEL maintainer="YUGI-AI Team"
LABEL description="YUGI-AI Backend — FastAPI Application"
LABEL version="0.1.0"

# Prevent Python from writing .pyc files and enable unbuffered output
# for real-time log visibility in Docker
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # pip configuration
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies required by:
#   - asyncpg: libpq-dev (PostgreSQL client library)
#   - bcrypt/cryptography: gcc, libffi-dev (C compilation)
#   - general: curl (health checks)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        libpq-dev \
        gcc \
        libffi-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user for security
# Running as root inside containers is a security risk — any container
# escape would grant root access to the host.
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Set working directory
WORKDIR /app

# ---------------------------------------------------------------------------
# Stage 2: Development — Hot reload, all dependencies
# ---------------------------------------------------------------------------
FROM base AS development

# Copy full source (editable install requires the package to exist)
# In development, app/ is overridden by volume mount
COPY . .

# Install all dependencies including dev extras
# Editable install so mounted volume changes are reflected immediately
RUN pip install -e ".[dev]" 2>/dev/null || pip install -e "."

# Switch to non-root user
USER appuser

# Expose port for direct access
EXPOSE 8000

# Development server with hot reload
# --reload watches for file changes and restarts automatically
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--reload", \
     "--reload-dir", "app", \
     "--log-level", "debug"]

# ---------------------------------------------------------------------------
# Stage 3: Production — Optimized, minimal image
# ---------------------------------------------------------------------------
FROM base AS production

# Copy full source for installation
COPY . .

# Install production dependencies only (no dev extras)
# Then remove build-time system packages to reduce image size
RUN pip install . && \
    apt-get update && \
    apt-get purge -y --auto-remove gcc libffi-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Ensure proper ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check — verify the application is responsive
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Production server with multiple workers
# Workers = (2 * CPU_CORES) + 1, configurable via BACKEND_WORKERS env var
# uvicorn is used directly (not gunicorn) because:
#   - Native ASGI support without adapter overhead
#   - Built-in WebSocket support required for Socket.IO
#   - Simpler configuration for async workloads
CMD ["sh", "-c", \
     "uvicorn app.main:app \
      --host 0.0.0.0 \
      --port 8000 \
      --workers ${BACKEND_WORKERS:-2} \
      --log-level ${LOG_LEVEL:-info} \
      --access-log \
      --proxy-headers \
      --forwarded-allow-ips '*'"]
