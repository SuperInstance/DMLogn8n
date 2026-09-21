# Multi-stage build for production optimization
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY source_code/frontend/package*.json ./source_code/frontend/

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY source_code/ ./source_code/
COPY config/ ./config/

# Build frontend
WORKDIR /app/source_code/frontend
RUN npm run build

# Production stage
FROM node:18-alpine AS production

# Install security updates
RUN apk update && apk upgrade && \
    apk add --no-cache curl dumb-init && \
    rm -rf /var/cache/apk/*

# Create non-root user
RUN addgroup -g 1001 -S dmlogn8n && \
    adduser -S dmlogn8n -u 1001

WORKDIR /app

# Copy built frontend
COPY --from=builder --chown=dmlogn8n:dmlogn8n /app/source_code/frontend/dist ./public

# Copy backend application
COPY --chown=dmlogn8n:dmlogn8n source_code/backend/ ./backend/
COPY --chown=dmlogn8n:dmlogn8n config/ ./config/

# Install backend dependencies
WORKDIR /app/backend
RUN npm ci --only=production && \
    npm cache clean --force

# Switch to non-root user
USER dmlogn8n

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Use dumb-init as PID 1
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "server.js"]