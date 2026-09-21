# Monitoring System Policy
# Provides read access for monitoring and observability systems

# Allow reading all services
service_prefix "" {
  policy = "read"
  capabilities = ["list", "read"]
}

# Allow reading all nodes
node_prefix "" {
  policy = "read"
  capabilities = ["list", "read"]
}

# Allow reading all agents
agent_prefix "" {
  policy = "read"
  capabilities = ["list", "read"]
}

# Allow reading all configuration
key_prefix "" {
  policy = "read"
  capabilities = ["list", "read"]
}

# Allow reading events
event_prefix "" {
  policy = "read"
  capabilities = ["list"]
}

# Allow reading queries
query_prefix "" {
  policy = "read"
  capabilities = ["list", "read"]
}

# Allow reading sessions
session_prefix "" {
  policy = "read"
  capabilities = ["list", "read"]
}

# Allow reading intentions
intention_prefix "" {
  policy = "read"
  capabilities = ["list", "read"]
}

# Allow reading CA information
ca_prefix "" {
  policy = "read"
  capabilities = ["list", "read"]
}

# Allow reading peering information
peering_prefix "" {
  policy = "read"
  capabilities = ["list", "read"]
}

# Allow reading namespaces
namespace_prefix "" {
  policy = "read"
  capabilities = ["list", "read"]
}

# Allow reading partitions
partition_prefix "" {
  policy = "read"
  capabilities = ["list", "read"]
}

# Allow access to metrics data
key_prefix "dmlogn8n/metrics/" {
  policy = "read"
  capabilities = ["list", "read"]
}

# Allow access to health data
key_prefix "dmlogn8n/health/" {
  policy = "read"
  capabilities = ["list", "read"]
}

# Allow access to topology and dependency data
key_prefix "dmlogn8n/topology/" {
  policy = "read"
  capabilities = ["list", "read"]
}

key_prefix "dmlogn8n/dependencies/" {
  policy = "read"
  capabilities = ["list", "read"]
}

# Allow access to agent coordination data
key_prefix "dmlogn8n/agents/" {
  policy = "read"
  capabilities = ["list", "read"]
}

key_prefix "dmlogn8n/collaborations/" {
  policy = "read"
  capabilities = ["list", "read"]
}

key_prefix "dmlogn8n/tasks/" {
  policy = "read"
  capabilities = ["list", "read"]
}