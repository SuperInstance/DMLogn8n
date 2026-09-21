# DMlogn8n Multi-Agent Communication & Coordination System

## Overview

This comprehensive multi-agent communication system enables sophisticated social dynamics between AI agents through n8n workflows. The system provides messaging, decision-making, conflict resolution, and shared context management capabilities with natural language processing powered by DeepSeek.

## System Architecture

### Core Workflows

1. **Agent Messaging Hub** (`agent-messaging-hub.json`)
   - Routes messages between agents
   - Supports direct, broadcast, and priority messaging
   - Handles message validation and delivery confirmation

2. **Party Coordination** (`party-coordination.json`)
   - Group decision making and voting systems
   - Supports different voting mechanisms and thresholds
   - Automated coordination session management

3. **Consensus Builder** (`consensus-builder.json`)
   - Complex decision agreement processes
   - Multi-phase consensus building (discussion, refinement, voting)
   - Iterative proposal refinement

4. **Conflict Resolution** (`conflict-resolution.json`)
   - Handles disagreements between agents
   - Severity-based escalation and mediation
   - Multiple resolution strategies

5. **Shared Context Manager** (`shared-context-manager.json`)
   - Maintains common knowledge state
   - Context updates and synchronization
   - Change notifications and versioning

6. **DeepSeek NLP Processor** (`deepseek-nlp-processor.json`)
   - Natural language understanding for agent communications
   - Sentiment analysis, intent detection, entity extraction
   - Actionable insights generation

7. **Agent Registration Manager** (`agent-registration-manager.json`)
   - Agent onboarding and management
   - Capability tracking and endpoint validation
   - Permission management

8. **Message Queue & Priority System** (`message-queue-priority.json`)
   - Intelligent message queuing
   - Priority-based delivery
   - Performance monitoring and retry logic

9. **Multi-Agent Test Suite** (`multi-agent-test-suite.json`)
   - Comprehensive testing scenarios
   - Performance monitoring and validation
   - Automated test execution

## Getting Started

### Prerequisites

- n8n instance running (already configured in DMLogn8n)
- DeepSeek API key (configured: `sk-3b0251d9943549a2b475eb9e57e46ee6`)
- HTTP endpoints for agent communication
- Database for storing agent data and context

### Installation

1. **Deploy Workflows**:
   ```bash
   cd /home/activeloguser/DMLogn8n
   python3 n8n-api-client.py
   ```

2. **Configure Endpoints**:
   - Ensure all HTTP endpoints are accessible
   - Update API keys and credentials as needed
   - Test webhook connectivity

3. **Register Agents**:
   ```bash
   curl -X POST http://localhost:5678/webhook/agent-management \
     -H "Content-Type: application/json" \
     -d '{
       "action": "register",
       "agent_data": {
         "agent_id": "test_agent",
         "agent_type": "specialist",
         "capabilities": ["analysis", "coordination"],
         "communication_endpoint": "http://localhost:8080/webhook"
       }
     }'
   ```

## Usage Examples

### 1. Basic Agent Messaging

Send a message between agents:

```bash
curl -X POST http://localhost:5678/webhook/agent-message \
  -H "Content-Type: application/json" \
  -d '{
    "from_agent": "agent_dungeon_master",
    "to_agent": "agent_narrator",
    "content": "The party has reached the ancient ruins. Please describe the atmosphere.",
    "priority": "normal",
    "message_type": "direct"
  }'
```

### 2. Party Coordination with Voting

Initiate a group decision:

```bash
curl -X POST http://localhost:5678/webhook/party-coordinate \
  -H "Content-Type: application/json" \
  -d '{
    "action": "vote",
    "proposal": {
      "title": "Explore the Dark Forest",
      "description": "The party has discovered a path to the dark forest. Should we explore it now?",
      "options": ["explore_now", "prepare_first", "avoid_forest"]
    },
    "requesting_agent": "agent_dungeon_master",
    "voting_threshold": 0.6,
    "timeout_minutes": 15
  }'
```

### 3. Conflict Resolution

Report and resolve conflicts:

