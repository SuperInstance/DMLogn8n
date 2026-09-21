#!/bin/bash

# DMlogn8n Voice System Deployment Script
# This script deploys the complete voice chat system with all components

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="dmlogn8n-voice"
COMPOSE_FILE="docker-compose.voice.yml"
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
LOG_DIR="./logs"

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."

    mkdir -p "$LOG_DIR"/{voice-chat,sfu,sound-effects,music,integration,nginx}
    mkdir -p "./config"/{nginx,prometheus,grafana,coturn,n8n}
    mkdir -p "./backups"
    mkdir -p "./data"/{redis,sounds,music,integration}

    # Set permissions
    chmod -R 755 "$LOG_DIR"
    chmod -R 755 "./config"
    chmod -R 755 "./data"

    print_success "Directories created successfully"
}

# Function to generate configuration files
generate_configurations() {
    print_status "Generating configuration files..."

    # Generate Redis configuration
    cat > ./config/redis.conf << EOF
# Redis Configuration for DMlogn8n Voice System
bind 0.0.0.0
port 6379
timeout 0
tcp-keepalive 300
daemonize no
supervised no
pidfile /var/run/redis_6379.pid
loglevel notice
logfile ""
databases 16

# Persistence
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /data

# Memory
maxmemory 256mb
maxmemory-policy allkeys-lru

# Security
# requirepass your-redis-password-here

# Performance
tcp-backlog 511
EOF

    # Generate Nginx configuration
    cat > ./config/nginx/nginx.conf << EOF
events {
    worker_connections 1024;
}

http {
    upstream voice-chat {
        server voice-chat-server:8001;
    }

    upstream voice-sfu {
        server voice-sfu-server:8002;
    }

    upstream sound-effects {
        server sound-effects-library:8003;
    }

    upstream dynamic-music {
        server dynamic-music-manager:8004;
    }

    upstream voice-integration {
        server voice-integration-layer:8005;
    }

    server {
        listen 80;
        server_name localhost;

        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }

        # Voice Chat API
        location /api/voice-chat/ {
            proxy_pass http://voice-chat/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        # SFU API
        location /api/voice-sfu/ {
            proxy_pass http://voice-sfu/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        # Sound Effects API
        location /api/sound-effects/ {
            proxy_pass http://sound-effects/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            client_max_body_size 100M;
        }

        # Dynamic Music API
        location /api/dynamic-music/ {
            proxy_pass http://dynamic-music/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        # Integration API
        location /api/voice-integration/ {
            proxy_pass http://voice-integration/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        # WebSocket connections
        location /ws/ {
            proxy_pass http://voice-chat;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
    }
}
EOF

    # Generate Coturn configuration
    cat > ./config/coturn/turnserver.conf << EOF
# Coturn Configuration for DMlogn8n Voice System
listening-port=3478
tls-listening-port=5349
listening-ip=0.0.0.0

# Authentication
use-auth-secret
static-auth-secret=your-static-auth-secret-here
realm=dmlogn8n

# WebRTC support
total-quota=100
user-quota=12
max-bps=64000

# Logging
log-file=/var/log/turnserver.log
verbose

# STUN/TURN
fingerprint
lt-cred-mech
stale-nonce
no-multicast-peers
no-loopback-peers
no-tcp-relay
no-tlsv1
no-tlsv1_1
EOF

    # Generate Prometheus configuration
    cat > ./config/prometheus/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'voice-chat-server'
    static_configs:
      - targets: ['voice-chat-server:8001']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'voice-sfu-server'
    static_configs:
      - targets: ['voice-sfu-server:8002']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'sound-effects-library'
    static_configs:
      - targets: ['sound-effects-library:8003']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'dynamic-music-manager'
    static_configs:
      - targets: ['dynamic-music-manager:8004']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'voice-integration-layer'
    static_configs:
      - targets: ['voice-integration-layer:8005']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 30s
EOF

    print_success "Configuration files generated"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."

    # Check Docker
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    # Check Docker Compose
    if ! command_exists docker-compose; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi

    print_success "Prerequisites check passed"
}

# Function to backup existing data
backup_data() {
    if [ -d "./data" ] && [ "$(ls -A ./data)" ]; then
        print_status "Backing up existing data..."
        mkdir -p "$BACKUP_DIR"
        cp -r ./data "$BACKUP_DIR/"
        print_success "Data backed up to $BACKUP_DIR"
    fi
}

# Function to build and start services
deploy_services() {
    print_status "Building and starting voice system services..."

    # Pull latest images
    docker-compose -f "$COMPOSE_FILE" pull

    # Build custom images
    docker-compose -f "$COMPOSE_FILE" build

    # Start services
    docker-compose -f "$COMPOSE_FILE" up -d

    print_success "Services deployed successfully"
}

# Function to wait for services to be healthy
wait_for_services() {
    print_status "Waiting for services to be healthy..."

    services=(
        "redis-voice:6379"
        "voice-chat-server:8001"
        "voice-sfu-server:8002"
        "sound-effects-library:8003"
        "dynamic-music-manager:8004"
        "voice-integration-layer:8005"
    )

    for service in "${services[@]}"; do
        service_name=$(echo "$service" | cut -d':' -f1)
        service_port=$(echo "$service" | cut -d':' -f2)

        print_status "Waiting for $service_name..."

        # Wait up to 60 seconds for service to be healthy
        for i in {1..60}; do
            if docker-compose -f "$COMPOSE_FILE" ps "$service_name" | grep -q "Up (healthy)"; then
                print_success "$service_name is healthy"
                break
            fi

            if [ $i -eq 60 ]; then
                print_warning "$service_name is not healthy after 60 seconds"
            fi

            sleep 1
        done
    done
}

# Function to run health checks
run_health_checks() {
    print_status "Running health checks..."

    # Check Voice Chat Server
    if curl -f http://localhost:8001/ >/dev/null 2>&1; then
        print_success "Voice Chat Server is responding"
    else
        print_error "Voice Chat Server is not responding"
    fi

    # Check SFU Server
    if curl -f http://localhost:8002/ >/dev/null 2>&1; then
        print_success "SFU Server is responding"
    else
        print_error "SFU Server is not responding"
    fi

    # Check Sound Effects Library
    if curl -f http://localhost:8003/ >/dev/null 2>&1; then
        print_success "Sound Effects Library is responding"
    else
        print_error "Sound Effects Library is not responding"
    fi

    # Check Dynamic Music Manager
    if curl -f http://localhost:8004/ >/dev/null 2>&1; then
        print_success "Dynamic Music Manager is responding"
    else
        print_error "Dynamic Music Manager is not responding"
    fi

    # Check Integration Layer
    if curl -f http://localhost:8005/ >/dev/null 2>&1; then
        print_success "Integration Layer is responding"
    else
        print_error "Integration Layer is not responding"
    fi
}

# Function to show deployment status
show_status() {
    print_status "Deployment Status:"
    echo ""
    docker-compose -f "$COMPOSE_FILE" ps
    echo ""

    print_status "Service URLs:"
    echo "Voice Chat API: http://localhost:8001"
    echo "SFU API: http://localhost:8002"
    echo "Sound Effects API: http://localhost:8003"
    echo "Dynamic Music API: http://localhost:8004"
    echo "Integration API: http://localhost:8005"
    echo "N8n Workflow Automation: http://localhost:5678"
    echo "Grafana Dashboard: http://localhost:3000"
    echo "Prometheus: http://localhost:9090"
    echo ""

    print_status "Default Credentials:"
    echo "N8n: admin / your-secure-n8n-password"
    echo "Grafana: admin / your-secure-grafana-password"
    echo ""
}

# Function to cleanup on failure
cleanup_on_failure() {
    print_error "Deployment failed. Cleaning up..."
    docker-compose -f "$COMPOSE_FILE" down
    exit 1
}

# Main deployment function
main() {
    echo "========================================"
    echo "DMlogn8n Voice System Deployment"
    echo "========================================"
    echo ""

    # Set up error handling
    trap cleanup_on_failure ERR

    # Run deployment steps
    check_prerequisites
    create_directories
    generate_configurations
    backup_data
    deploy_services
    wait_for_services
    run_health_checks
    show_status

    print_success "Voice system deployment completed successfully!"
    echo ""
    print_status "Next steps:"
    echo "1. Update default passwords in configuration files"
    echo "2. Configure SSL certificates for production"
    echo "3. Set up monitoring and alerting"
    echo "4. Import n8n workflows for automation"
    echo "5. Test voice chat functionality"
    echo ""
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "stop")
        print_status "Stopping voice system..."
        docker-compose -f "$COMPOSE_FILE" down
        print_success "Voice system stopped"
        ;;
    "restart")
        print_status "Restarting voice system..."
        docker-compose -f "$COMPOSE_FILE" restart
        wait_for_services
        run_health_checks
        print_success "Voice system restarted"
        ;;
    "logs")
        docker-compose -f "$COMPOSE_FILE" logs -f
        ;;
    "status")
        show_status
        ;;
    "health")
        run_health_checks
        ;;
    "cleanup")
        print_warning "This will remove all containers, networks, and volumes."
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker-compose -f "$COMPOSE_FILE" down -v
            docker system prune -f
            print_success "Cleanup completed"
        else
            print_status "Cleanup cancelled"
        fi
        ;;
    *)
        echo "Usage: $0 {deploy|stop|restart|logs|status|health|cleanup}"
        echo ""
        echo "Commands:"
        echo "  deploy   - Deploy the complete voice system"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  logs     - Show logs for all services"
        echo "  status   - Show deployment status"
        echo "  health   - Run health checks"
        echo "  cleanup  - Remove all containers and data"
        exit 1
        ;;
esac