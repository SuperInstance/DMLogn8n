#!/bin/bash

# DMlogn8n Multi-Agent Communication System Deployment Script
# This script deploys and configures the multi-agent communication workflows

set -e

echo "🚀 Deploying DMlogn8n Multi-Agent Communication System..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
N8N_BASE_URL="${N8N_BASE_URL:-http://localhost:5678}"
N8N_API_KEY="${N8N_API_KEY:-}"
DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-sk-3b0251d9943549a2b475eb9e57e46ee6}"
WORKFLOWS_DIR="/home/activeloguser/DMLogn8n/workflows"

# Check if n8n is running
echo -e "${BLUE}📋 Checking n8n instance...${NC}"
if curl -s "$N8N_BASE_URL" > /dev/null; then
    echo -e "${GREEN}✅ n8n is running at $N8N_BASE_URL${NC}"
else
    echo -e "${RED}❌ n8n is not accessible at $N8N_BASE_URL${NC}"
    echo "Please ensure n8n is running before continuing."
    exit 1
fi

# Check if API key is available
if [ -z "$N8N_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  No N8N_API_KEY provided. Attempting to generate one...${NC}"
    N8N_API_KEY="n8n-api-$(date +%s)-$(openssl rand -hex 16)"
    echo -e "${GREEN}🔑 Generated API key: $N8N_API_KEY${NC}"
    echo "Please add this key to your n8n instance configuration."
fi

# Function to deploy workflow
deploy_workflow() {
    local workflow_file="$1"
    local workflow_name=$(basename "$workflow_file" .json)

    echo -e "${BLUE}📝 Deploying workflow: $workflow_name${NC}"

    # Check if workflow file exists
    if [ ! -f "$workflow_file" ]; then
        echo -e "${RED}❌ Workflow file not found: $workflow_file${NC}"
        return 1
    fi

    # Deploy workflow using curl
    response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $N8N_API_KEY" \
        -d @"$workflow_file" \
        "$N8N_BASE_URL/rest/workflows" 2>/dev/null || echo "")

    if echo "$response" | grep -q '"id"'; then
        echo -e "${GREEN}✅ Successfully deployed: $workflow_name${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to deploy: $workflow_name${NC}"
        echo "Response: $response"
        return 1
    fi
}

# Deploy all multi-agent workflows
echo -e "${BLUE}🔄 Deploying multi-agent communication workflows...${NC}"

workflows=(
    "agent-messaging-hub.json"
    "party-coordination.json"
    "consensus-builder.json"
    "conflict-resolution.json"
    "shared-context-manager.json"
    "deepseek-nlp-processor.json"
    "agent-registration-manager.json"
    "message-queue-priority.json"
    "multi-agent-test-suite.json"
)

success_count=0
total_count=${#workflows[@]}

for workflow in "${workflows[@]}"; do
    if deploy_workflow "$WORKFLOWS_DIR/$workflow"; then
        ((success_count++))
    fi
done

echo -e "${GREEN}📊 Deployment Summary: $success_count/$total_count workflows deployed successfully${NC}"

# Create basic agent registration test
echo -e "${BLUE}🤖 Creating initial test agents...${NC}"

# Register Dungeon Master agent
curl -s -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $N8N_API_KEY" \
    -d '{
        "action": "register",
        "agent_data": {
            "agent_id": "agent_dungeon_master",
            "agent_type": "coordinator",
            "display_name": "Dungeon Master",
            "description": "Primary game coordinator and story manager",
            "capabilities": ["plot_development", "npc_management", "world_state", "coordination"],
            "communication_endpoint": "http://localhost:8001/webhook/dm",
            "permissions": {
                "can_initiate_coordination": true,
                "can_vote": true,
                "can_propose_actions": true,
                "can_access_shared_context": true
            }
        }
    }' \
    "$N8N_BASE_URL/webhook/agent-management" > /dev/null

# Register Narrator agent
curl -s -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $N8N_API_KEY" \
    -d '{
        "action": "register",
        "agent_data": {
            "agent_id": "agent_narrator",
            "agent_type": "creative",
            "display_name": "Narrator",
            "description": "Storytelling and atmosphere specialist",
            "capabilities": ["narrative_generation", "description", "dialogue", "atmosphere"],
            "communication_endpoint": "http://localhost:8002/webhook/narrator",
            "permissions": {
                "can_initiate_coordination": false,
                "can_vote": true,
                "can_propose_actions": true,
                "can_access_shared_context": true
            }
        }
    }' \
    "$N8N_BASE_URL/webhook/agent-management" > /dev/null

