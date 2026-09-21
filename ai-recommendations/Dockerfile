# Use Node.js 18 LTS as base image
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Create app directory
RUN mkdir -p /app

# Install system dependencies
RUN apk add --no-cache \
    python3 \
    make \
    g++ \
    && rm -rf /var/cache/apk/*

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S recommendations -u 1001

# Copy application code
COPY --chown=recommendations:nodejs . .

# Create logs directory
RUN mkdir -p /app/logs && chown recommendations:nodejs /app/logs

# Set permissions
RUN chown -R recommendations:nodejs /app

# Switch to non-root user
USER recommendations

# Expose port
EXPOSE 3001

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD node healthcheck.js

# Start the application
CMD ["npm", "start"]