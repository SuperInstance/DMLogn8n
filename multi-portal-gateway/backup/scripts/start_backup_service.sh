#!/bin/bash

# DMLogn8n Backup Service Startup Script
# This script starts the backup service with proper configuration and monitoring

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$BACKUP_DIR/config/backup_config.yaml"
LOG_FILE="$BACKUP_DIR/logs/backup_service.log"
PID_FILE="$BACKUP_DIR/backup_service.pid"
VENV_PATH="$BACKUP_DIR/venv"

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

# Function to check if service is already running
is_service_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi

    # Check configuration file
    if [ ! -f "$CONFIG_FILE" ]; then
        print_error "Configuration file not found: $CONFIG_FILE"
        exit 1
    fi

    # Check required directories
    mkdir -p "$BACKUP_DIR/logs"
    mkdir -p "$BACKUP_DIR/storage/local"
    mkdir -p "$BACKUP_DIR/temp"

    # Check database connectivity (basic check)
    if command -v psql &> /dev/null; then
        if ! PGPASSWORD=${POSTGRES_PASSWORD:-} psql -h localhost -U postgres -d postgres -c "SELECT 1;" &> /dev/null; then
            print_warning "PostgreSQL connection failed - please check database configuration"
        fi
    fi

    # Check Redis connectivity (basic check)
    if command -v redis-cli &> /dev/null; then
        if ! redis-cli ping &> /dev/null; then
            print_warning "Redis connection failed - please check Redis configuration"
        fi
    fi

    print_success "Prerequisites check completed"
}

# Function to activate virtual environment
activate_venv() {
    if [ -d "$VENV_PATH" ]; then
        print_status "Activating virtual environment..."
        source "$VENV_PATH/bin/activate"
    else
        print_warning "Virtual environment not found, using system Python"
    fi

    # Check if required packages are installed
    python -c "import yaml, psycopg2, redis, boto3, google.cloud.storage" 2>/dev/null || {
        print_error "Required Python packages are not installed"
        print_status "Installing requirements..."
        pip install -r "$BACKUP_DIR/requirements.txt"
    }
}

# Function to start the service
start_service() {
    print_status "Starting DMLogn8n Backup Service..."

    # Set environment variables
    export PYTHONPATH="$BACKUP_DIR:$PYTHONPATH"
    export BACKUP_CONFIG_FILE="$CONFIG_FILE"
    export BACKUP_LOG_FILE="$LOG_FILE"

    # Start the service in background
    cd "$BACKUP_DIR"
    nohup python backup_service.py > "$LOG_FILE" 2>&1 &
    SERVICE_PID=$!

    # Save PID
    echo "$SERVICE_PID" > "$PID_FILE"

    # Wait a moment and check if service started successfully
    sleep 3

    if ps -p "$SERVICE_PID" > /dev/null 2>&1; then
        print_success "Backup service started successfully (PID: $SERVICE_PID)"
        print_status "Log file: $LOG_FILE"
        print_status "Configuration: $CONFIG_FILE"
        print_status "To stop the service: ./scripts/stop_backup_service.sh"
        print_status "To check status: ./scripts/status_backup_service.sh"
    else
        print_error "Failed to start backup service"
        rm -f "$PID_FILE"
        exit 1
    fi
}

# Function to show usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -c, --config FILE    Configuration file (default: $CONFIG_FILE)"
    echo "  -l, --log FILE      Log file (default: $LOG_FILE)"
    echo "  -d, --daemon        Run as daemon"
    echo "  -f, --foreground    Run in foreground"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Start with default settings"
    echo "  $0 -c /path/to/config.yaml          # Use custom config"
    echo "  $0 -f                                 # Run in foreground"
}

# Parse command line arguments
DAEMON_MODE=true
FOREGROUND_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -l|--log)
            LOG_FILE="$2"
            shift 2
            ;;
        -d|--daemon)
            DAEMON_MODE=true
            shift
            ;;
        -f|--foreground)
            FOREGROUND_MODE=true
            DAEMON_MODE=false
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    print_status "DMLogn8n Backup Service Startup"
    print_status "=================================="

    # Check if service is already running
    if is_service_running; then
        print_warning "Backup service is already running (PID: $(cat $PID_FILE))"
        print_status "To restart the service, run: ./scripts/restart_backup_service.sh"
        exit 1
    fi

    # Check prerequisites
    check_prerequisites

    # Activate virtual environment
    activate_venv

    # Start service
    if [ "$FOREGROUND_MODE" = true ]; then
        print_status "Starting backup service in foreground..."
        export PYTHONPATH="$BACKUP_DIR:$PYTHONPATH"
        export BACKUP_CONFIG_FILE="$CONFIG_FILE"
        export BACKUP_LOG_FILE="$LOG_FILE"
        cd "$BACKUP_DIR"
        python backup_service.py
    else
        start_service
    fi
}

# Handle signals for graceful shutdown
trap 'print_status "Received signal, shutting down gracefully..."; exit 0' SIGTERM SIGINT

# Run main function
main