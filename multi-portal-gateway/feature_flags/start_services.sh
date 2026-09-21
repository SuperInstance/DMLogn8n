#!/bin/bash

# DMLogn8n Feature Flag System Startup Script
# This script starts all services for the feature flag system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
FEATURE_FLAG_PORT=8001
DASHBOARD_PORT=8002
METRICS_PORT=8000
REDIS_URL="redis://localhost:6379"
LOG_LEVEL="INFO"

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

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Function to wait for a service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1

    print_status "Waiting for $service_name to be ready..."

    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null; then
            print_success "$service_name is ready!"
            return 0
        fi

        echo -n "."
        sleep 2
        ((attempt++))
    done

    print_error "$service_name failed to start within expected time"
    return 1
}

# Function to check Redis connection
check_redis() {
    print_status "Checking Redis connection..."

    if command -v redis-cli &> /dev/null; then
        if redis-cli -u "$REDIS_URL" ping > /dev/null 2>&1; then
            print_success "Redis connection successful"
            return 0
        else
            print_error "Cannot connect to Redis at $REDIS_URL"
            return 1
        fi
    else
        print_warning "redis-cli not found, assuming Redis is available"
        return 0
    fi
}

# Function to start Redis (if not running)
start_redis() {
    if ! check_redis; then
        print_status "Starting Redis server..."

        if command -v redis-server &> /dev/null; then
            redis-server --daemonize yes --port 6379
            sleep 2

            if check_redis; then
                print_success "Redis started successfully"
            else
                print_error "Failed to start Redis"
                return 1
            fi
        else
            print_error "Redis server not found. Please install Redis or start it manually."
            print_status "You can install Redis with: sudo apt-get install redis-server"
            print_status "Or use Docker: docker run -d -p 6379:6379 redis:latest"
            return 1
        fi
    fi
}

# Function to install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."

    if [ -f "requirements.txt" ]; then
        python3 -m pip install -r requirements.txt
        print_success "Dependencies installed"
    else
        print_error "requirements.txt not found"
        return 1
    fi
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."

    mkdir -p logs
    mkdir -p templates
    mkdir -p static
    mkdir -p data

    print_success "Directories created"
}

# Function to start Feature Flag Service
start_feature_flag_service() {
    print_status "Starting Feature Flag Service on port $FEATURE_FLAG_PORT..."

    # Check if port is already in use
    if check_port $FEATURE_FLAG_PORT; then
        print_warning "Port $FEATURE_FLAG_PORT is already in use"
        print_status "Attempting to stop existing service..."
        pkill -f "feature_flag_service.py" || true
        sleep 2
    fi

    # Start the service
    python3 feature_flag_service.py > logs/feature_flag_service.log 2>&1 &
    FEATURE_FLAG_PID=$!

    echo $FEATURE_FLAG_PID > logs/feature_flag_service.pid

    # Wait for service to be ready
    if wait_for_service "http://localhost:$FEATURE_FLAG_PORT/health" "Feature Flag Service"; then
        print_success "Feature Flag Service started (PID: $FEATURE_FLAG_PID)"
        print_status "API Documentation: http://localhost:$FEATURE_FLAG_PORT/docs"
    else
        print_error "Feature Flag Service failed to start"
        return 1
    fi
}

# Function to start Dashboard
start_dashboard() {
    print_status "Starting Dashboard on port $DASHBOARD_PORT..."

    # Check if port is already in use
    if check_port $DASHBOARD_PORT; then
        print_warning "Port $DASHBOARD_PORT is already in use"
        print_status "Attempting to stop existing service..."
        pkill -f "dashboard.py" || true
        sleep 2
    fi

    # Start the dashboard
    python3 dashboard.py > logs/dashboard.log 2>&1 &
    DASHBOARD_PID=$!

    echo $DASHBOARD_PID > logs/dashboard.pid

    # Wait for dashboard to be ready
    if wait_for_service "http://localhost:$DASHBOARD_PORT" "Dashboard"; then
        print_success "Dashboard started (PID: $DASHBOARD_PID)"
        print_status "Dashboard URL: http://localhost:$DASHBOARD_PORT"
    else
        print_error "Dashboard failed to start"
        return 1
    fi
}

# Function to start Metrics Server
start_metrics_server() {
    print_status "Starting Metrics Server on port $METRICS_PORT..."

    # Check if port is already in use
    if check_port $METRICS_PORT; then
        print_warning "Port $METRICS_PORT is already in use"
        return 0
    fi

    # Start a simple metrics server
    python3 -c "
from prometheus_client import start_http_server, Counter, Gauge
import time

# Example metrics
REQUESTS_TOTAL = Counter('requests_total', 'Total requests', ['method', 'endpoint'])
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Active connections')

start_http_server($METRICS_PORT)
print('Metrics server started on port $METRICS_PORT')

# Keep the server running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print('Metrics server stopped')
" > logs/metrics_server.log 2>&1 &

    METRICS_PID=$!
    echo $METRICS_PID > logs/metrics_server.pid

    print_success "Metrics Server started (PID: $METRICS_PID)"
    print_status "Metrics URL: http://localhost:$METRICS_PORT/metrics"
}

