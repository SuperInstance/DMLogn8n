#!/bin/bash

# DMLogn8n Quick Deployment Script
# One-command deployment for the entire platform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="development"
SKIP_BACKUP=false
SKIP_HEALTH_CHECK=false
SKIP_MONITORING=false
DRY_RUN=false
VERBOSE=false

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

# Function to show usage
usage() {
    cat << EOF
DMLogn8n Quick Deployment Script

Usage: $0 [OPTIONS]

OPTIONS:
    -e, --environment ENV    Target environment (development|staging|production) [default: development]
    -b, --skip-backup        Skip backup creation
    -h, --skip-health        Skip health checks
    -m, --skip-monitoring    Skip monitoring setup
    -d, --dry-run            Show what would be deployed without executing
    -v, --verbose            Enable verbose output
    --rollback ROLLBACK_ID   Rollback to specific deployment
    --status                 Show deployment status
    --help                   Show this help message

EXAMPLES:
    # Deploy to development environment
    $0 -e development

    # Deploy to production without backup
    $0 -e production --skip-backup

    # Rollback to previous deployment
    $0 --rollback deploy_1234567890

    # Check deployment status
    $0 --status

    # Dry run to see what would be deployed
    $0 -e production --dry-run

EOF
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."

    # Check if running as root
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root for security reasons"
        exit 1
    fi

    # Check if Python 3 is installed
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is required but not installed"
        exit 1
    fi

    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is required but not installed"
        exit 1
    fi

    # Check if we're in the right directory
    if [[ ! -f "deployment_manager.py" ]]; then
        print_error "Please run this script from the DMLogn8n/deploy directory"
        exit 1
    fi

    print_success "Prerequisites check passed"
}

# Function to load environment variables
load_env() {
    local env_file="docker/.env.${ENVIRONMENT}"

    if [[ -f "$env_file" ]]; then
        print_status "Loading environment variables from $env_file"
        set -a
        source "$env_file"
        set +a
    else
        print_warning "Environment file $env_file not found, using defaults"
    fi
}

# Function to create backup
create_backup() {
    if [[ "$SKIP_BACKUP" == true ]]; then
        print_warning "Skipping backup creation"
        return
    fi

    print_status "Creating backup..."

    backup_dir="/var/backups/dmlogn8n/deploy_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"

    # Backup current configurations
    if [[ -d "/etc/dmlogn8n" ]]; then
        cp -r /etc/dmlogn8n "$backup_dir/"
        print_success "Configurations backed up"
    fi

    # Backup databases
    if docker ps | grep -q "dmlogn8n-mysql"; then
        docker exec dmlogn8n-mysql mysqldump --single-transaction -u root -p"$MYSQL_ROOT_PASSWORD" dmlogn8n > "$backup_dir/dmlogn8n.sql" 2>/dev/null || print_warning "MySQL backup failed"
        docker exec dmlogn8n-mysql mysqldump --single-transaction -u root -p"$MYSQL_ROOT_PASSWORD" n8n > "$backup_dir/n8n.sql" 2>/dev/null || print_warning "N8N database backup failed"
        print_success "Databases backed up"
    fi

    print_success "Backup created at $backup_dir"
}

# Function to run deployment
run_deployment() {
    print_status "Starting deployment to $ENVIRONMENT environment..."

    local deploy_args=(
        "$ENVIRONMENT"
        "--version" "latest"
    )

    if [[ "$SKIP_BACKUP" == true ]]; then
        deploy_args+=("--no-backup")
    fi

    if [[ "$SKIP_HEALTH_CHECK" == true ]]; then
        deploy_args+=("--no-health-check")
    fi

    if [[ "$SKIP_MONITORING" == true ]]; then
        deploy_args+=("--no-monitoring")
    fi

    if [[ "$VERBOSE" == true ]]; then
        deploy_args+=("--verbose")
    fi

    if [[ "$DRY_RUN" == true ]]; then
        print_status "DRY RUN: Would execute: python3 deployment_manager.py ${deploy_args[*]}"
        return 0
    fi

    # Run the deployment
    if python3 deployment_manager.py "${deploy_args[@]}"; then
        print_success "Deployment completed successfully!"
        return 0
    else
        print_error "Deployment failed!"
        return 1
    fi
}

# Function to run rollback
run_rollback() {
    local rollback_id="$1"
    print_status "Rolling back to deployment: $rollback_id"

    if python3 rollback_manager.py "$ENVIRONMENT" --action rollback --deployment-id "$rollback_id"; then
        print_success "Rollback completed successfully!"
        return 0
    else
        print_error "Rollback failed!"
        return 1
    fi
}

# Function to show status
show_status() {
    print_status "Deployment status for $ENVIRONMENT environment:"

    # Check Docker containers
    print_status "Docker containers:"
    docker-compose -f docker/docker-compose.yml ps

    # Check health status
    if [[ -f "health_check_deploy.py" ]]; then
        print_status "Health checks:"
        python3 health_check_deploy.py "$ENVIRONMENT"
    fi

    # Show recent logs
    print_status "Recent deployment logs:"
    if [[ -f "/var/log/dmlogn8n/deployments" ]]; then
        ls -la /var/log/dmlogn8n/deployments/ | tail -5
    fi
}

# Function to cleanup on exit
cleanup() {
    if [[ $? -ne 0 ]]; then
        print_error "Deployment failed. Check logs for details."
    fi
}

# Set up cleanup trap
trap cleanup EXIT

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -b|--skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        -h|--skip-health)
            SKIP_HEALTH_CHECK=true
            shift
            ;;
        -m|--skip-monitoring)
            SKIP_MONITORING=true
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --rollback)
            ROLLBACK_ID="$2"
            shift 2
            ;;
        --status)
            SHOW_STATUS=true
            shift
            ;;
        --help)
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

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    print_error "Invalid environment: $ENVIRONMENT"
    usage
    exit 1
fi

# Main execution
main() {
    print_status "DMLogn8n Quick Deployment Script"
    print_status "Environment: $ENVIRONMENT"

    if [[ "$VERBOSE" == true ]]; then
        set -x
    fi

    # Check prerequisites
    check_prerequisites

    # Load environment variables
    load_env

    # Handle different actions
    if [[ -n "$ROLLBACK_ID" ]]; then
        run_rollback "$ROLLBACK_ID"
    elif [[ "$SHOW_STATUS" == true ]]; then
        show_status
    else
        # Create backup if not skipped
        create_backup

        # Run deployment
        if run_deployment; then
            print_success "🎉 DMLogn8n deployment completed successfully!"
            print_status "Next steps:"
            print_status "1. Verify services are running: docker-compose -f docker/docker-compose.yml ps"
            print_status "2. Check health: python3 health_check_deploy.py $ENVIRONMENT"
            print_status "3. Access the application:"
            if [[ "$ENVIRONMENT" == "development" ]]; then
                print_status "   - Player Portal: http://localhost:3000"
                print_status "   - API: http://localhost:8000"
                print_status "   - N8N: http://localhost:5678"
            else
                print_status "   - Player Portal: https://dmlogn8n.com"
                print_status "   - API: https://api.dmlogn8n.com"
                print_status "   - N8N: https://n8n.dmlogn8n.com"
            fi
        else
            print_error "Deployment failed. Check logs and try rollback if needed."
            exit 1
        fi
    fi
}

# Run main function
main "$@"