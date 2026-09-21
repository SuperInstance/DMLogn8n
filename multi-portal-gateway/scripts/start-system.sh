#!/bin/bash

# Multi-Portal Gateway System Startup Script
# This script starts all components of the DMlogn8n Multi-Portal Gateway System

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    print_success "Docker is running"
}

# Check if docker-compose is available
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose is not installed. Please install docker-compose first."
        exit 1
    fi
    print_success "docker-compose is available"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."

    mkdir -p logs
    mkdir -p config/ssl
    mkdir -p tmp/scripts
    mkdir -p data/postgres
    mkdir -p data/redis
    mkdir -p data/ollama
    mkdir -p data/n8n
    mkdir -p data/prometheus
    mkdir -p data/grafana

    # Set proper permissions
    chmod 755 logs tmp scripts data
    chmod 755 config

    print_success "Directories created"
}

# Build Docker images
build_images() {
    print_status "Building Docker images..."

    # Build main services
    docker-compose build gateway dm-portal coder-portal frontend

    print_success "Docker images built"
}

# Start the database services first
start_databases() {
    print_status "Starting database services..."

    docker-compose up -d postgres redis

    # Wait for databases to be ready
    print_status "Waiting for databases to be ready..."
    sleep 10

    # Check if PostgreSQL is ready
    until docker-compose exec -T postgres pg_isready -U dmlogn8n; do
        print_status "Waiting for PostgreSQL..."
        sleep 2
    done

    print_success "Databases are ready"
}

# Start AI service
start_ai_service() {
    print_status "Starting AI service..."

    docker-compose up -d ollama

    # Wait for Ollama to be ready
    print_status "Waiting for Ollama to be ready..."
    sleep 15

    # Pull models
    print_status "Pulling AI models..."
    docker-compose exec -T ollama ollama pull llama2 || true
    docker-compose exec -T ollama ollama pull codellama || true

    print_success "AI service is ready"
}

# Start core services
start_core_services() {
    print_status "Starting core services..."

    docker-compose up -d gateway

    # Wait for gateway to be ready
    print_status "Waiting for gateway to be ready..."
    sleep 10

    # Check gateway health
    until curl -f http://localhost:8000/health > /dev/null 2>&1; do
        print_status "Waiting for gateway..."
        sleep 2
    done

    print_success "Core services are ready"
}

# Start portal services
start_portal_services() {
    print_status "Starting portal services..."

    docker-compose up -d dm-portal coder-portal

    # Wait for portals to be ready
    sleep 10

    # Check portal health
    curl -f http://localhost:9501/health > /dev/null 2>&1 && print_success "DM Portal is ready" || print_warning "DM Portal might not be ready yet"
    curl -f http://localhost:9502/health > /dev/null 2>&1 && print_success "Coder Portal is ready" || print_warning "Coder Portal might not be ready yet"

    print_success "Portal services started"
}

# Start frontend and additional services
start_additional_services() {
    print_status "Starting additional services..."

    docker-compose up -d frontend n8n nginx prometheus grafana

    sleep 10

    print_success "Additional services started"
}

# Run system checks
run_system_checks() {
    print_status "Running system checks..."

    # Check if all services are running
    services=("gateway" "postgres" "redis" "ollama" "dm-portal" "coder-portal" "frontend" "n8n" "nginx")

    for service in "${services[@]}"; do
        if docker-compose ps | grep -q "${service}.*Up"; then
            print_success "$service is running"
        else
            print_warning "$service might not be running properly"
        fi
    done

    # Test API endpoints
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Gateway API is responding"
    else
        print_error "Gateway API is not responding"
    fi

    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        print_success "Frontend is responding"
    else
        print_warning "Frontend might not be ready yet"
    fi
}

# Display access information
show_access_info() {
    print_success "Multi-Portal Gateway System is now running!"
    echo ""
    echo "Access URLs:"
    echo "  Frontend:        http://localhost:3000"
    echo "  Gateway API:     http://localhost:8000"
    echo "  API Docs:        http://localhost:8000/docs"
    echo "  DM Portal:       http://localhost:9501"
    echo "  Coder Workshop:  http://localhost:9502"
    echo "  N8N Workflows:   http://localhost:5678 (admin/password)"
    echo "  Prometheus:      http://localhost:9090"
    echo "  Grafana:         http://localhost:3001 (admin/admin)"
    echo "  Nginx Proxy:     http://localhost:80"
    echo ""
    echo "Health Check:     curl http://localhost:8000/health"
    echo ""
    echo "To view logs:     docker-compose logs -f [service_name]"
    echo "To stop system:   ./scripts/stop-system.sh"
    echo "To restart:       ./scripts/restart-system.sh"
}

# Main execution
main() {
    echo "Starting Multi-Portal Gateway System..."
    echo "======================================"
    echo ""

    check_docker
    check_docker_compose
    create_directories

    if [ "$1" = "--build" ] || [ "$1" = "-b" ]; then
        build_images
    fi

    start_databases
    start_ai_service
    start_core_services
    start_portal_services
    start_additional_services
    run_system_checks
    show_access_info

    print_success "System startup completed!"
}

# Handle script arguments
case "$1" in
    --help|-h)
        echo "Usage: $0 [--build|-b] [--help|-h]"
        echo "  --build, -b: Build Docker images before starting"
        echo "  --help, -h:  Show this help message"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac