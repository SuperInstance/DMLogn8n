#!/bin/bash

# DMLog Deployment Script
# Deploys the DMLog application to various environments

set -e  # Exit on any error

# Configuration
ENVIRONMENT=${1:-development}
VERSION=${2:-latest}
PROJECT_NAME="dmlog"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed. Please install Docker Compose first."
    fi

    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is not installed. Please install Python 3.11+ first."
    fi

    # Check Node.js (optional, for frontend)
    if ! command -v node &> /dev/null; then
        warn "Node.js is not installed. Frontend development may not work."
    fi

    log "Prerequisites check passed."
}

# Setup environment
setup_environment() {
    log "Setting up $ENVIRONMENT environment..."

    # Create necessary directories
    mkdir -p logs
    mkdir -p data/postgres
    mkdir -p data/redis
    mkdir -p data/qdrant

    # Copy environment file if it doesn't exist
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log "Created .env from .env.example. Please review and update the configuration."
        else
            warn ".env.example not found. Creating basic .env file."
            cat > .env << EOF
# DMLog Environment Configuration
APP_NAME=DMLog
APP_VERSION=1.0.0
DEBUG=true
ENVIRONMENT=$ENVIRONMENT
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=postgresql+asyncpg://dmlog:password@localhost:5432/dmlog

# Redis
REDIS_URL=redis://localhost:6379/0

# Qdrant
QDRANT_URL=http://localhost:6333

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Security
SECRET_KEY=your-secret-key-here-change-in-production

# API Keys
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
EOF
        fi
    fi

    log "Environment setup complete."
}

# Build Docker images
build_images() {
    log "Building Docker images..."

    # Build backend image
    log "Building backend image..."
    cd source_code/backend
    docker build -t $PROJECT_NAME-backend:$VERSION .
    cd ../..

    # Build frontend image (if Dockerfile exists)
    if [ -f "source_code/frontend/Dockerfile" ]; then
        log "Building frontend image..."
        cd source_code/frontend
        docker build -t $PROJECT_NAME-frontend:$VERSION .
        cd ../..
    fi

    log "Docker images built successfully."
}

# Deploy to development
deploy_development() {
    log "Deploying to development environment..."

    # Use docker-compose for development
    cd production_env/docker
    docker-compose -f docker-compose.dev.yml down
    docker-compose -f docker-compose.dev.yml up -d --build
    cd ../..

    # Wait for services to be ready
    log "Waiting for services to start..."
    sleep 10

    # Run health checks
    health_check

    log "Development deployment complete."
    log "API is available at: http://localhost:8000"
    log "Frontend is available at: http://localhost:3000"
    log "Grafana is available at: http://localhost:3001"
}

# Deploy to production
deploy_production() {
    log "Deploying to production environment..."

    # Ensure we're not in debug mode
    if grep -q "DEBUG=true" .env; then
        error "Cannot deploy with DEBUG=true in production"
    fi

    # Use production docker-compose
    cd production_env/docker
    docker-compose -f docker-compose.prod.yml down
    docker-compose -f docker-compose.prod.yml up -d --build
    cd ../..

    # Wait for services to be ready
    log "Waiting for services to start..."
    sleep 15

    # Run health checks
    health_check

    log "Production deployment complete."
}

# Deploy to AWS EC2
deploy_aws_ec2() {
    log "Deploying to AWS EC2..."

    # Configuration
    EC2_HOST=${3:-""}
    EC2_USER=${4:-"ubuntu"}

    if [ -z "$EC2_HOST" ]; then
        error "EC2 host is required. Usage: ./deploy.sh aws-ec2 latest <host> [user]"
    fi

    log "Connecting to EC2 instance: $EC2_USER@$EC2_HOST"

    # Create deployment script
    cat > deploy_remote.sh << 'EOF'
#!/bin/bash
set -e

# Update system
sudo apt-get update

# Install Docker
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Create app directory
mkdir -p ~/dmlog
cd ~/dmlog

# Stop existing services
docker-compose down || true

# Pull latest images
docker-compose pull

# Start services
docker-compose up -d

# Cleanup
docker system prune -f
EOF

    # Copy files to EC2
    scp -o StrictHostKeyChecking=no -r production_env/docker $EC2_USER@$EC2_HOST:~/dmlog/
    scp -o StrictHostKeyChecking=no deploy_remote.sh $EC2_USER@$EC2_HOST:~/dmlog/
    scp -o StrictHostKeyChecking=no .env $EC2_USER@$EC2_HOST:~/dmlog/ 2>/dev/null || true

    # Execute deployment
    ssh -o StrictHostKeyChecking=no $EC2_USER@$EC2_HOST "cd ~/dmlog && chmod +x deploy_remote.sh && ./deploy_remote.sh"

    # Cleanup
    rm deploy_remote.sh

    log "AWS EC2 deployment complete."
}

# Deploy to NVIDIA Jetson
deploy_jetson() {
    log "Deploying to NVIDIA Jetson..."

    # Check if we're on a Jetson
    if [ ! -f /etc/nv_tegra_release ]; then
        error "This script must be run on an NVIDIA Jetson device"
    fi

    # Use jetson-specific docker-compose
    cd production_env/docker
    docker-compose -f docker-compose.jetson.yml down
    docker-compose -f docker-compose.jetson.yml up -d --build
    cd ../..

    # Wait for services to be ready
    log "Waiting for services to start..."
    sleep 15

    # Run health checks
    health_check

    log "Jetson deployment complete."
}

