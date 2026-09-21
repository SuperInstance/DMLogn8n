# AI Agent Policy
# Provides access for AI agents to register and coordinate

# Allow agents to register and manage themselves
service_prefix "dmlogn8n-agent" {
  policy = "write"
  capabilities = ["list", "read", "register", "deregister"]
}

# Allow agents to access their own configuration
key_prefix "dmlogn8n/agents/{{agent_id}}/" {
  policy = "write"
  capabilities = ["list", "read", "create", "update", "delete"]
}

# Allow agents to read shared configuration
key_prefix "dmlogn8n/config/global/" {
  policy = "read"
  capabilities = ["list", "read"]
}

key_prefix "dmlogn8n/config/environment/{{environment}}/" {
  policy = "read"
  capabilities = ["list", "read"]
}

# Allow agents to participate in collaboration sessions
key_prefix "dmlogn8n/collaborations/" {
  policy = "write"
  capabilities = ["list", "read", "create", "update", "delete"]
}

# Allow agents to submit and manage tasks
key_prefix "dmlogn8n/tasks/{{agent_id}}/" {
  policy = "write"
  capabilities = ["list", "read", "create", "update", "delete"]
}

# Allow agents to discover other agents
service_prefix "dmlogn8n-agent" {
  policy = "read"
  capabilities = ["list", "read"]
}

# Allow agents to discover other services
service_prefix "dmlogn8n-" {
  policy = "read"
  capabilities = ["list", "read"]
}

# Allow agents to read health information
node_prefix "" {
  policy = "read"
  capabilities = ["list", "read"]
}

# Allow agents to fire coordination events
event_prefix "agent-" {
  policy = "write"
  capabilities = ["fire", "list"]
}

# Allow agents to use distributed locks
key_prefix "dmlogn8n/locks/agent/" {
  policy = "write"
  capabilities = ["create", "read", "delete"]
}

# Allow agents to update their own metrics
key_prefix "dmlogn8n/metrics/agents/{{agent_id}}/" {
  policy = "write"
  capabilities = ["list", "read", "create", "update", "delete"]
}