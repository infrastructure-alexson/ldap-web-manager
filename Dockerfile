# Multi-stage Dockerfile for LDAP Web Manager
# Production-ready Docker image with optimized layers

# Stage 1: Backend Build
FROM python:3.11-slim as backend-builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements.txt .

# Build wheels for faster installation
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# Stage 2: Frontend Build
FROM node:18-alpine as frontend-builder

WORKDIR /build

# Copy frontend dependencies
COPY frontend/package*.json ./

# Install dependencies and build
RUN npm ci && npm run build

# Stage 3: Runtime
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

# Copy Python wheels from builder
COPY --from=backend-builder /build/wheels /wheels
COPY --from=backend-builder /build/requirements.txt .

# Install Python dependencies from wheels
RUN pip install --no-cache /wheels/*

# Copy backend application
COPY backend/ ./backend/

# Copy built frontend
COPY --from=frontend-builder /build/dist ./frontend/dist

# Copy nginx config
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/sites-available/ldap-manager.conf /etc/nginx/conf.d/default.conf

# Create necessary directories
RUN mkdir -p /app/logs /app/data && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose ports
EXPOSE 8000 8080

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Run application
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

