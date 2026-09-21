#!/bin/bash

# =============================================================================
# Enhanced Multi-Portal D&D System Deployment Script
# =============================================================================

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
ENV_FILE=".env.enhanced"
COMPOSE_FILE="docker-compose.enhanced.yml"
PROJECT_NAME="DMLogn8n Enhanced"
LOG_FILE="./logs/deploy-enhanced-$(date +%Y%m%d_%H%M%S).log"

# =============================================================================
echo -e "${BLUE}🚀 Starting deployment of ${PROJECT_NAME}${NC}"
echo -e "${BLUE}===========================================${NC}"

# Create logs directory
mkdir -p logs

# Function to log messages
log() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] ${GREEN}INFO${NC}: $1" | tee -a "$LOG_FILE"
}

# Function to check if service is ready
check_service() {
    local service_name=$1
    local port=$2
    local max_attempts=${3:-30}
    local attempt=1

    echo -e "${BLUE}🔍 Checking $service_name on port $port...${NC}"

    while [ $attempt -le $max_attempts ]; do
        if nc -z localhost $port 2>/dev/null; then
            echo -e "${GREEN}✓ $service_name is ready on port $port${NC}"
            return 0
        else
            echo -e "${YELLOW}⏳ Attempt $attempt/$max_attempts for $service_name...${NC}"
            sleep 2
            ((attempt++))
    done

    echo -e "${RED}❌ $service_name failed to start after $max_attempts attempts${NC}"
    return 1
}

# Function to deploy a service
deploy_service() {
    local service_name=$1
    local compose_file=$2

    echo -e "${BLUE}📦 Deploying $service_name...${NC}"

    if docker-compose -f "$compose_file" up -d; then
        echo -e "${GREEN}✓ $service_name deployed successfully${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to deploy $service_name${NC}"
        docker-compose -f "$compose_file" logs 2>&1 | tee -a "$LOG_FILE"
        return 1
}

# Check environment
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}⚠️  Environment file not found: $ENV_FILE${NC}"
    echo -e "${BLUE}Creating from template...${NC}"

    # Copy template if it exists
    if [ -f ".env.template" ]; then
        cp .env.template "$ENV_FILE"
    fi

    # Prompt for API keys
    echo -e "${YELLOW}⚠️  Please add your API keys to $ENV_FILE${NC}"
    echo -e "${BLUE}Required variables:${NC}"
    echo -e "  - GLM4_API_KEY (for GLM-4.6 coder bot)"
    echo -e "  - OPENAI_API_KEY (optional, for advanced features)"
    echo -e "  - ANTHROPIC_API_KEY (optional, for Claude integration)"
    echo -e "  - POSTGRES_PASSWORD (database)"
    echo -e "  - REDIS_PASSWORD (caching)"
    echo -e "  - NEO4J_AUTH (knowledge graph)"
    echo -e "  - QDRANT_API_KEY (vector database)"

    read -p "Press Enter to continue after adding API keys..."

    # Check if critical keys are set
    source "$ENV_FILE" 2>/dev/null
    if [ -z "$GLM4_API_KEY" ] || [ -z "$POSTGRES_PASSWORD" ]; then
        echo -e "${RED}❌ Critical API keys missing in $ENV_FILE${NC}"
        echo -e "${BLUE}Please edit the file and add the required keys.${NC}"
        exit 1
    fi
fi