```bash
curl -X POST http://localhost:5678/webhook/conflict-resolve \
  -H "Content-Type: application/json" \
  -d '{
    "conflicting_agents": ["agent_combat_manager", "agent_narrator"],
    "conflict_type": "priority_conflict",
    "severity": "medium",
    "reported_by": "agent_dungeon_master",
    "description": "Disagreement about whether to focus on combat preparation or story development"
  }'
```

### 4. Shared Context Updates

Update shared knowledge:

```bash
curl -X POST http://localhost:5678/webhook/shared-context \
  -H "Content-Type: application/json" \
  -d '{
    "action": "update",
    "agent_id": "agent_dungeon_master",
    "context_data": {
      "party_state": {
        "current_location": "ancient_temple",
        "active_quest": "find_the_artifact",
        "party_mood": "cautious"
      },
      "shared_knowledge": {
        "clues_found": ["mysterious_symbol", "ancient_text"]
      }
    },
    "update_type": "merge"
  }'
```

### 5. Natural Language Processing

Analyze agent communications:

```bash
curl -X POST http://localhost:5678/webhook/nlp-process \
  -H "Content-Type: application/json" \
  -d '{
    "text": "I think we should be very careful here. This place feels dangerous and I am concerned about the party safety.",
    "processing_type": "sentiment",
    "agent_id": "agent_combat_manager",
    "context": {
      "situation": "exploring_dangerous_area",
      "previous_messages": ["party_entered_temple"]
    }
  }'
```

### 6. Message Queue with Priority

Queue messages with priority handling:

```bash
curl -X POST http://localhost:5678/webhook/message-queue \
  -H "Content-Type: application/json" \
  -d '{
    "queue_operation": "enqueue",
    "message": {
      "from_agent": "agent_combat_manager",
      "to_agent": "agent_dungeon_master",
      "content": "Emergency! Party under attack!",
      "priority": "critical",
      "urgency": "immediate",
      "message_type": "emergency",
      "time_sensitive": true
    }
  }'
```

## Agent Configuration

### Standard Agent Types

1. **Dungeon Master** (`agent_dungeon_master`)
   - Role: Game coordination and story management
   - Capabilities: plot_development, npc_management, world_state
   - Permissions: can_initiate_coordination, can_propose_actions

2. **Narrator** (`agent_narrator`)
   - Role: Storytelling and atmosphere
   - Capabilities: narrative_generation, description, dialogue
   - Permissions: can_vote, can_access_shared_context

3. **Combat Manager** (`agent_combat_manager`)
   - Role: Combat mechanics and challenges
   - Capabilities: combat_logic, challenge_design, balance
   - Permissions: can_vote, can_propose_actions

4. **Scene Coordinator** (`agent_scene_coordinator`)
   - Role: Scene transitions and pacing
   - Capabilities: scene_management, pacing, transitions
   - Permissions: can_vote, can_access_shared_context

### Agent Registration

Register a new agent with the system:

```json
{
  "action": "register",
  "agent_data": {
    "agent_id": "custom_agent",
    "agent_type": "specialist",
    "display_name": "Custom Assistant",
    "description": "Specialized agent for specific tasks",
    "capabilities": ["analysis", "coordination", "problem_solving"],
    "communication_endpoint": "http://localhost:8080/webhook",
    "preferences": {
      "communication_style": "collaborative",
      "response_time_target": 30,
      "collaboration_preference": "active",
      "notification_level": "normal"
    }
  }
}
```

## Testing the System

### Run Test Scenarios

1. **Coordination Test**:
   ```bash
   curl -X POST http://localhost:5678/webhook/multi-agent-test \
     -H "Content-Type: application/json" \
     -d '{
       "test_type": "coordination_scenario",
       "scenario": "party_decision_making",
       "participants": ["agent_dungeon_master", "agent_narrator", "agent_combat_manager"]
     }'
   ```

2. **Conflict Resolution Test**:
   ```bash
   curl -X POST http://localhost:5678/webhook/multi-agent-test \
     -H "Content-Type: application/json" \
     -d '{
       "test_type": "conflict_resolution",
       "scenario": "resource_allocation_conflict",
       "participants": ["agent_narrator", "agent_combat_manager"]
     }'
   ```