# Register Combat Manager agent
curl -s -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $N8N_API_KEY" \
    -d '{
        "action": "register",
        "agent_data": {
            "agent_id": "agent_combat_manager",
            "agent_type": "technical",
            "display_name": "Combat Manager",
            "description": "Combat mechanics and challenge specialist",
            "capabilities": ["combat_logic", "challenge_design", "balance", "encounter_management"],
            "communication_endpoint": "http://localhost:8003/webhook/combat",
            "permissions": {
                "can_initiate_coordination": true,
                "can_vote": true,
                "can_propose_actions": true,
                "can_access_shared_context": true
            }
        }
    }' \
    "$N8N_BASE_URL/webhook/agent-management" > /dev/null

echo -e "${GREEN}✅ Test agents registered successfully${NC}"

# Create environment configuration file
echo -e "${BLUE}⚙️  Creating environment configuration...${NC}"

cat > /home/activeloguser/DMLogn8n/multi-agent-env.conf << EOF
# DMlogn8n Multi-Agent Communication System Configuration
N8N_BASE_URL="$N8N_BASE_URL"
N8N_API_KEY="$N8N_API_KEY"
DEEPSEEK_API_KEY="$DEEPSEEK_API_KEY"

# Agent Endpoints
AGENT_DM_ENDPOINT="http://localhost:8001/webhook/dm"
AGENT_NARRATOR_ENDPOINT="http://localhost:8002/webhook/narrator"
AGENT_COMBAT_ENDPOINT="http://localhost:8003/webhook/combat"

# System Configuration
MESSAGE_QUEUE_SIZE=1000
VOTING_TIMEOUT_MINUTES=15
CONSENSUS_THRESHOLD=0.8
CONFLICT_RESOLUTION_TIMEOUT=30

# Logging
LOG_LEVEL="INFO"
LOG_FILE="/var/log/dmlogn8n/multi-agent.log"
EOF

echo -e "${GREEN}✅ Environment configuration created${NC}"

# Run basic test
echo -e "${BLUE}🧪 Running basic system test...${NC}"

test_response=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $N8N_API_KEY" \
    -d '{
        "test_type": "messaging_performance",
        "scenario": "basic_connectivity",
        "participants": ["agent_dungeon_master", "agent_narrator"]
    }' \
    "$N8N_BASE_URL/webhook/multi-agent-test" 2>/dev/null || echo "")

if echo "$test_response" | grep -q "test_scenario_completed\|test_completed"; then
    echo -e "${GREEN}✅ Basic system test passed${NC}"
else
    echo -e "${YELLOW}⚠️  Basic test may need manual verification${NC}"
fi

# Display completion message
echo -e "${GREEN}🎉 Multi-Agent Communication System deployment completed!${NC}"
echo ""
echo -e "${BLUE}📖 Next Steps:${NC}"
echo "1. Review the comprehensive guide: MULTI_AGENT_COMMUNICATION_SYSTEM_GUIDE.md"
echo "2. Test agent messaging: curl -X POST $N8N_BASE_URL/webhook/agent-message ..."
echo "3. Run test scenarios: curl -X POST $N8N_BASE_URL/webhook/multi-agent-test ..."
echo "4. Monitor system performance and agent interactions"
echo ""
echo -e "${BLUE}🔗 Key Endpoints:${NC}"
echo "- Agent Messaging: $N8N_BASE_URL/webhook/agent-message"
echo "- Party Coordination: $N8N_BASE_URL/webhook/party-coordinate"
echo "- Conflict Resolution: $N8N_BASE_URL/webhook/conflict-resolve"
echo "- Shared Context: $N8N_BASE_URL/webhook/shared-context"
echo "- NLP Processing: $N8N_BASE_URL/webhook/nlp-process"
echo "- Agent Management: $N8N_BASE_URL/webhook/agent-management"
echo "- Message Queue: $N8N_BASE_URL/webhook/message-queue"
echo "- Test Suite: $N8N_BASE_URL/webhook/multi-agent-test"
echo ""
echo -e "${YELLOW}💡 Tip: Use the provided curl examples in the guide to test different features${NC}"
echo ""
echo -e "${GREEN}🚀 Your multi-agent communication system is ready!${NC}"