# Multi-stage build for DMLog production deployment
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY source_code/frontend/package*.json ./
RUN npm ci --only=production && npm cache clean --force

# Copy frontend source and build
COPY source_code/frontend/ ./
RUN npm run build

# Python backend stage
FROM python:3.11-slim AS backend

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r dmlog && useradd -r -g dmlog dmlog

WORKDIR /app

# Install Python dependencies
COPY source_code/backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY source_code/backend/ ./
COPY docker/scripts/ ./scripts/

# Copy frontend build artifacts
COPY --from=frontend-builder /app/frontend/dist ./static/

# Set permissions
RUN chown -R dmlog:dmlog /app
USER dmlog

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Startup script
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]