# Main deployment
main() {
    log "Starting deployment of $PROJECT_NAME"

    # Load environment variables
    source "$ENV_FILE"

    # Display configuration
    echo -e "${BLUE}📋 Configuration Summary:${NC}"
    echo -e "  Gateway WebSocket: 8001"
    echo -e "  Character Ports: 9000-9500"
    echo -e "  DM Port: 9501"
    echo -e "  Coder Bot: 7900"
    echo -e "  AI Transparency: 3001 (WebSocket)"
    echo -e "  Player Dashboard: 3000"

    # Check prerequisites
    log "Checking prerequisites..."

    # Check Docker
    if ! command -v docker >/dev/null; then
        echo -e "${RED}❌ Docker not installed${NC}"
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker-compose >/dev/null; then
        echo -e "${RED}❌ Docker Compose not installed${NC}"
        exit 1
    fi

    # Check available ports
    log "Checking port availability..."
    ports_in_use=$(lsof -i -P -n -sTCP:9000-9510 | wc -l)
    if [ "$ports_in_use" -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Ports 9000-9510 appear to be in use${NC}"
        echo -e "${BLUE}Currently in use by: $ports_in_use${NC}"
    fi

    # Deploy infrastructure services first
    log "Phase 1: Deploying infrastructure services..."

    services=(
        "postgres"
        "redis"
        "neo4j"
        "qdrant"
        "prometheus"
    )

    for service in "${services[@]}"; do
        log "Deploying $service..."
        if ! deploy_service "$service" "$COMPOSE_FILE"; then
            log "${RED}Failed to deploy $service${NC}"
            deployment_failed=true
            break
        fi
    done

    # Check if infrastructure deployment failed
    if [ "${deployment_failed:-false}" = true ]; then
        echo -e "${RED}❌ Infrastructure deployment failed. Check logs above.${NC}"
        exit 1
    fi

    # Wait for infrastructure to be ready
    log "Waiting for infrastructure services to be ready..."

    infra_services=(
        "postgres:5432"
        "redis:6379"
        "neo4j:7474"
        "qdrant:6333"
    )

    infra_ready=true
    for service_port in "${infra_services[@]}"; do
        service=$(echo $service_port | cut -d: -f1)
        port=$(echo $service_port | cut -d: -f2)

        check_service "$service" "$port"
        if [ $? -ne 0 ]; then
            infra_ready=false
        fi
    done

    if [ "$infra_ready" = false ]; then
        echo -e "${RED}❌ Infrastructure services not ready${NC}"
        exit 1
    fi

    # Deploy application services
    log "Phase 2: Deploying application services..."

    app_services=(
        "enhanced-gateway:8001"
        "ai-transparency:3001"
        "player-dashboard:3000"
    )

    for service_port in "${app_services[@]}"; do
        service=$(echo $service_port | cut -d: -f1)
        port=$(echo $service_port | cut -d: -f2)

        log "Deploying $service on port $port..."
        if ! deploy_service "$service" "$COMPOSE_FILE"; then
            log "${RED}Failed to deploy $service${NC}"
            app_deployment_failed=true
            break
        fi
    done

    # Check if application deployment failed
    if [ "${app_deployment_failed:-false}" = true ]; then
        echo -e "${RED}❌ Application deployment failed. Check logs above.${NC}"
        exit 1
    fi

    # Final verification
    log "Phase 3: Verifying deployment..."

    # Check all critical services
    critical_services=(
        "postgres:5432"
        "redis:6379"
        "neo4j:7474"
        "qdrant:6333"
        "enhanced-gateway:8001"
    )

    all_ready=true
    for service_port in "${critical_services[@]}"; do
        service=$(echo $service_port | cut -d: -f1)
        port=$(echo $service_port | cut -d: -f2)

        check_service "$service" "$port"
        if [ $? -ne 0 ]; then
            all_ready=false
        fi
    done

    if [ "$all_ready" = true ]; then
        echo -e "${GREEN}✅ Enhanced Multi-Portal D&D System deployed successfully!${NC}"
        echo -e "${BLUE}🎮 Access Points:${NC}"
        echo -e "  ${GREEN}Gateway API${NC}: http://localhost:8001/docs"
        echo -e "  ${GREEN}AI Transparency${NC}: http://localhost:3001"
        echo -e "  ${GREEN}Player Dashboard${NC}: http://localhost:3000"
        echo -e "  ${GREEN}Character Portals${NC}: ws://localhost:8001/ws/characters/[ID]"
        echo -e "  ${GREEN}DM Portal${NC}: ws://localhost:8001/ws/dm/"
        echo -e "  ${GREEN}Monitoring${NC}: http://localhost:9090 (Prometheus)"
        echo -e "  ${GREEN}Metrics${NC}: http://localhost:3002 (Grafana)"
        echo -e ""
        echo -e "${BLUE}📚 Logs are being written to: $LOG_FILE${NC}"
        echo -e "${YELLOW}💡 To create character portals:${NC}"
        echo -e "  curl -X POST http://localhost:8001/api/v1/characters/create \\"
        echo -e "    -H 'Content-Type: application/json' \\"
        echo -e "    -d '{\"character_id\": \"my_character\", \"name\": \"Aragorn\"}'"
        echo -e ""
        echo -e "${YELLOW}💡 To observe AI thoughts:${NC}"
        echo -e "  Connect to ws://localhost:3001/ws/ai-thoughts/[character_id]"
        echo -e ""
        echo -e "${BLUE}🎯 Ready for your automated D&D adventure!${NC}"
    else
        echo -e "${RED}❌ Deployment verification failed${NC}"
        exit 1
    fi
}

# Run main function
main "$@"