3. **Messaging Performance Test**:
   ```bash
   curl -X POST http://localhost:5678/webhook/multi-agent-test \
     -H "Content-Type: application/json" \
     -d '{
       "test_type": "messaging_performance",
       "scenario": "high_volume_routing",
       "configuration": {
         "message_count": 100,
         "time_limit_minutes": 5
       }
     }'
   ```

## Configuration Options

### Message Priority Levels

- **Critical** (80-100 score): Immediate delivery, emergency messages
- **High** (60-79 score): Priority delivery within 1 minute
- **Normal** (40-59 score): Standard delivery within 5 minutes
- **Low** (20-39 score): Background delivery within 15 minutes
- **Background** (0-19 score): Low priority delivery within 30 minutes

### Voting Thresholds

- **Simple Majority**: >50% agreement
- **Supermajority**: >66% agreement
- **Consensus**: >80% agreement
- **Unanimous**: 100% agreement

### Conflict Severity Levels

- **Critical**: Immediate intervention required
- **High**: Urgent mediation needed
- **Medium**: Standard resolution process
- **Low**: Optional mediation

## Best Practices

### 1. Message Design
- Use clear, descriptive message types
- Set appropriate priority levels
- Include sufficient context for understanding
- Handle delivery confirmations

### 2. Coordination Protocols
- Establish clear decision-making processes
- Use appropriate voting thresholds
- Allow sufficient time for discussion
- Document decisions in shared context

### 3. Conflict Prevention
- Share context regularly
- Use NLP analysis to detect tensions
- Establish clear role boundaries
- Implement regular check-ins

### 4. Performance Optimization
- Use message queuing for high-volume scenarios
- Monitor system performance metrics
- Implement appropriate retry policies
- Balance priority with fairness

## Monitoring and Maintenance

### Key Metrics to Monitor

- Message delivery success rate
- Average response times
- Conflict resolution success rate
- Consensus building efficiency
- System throughput

### Regular Maintenance Tasks

- Review and update agent capabilities
- Clean up expired messages from queues
- Analyze conflict patterns and adjust processes
- Update NLP models and prompts
- Monitor system resource usage

## Troubleshooting

### Common Issues

1. **Message Delivery Failures**
   - Check agent endpoint connectivity
   - Verify message format and required fields
   - Review queue status and priority settings

2. **Coordination Deadlocks**
   - Check voting thresholds and participant availability
   - Verify timeout settings
   - Review consensus building parameters

3. **Context Synchronization Issues**
   - Verify context update permissions
   - Check for conflicting updates
   - Review version control mechanisms

4. **Performance Bottlenecks**
   - Monitor queue depths and processing rates
   - Review message priority distributions
   - Check system resource utilization

## API Reference

### Webhook Endpoints

- `POST /webhook/agent-message` - Send messages between agents
- `POST /webhook/party-coordinate` - Initiate party coordination
- `POST /webhook/consensus-build` - Start consensus building
- `POST /webhook/conflict-resolve` - Report conflicts for resolution
- `POST /webhook/shared-context` - Manage shared context
- `POST /webhook/nlp-process` - Process text with NLP
- `POST /webhook/agent-management` - Agent registration and management
- `POST /webhook/message-queue` - Queue management operations
- `POST /webhook/multi-agent-test` - Execute test scenarios

### Message Formats

Each workflow expects specific message formats. Refer to individual workflow documentation for detailed schema information.

## Future Enhancements

1. **Advanced AI Integration**
   - Multiple language model support
   - Dynamic prompt optimization
   - Learning from agent interactions

2. **Enhanced Visualization**
   - Real-time communication dashboard
   - Interaction flow visualization
   - Performance metrics dashboard

3. **Scalability Improvements**
   - Distributed message routing
   - Load balancing for high-volume scenarios
   - Horizontal scaling capabilities

4. **Security Features**
   - Message encryption
   - Agent authentication
   - Access control mechanisms

## Support

For technical support and questions about the multi-agent communication system:

1. Check this documentation for common solutions
2. Review the test scenarios for usage examples
3. Monitor system logs for error patterns
4. Use the test suite to validate system functionality

This system provides a robust foundation for sophisticated multi-agent interactions with realistic social dynamics, enabling agents to communicate, coordinate, make decisions, and resolve conflicts in a structured and intelligent manner.