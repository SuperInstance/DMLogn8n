#!/bin/bash

# =============================================================================
# GLM-4.6 Local Setup Script
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔐 GLM-4.6 Local Setup${NC}"
echo -e "${BLUE}========================${NC}"

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
    echo -e "${YELLOW}Creating .env.local file...${NC}"
    cat > .env.local << EOL
# GLM-4.6 Configuration
GLM4_API_KEY=your_actual_glm4_api_key_here
GLM4_ENDPOINT=https://open.bigmodel.cn/api/paas/v4/chat/completions
GLM4_MODEL=glm-4

# Optional: Other AI Model Keys
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Database Configuration
POSTGRES_PASSWORD=your_postgres_password
REDIS_PASSWORD=your_redis_password

# System Configuration
LOG_LEVEL=INFO
ENVIRONMENT=development
EOL
    echo -e "${GREEN}✓ Created .env.local${NC}"
    echo -e "${YELLOW}⚠️  Please edit .env.local and add your actual API keys${NC}"
    echo -e "${BLUE}nano .env.local${NC}"
    echo ""
    read -p "Press Enter after adding your API keys..."
else
    echo -e "${GREEN}✓ .env.local already exists${NC}"
fi

# Load environment variables
if [ -f ".env.local" ]; then
    export $(cat .env.local | grep -v '^#' | xargs)
    echo -e "${GREEN}✓ Loaded environment variables${NC}"
fi

# Check if GLM4 API key is set
if [ "$GLM4_API_KEY" = "your_actual_glm4_api_key_here" ] || [ -z "$GLM4_API_KEY" ]; then
    echo -e "${RED}❌ Please set your actual GLM4 API key in .env.local${NC}"
    exit 1
fi

echo -e "${BLUE}🚀 Starting GLM-4.6 Services...${NC}"

# Function to start service in background
start_service() {
    local service_name=$1
    local command=$2
    local log_file="logs/${service_name}.log"

    echo -e "${BLUE}Starting $service_name...${NC}"
    mkdir -p logs

    # Start service in background
    ($command 2>&1 | tee "$log_file") &
    local pid=$!

    echo "$pid" > "logs/${service_name}.pid"
    echo -e "${GREEN}✓ $service_name started (PID: $pid)${NC}"
    echo -e "${BLUE}  Log file: $log_file${NC}"
}

# Start services
echo -e "\n${BLUE}Phase 1: Starting AI Services${NC}"

# Start AI Model Pools
start_service "ai-model-pools" "python multi-portal-gateway/services/ai_model_pools.py"

# Wait a moment
sleep 2

# Start Coder Bot
start_service "coder-bot" "python multi-portal-gateway/services/coder_bot.py"

# Wait a moment
sleep 2

# Start AI Transparency Service
start_service "ai-transparency" "python multi-portal-gateway/services/ai_transparency.py"

# Wait a moment
sleep 2

echo -e "\n${BLUE}Phase 2: Starting Core Services${NC}"

# Start Memory System
start_service "memory-system" "python multi-portal-gateway/services/memory_system.py"

# Wait a moment
sleep 2

# Start Living World
start_service "living-world" "python multi-portal-gateway/services/living_world.py"

# Wait a moment
sleep 2

echo -e "\n${BLUE}Phase 3: Starting Gateway${NC}"

# Start Enhanced Gateway
start_service "enhanced-gateway" "python multi-portal-gateway/gateway/main.py"

# Wait for services to be ready
echo -e "\n${YELLOW}Waiting for services to be ready...${NC}"
sleep 5

# Check services
echo -e "\n${BLUE}🔍 Service Status:${NC}"

# Check if ports are responding
services_to_check=(
    "7900:Coder Bot"
    "8001:Enhanced Gateway"
)

for service in "${services_to_check[@]}"; do
    port=$(echo $service | cut -d: -f1)
    name=$(echo $service | cut -d: -f2)

    if nc -z localhost $port 2>/dev/null; then
        echo -e "${GREEN}✓ $name is responding on port $port${NC}"
    else
        echo -e "${RED}❌ $name is not responding on port $port${NC}"
    fi
done

echo -e "\n${GREEN}🎉 GLM-4.6 Services Started Successfully!${NC}"
echo -e "\n${BLUE}📋 Access Points:${NC}"
echo -e "  ${GREEN}Gateway API${NC}: http://localhost:8001/docs"
echo -e "  ${GREEN}Coder Bot${NC}: http://localhost:7900"
echo -e "  ${GREEN}WebSocket${NC}: ws://localhost:8001/ws/characters/[id]"
echo -e "\n${BLUE}📚 Logs:${NC}"
echo -e "  All logs are in the 'logs/' directory"
echo -e "  ${YELLOW}tail -f logs/enhanced-gateway.log${NC} to see main logs"
echo -e "\n${BLUE}🛑 To Stop Services:${NC}"
echo -e "  ${YELLOW}./stop_glm4_services.sh${NC}"
echo -e "\n${BLUE}🧪 To Test:${NC}"
echo -e "  ${YELLOW}curl http://localhost:7900/health${NC}"
echo -e "  ${YELLOW}curl http://localhost:8001/health${NC}"

# Create stop script
cat > stop_glm4_services.sh << 'EOS'
#!/bin/bash
echo "🛑 Stopping GLM-4.6 Services..."
cd "$(dirname "$0")"

# Kill all services by PID
for pid_file in logs/*.pid; do
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "Stopping service with PID $pid..."
            kill "$pid"
        fi
        rm -f "$pid_file"
    fi
done

# Kill any remaining Python processes from this project
pkill -f "multi-portal-gateway"

echo "✅ All services stopped"
EOS

chmod +x stop_glm4_services.sh
echo -e "\n${GREEN}✓ Created stop_glm4_services.sh${NC}"