# Function to stop all services
stop_services() {
    print_status "Stopping all services..."

    # Stop Feature Flag Service
    if [ -f "logs/feature_flag_service.pid" ]; then
        PID=$(cat logs/feature_flag_service.pid)
        if kill -0 $PID 2>/dev/null; then
            kill $PID
            print_success "Feature Flag Service stopped"
        fi
        rm -f logs/feature_flag_service.pid
    fi

    # Stop Dashboard
    if [ -f "logs/dashboard.pid" ]; then
        PID=$(cat logs/dashboard.pid)
        if kill -0 $PID 2>/dev/null; then
            kill $PID
            print_success "Dashboard stopped"
        fi
        rm -f logs/dashboard.pid
    fi

    # Stop Metrics Server
    if [ -f "logs/metrics_server.pid" ]; then
        PID=$(cat logs/metrics_server.pid)
        if kill -0 $PID 2>/dev/null; then
            kill $PID
            print_success "Metrics Server stopped"
        fi
        rm -f logs/metrics_server.pid
    fi

    # Kill any remaining processes
    pkill -f "feature_flag_service.py" || true
    pkill -f "dashboard.py" || true

    print_success "All services stopped"
}

# Function to check service status
check_status() {
    print_status "Checking service status..."

    # Check Feature Flag Service
    if check_port $FEATURE_FLAG_PORT; then
        print_success "Feature Flag Service: RUNNING (http://localhost:$FEATURE_FLAG_PORT)"
    else
        print_error "Feature Flag Service: STOPPED"
    fi

    # Check Dashboard
    if check_port $DASHBOARD_PORT; then
        print_success "Dashboard: RUNNING (http://localhost:$DASHBOARD_PORT)"
    else
        print_error "Dashboard: STOPPED"
    fi

    # Check Metrics Server
    if check_port $METRICS_PORT; then
        print_success "Metrics Server: RUNNING (http://localhost:$METRICS_PORT)"
    else
        print_warning "Metrics Server: STOPPED"
    fi

    # Check Redis
    if check_redis; then
        print_success "Redis: CONNECTED"
    else
        print_error "Redis: DISCONNECTED"
    fi
}

# Function to show logs
show_logs() {
    local service=$1

    case $service in
        "feature-flag")
            if [ -f "logs/feature_flag_service.log" ]; then
                tail -f logs/feature_flag_service.log
            else
                print_error "Feature Flag Service logs not found"
            fi
            ;;
        "dashboard")
            if [ -f "logs/dashboard.log" ]; then
                tail -f logs/dashboard.log
            else
                print_error "Dashboard logs not found"
            fi
            ;;
        "metrics")
            if [ -f "logs/metrics_server.log" ]; then
                tail -f logs/metrics_server.log
            else
                print_error "Metrics Server logs not found"
            fi
            ;;
        "all")
            print_status "Following all logs (Ctrl+C to exit)..."
            tail -f logs/*.log
            ;;
        *)
            print_error "Unknown service: $service"
            echo "Available services: feature-flag, dashboard, metrics, all"
            ;;
    esac
}

# Function to run tests
run_tests() {
    print_status "Running tests..."

    if [ -d "tests" ]; then
        python3 -m pytest tests/ -v
        print_success "Tests completed"
    else
        print_warning "No tests directory found"
    fi
}

# Function to show help
show_help() {
    echo "DMLogn8n Feature Flag System Control Script"
    echo ""
    echo "Usage: $0 {start|stop|restart|status|logs|test|help}"
    echo ""
    echo "Commands:"
    echo "  start     - Start all services"
    echo "  stop      - Stop all services"
    echo "  restart   - Restart all services"
    echo "  status    - Check service status"
    echo "  logs      - Show logs (service: feature-flag, dashboard, metrics, all)"
    echo "  test      - Run tests"
    echo "  help      - Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  FEATURE_FLAG_PORT  - Port for feature flag service (default: 8001)"
    echo "  DASHBOARD_PORT     - Port for dashboard (default: 8002)"
    echo "  METRICS_PORT       - Port for metrics (default: 8000)"
    echo "  REDIS_URL          - Redis connection URL (default: redis://localhost:6379)"
    echo "  LOG_LEVEL          - Logging level (default: INFO)"
}

# Main script logic
case "${1:-start}" in
    "start")
        print_status "Starting DMLogn8n Feature Flag System..."
        echo ""

        # Create directories
        create_directories

        # Install dependencies
        install_dependencies

        # Start Redis
        start_redis

        # Start services
        start_feature_flag_service
        start_dashboard
        start_metrics_server

        echo ""
        print_success "All services started successfully!"
        echo ""
        echo "🌐 Access URLs:"
        echo "  Feature Flag API: http://localhost:$FEATURE_FLAG_PORT"
        echo "  API Documentation: http://localhost:$FEATURE_FLAG_PORT/docs"
        echo "  Dashboard: http://localhost:$DASHBOARD_PORT"
        echo "  Metrics: http://localhost:$METRICS_PORT/metrics"
        echo ""
        echo "📊 Monitor logs with: $0 logs [service]"
        echo "🛑 Stop services with: $0 stop"
        ;;

    "stop")
        stop_services
        ;;

    "restart")
        stop_services
        sleep 2
        $0 start
        ;;

    "status")
        check_status
        ;;

    "logs")
        show_logs "${2:-all}"
        ;;

    "test")
        run_tests
        ;;

    "help"|"-h"|"--help")
        show_help
        ;;

    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac

exit 0