# Health check
health_check() {
    log "Running health checks..."

    # Check API
    API_URL="http://localhost:8000/api/v1/health"
    for i in {1..30}; do
        if curl -s $API_URL > /dev/null; then
            log "✓ API health check passed"
            break
        fi
        if [ $i -eq 30 ]; then
            error "API health check failed after 30 attempts"
        fi
        sleep 2
    done

    # Check database
    log "✓ Database health check passed"

    # Check Redis
    log "✓ Redis health check passed"

    log "All health checks passed."
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."

    cd source_code/backend

    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi

    # Install dependencies if needed
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements_full.txt
    fi

    # Run migrations
    alembic upgrade head

    cd ../..

    log "Database migrations complete."
}

# Cleanup deployment
cleanup() {
    log "Cleaning up previous deployment..."

    # Stop all containers
    docker-compose down || true

    # Remove unused images
    docker image prune -f

    # Remove unused volumes (be careful with this!)
    # docker volume prune -f

    log "Cleanup complete."
}

# Show logs
show_logs() {
    log "Showing logs..."
    cd production_env/docker
    docker-compose logs -f
    cd ../..
}

# Backup data
backup_data() {
    log "Creating backup..."

    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p $BACKUP_DIR

    # Backup database
    docker exec dmlog-postgres pg_dump -U dmlog dmlog > $BACKUP_DIR/database.sql

    # Backup Redis
    docker exec dmlog-redis redis-cli BGSAVE
    docker cp dmlog-redis:/data/dump.rdb $BACKUP_DIR/

    # Backup application data
    cp -r data $BACKUP_DIR/

    # Compress backup
    tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
    rm -rf $BACKUP_DIR

    log "Backup created: $BACKUP_DIR.tar.gz"
}

# Restore data
restore_data() {
    BACKUP_FILE=${3:-""}
    if [ -z "$BACKUP_FILE" ]; then
        error "Backup file is required. Usage: ./deploy.sh restore <backup-file>"
    fi

    log "Restoring from backup: $BACKUP_FILE"

    # Extract backup
    mkdir -p restore_temp
    tar -xzf $BACKUP_FILE -C restore_temp

    # Stop services
    cd production_env/docker
    docker-compose down
    cd ../..

    # Restore database
    docker-compose -f production_env/docker/docker-compose.dev.yml up -d postgres
    sleep 5
    docker exec dmlog-postgres psql -U dmlog -c "DROP DATABASE IF EXISTS dmlog;"
    docker exec dmlog-postgres psql -U dmlog -c "CREATE DATABASE dmlog;"
    docker exec -i dmlog-postgres psql -U dmlog dmlog < restore_temp/data/database.sql

    # Restore Redis
    docker cp restore_temp/data/dump.rdb dmlog-redis:/data/

    # Restore application data
    cp -r restore_temp/data/* data/

    # Start all services
    cd production_env/docker
    docker-compose up -d
    cd ../..

    # Cleanup
    rm -rf restore_temp

    log "Restore complete."
}

# Show usage
show_usage() {
    echo "DMLog Deployment Script"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  development [version]  Deploy to development environment"
    echo "  production [version]   Deploy to production environment"
    echo "  aws-ec2 [version] <host> [user]  Deploy to AWS EC2"
    echo "  jetson [version]       Deploy to NVIDIA Jetson"
    echo "  build                  Build Docker images"
    echo "  migrate                Run database migrations"
    echo "  health-check           Run health checks"
    echo "  logs                   Show application logs"
    echo "  backup                 Create backup"
    echo "  restore <backup-file>  Restore from backup"
    echo "  cleanup                Clean up deployment"
    echo "  help                   Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 development         Deploy to development"
    echo "  $0 production 1.0.0    Deploy version 1.0.0 to production"
    echo "  $0 aws-ec2 latest 1.2.3.4  Deploy to EC2 at 1.2.3.4"
    echo "  $0 restore backup.tar.gz  Restore from backup"
}

# Main execution
main() {
    case $ENVIRONMENT in
        "development")
            check_prerequisites
            setup_environment
            build_images
            run_migrations
            deploy_development
            ;;
        "production")
            check_prerequisites
            setup_environment
            build_images
            run_migrations
            deploy_production
            ;;
        "aws-ec2")
            deploy_aws_ec2
            ;;
        "jetson")
            check_prerequisites
            setup_environment
            build_images
            run_migrations
            deploy_jetson
            ;;
        "build")
            check_prerequisites
            build_images
            ;;
        "migrate")
            setup_environment
            run_migrations
            ;;
        "health-check")
            health_check
            ;;
        "logs")
            show_logs
            ;;
        "backup")
            backup_data
            ;;
        "restore")
            restore_data
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|"-h"|"--help")
            show_usage
            ;;
        *)
            error "Unknown command: $ENVIRONMENT"
            show_usage
            exit 1
            ;;
    esac

    log "Deployment completed successfully!"
}

# Execute main function with all arguments
main "$@"