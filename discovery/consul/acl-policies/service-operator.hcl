# Service Operator Policy
# Provides access for service operators to manage their own services

# Allow operators to read global service information
service_prefix "" {
  policy = "read"
  capabilities = ["list", "read"]
}

# Allow operators to manage their own services
service_prefix "dmlogn8n-{{service_name}}" {
  policy = "write"
  capabilities = ["list", "read", "register", "deregister"]
}

# Allow reading of health checks
node_prefix "" {
  policy = "read"
  capabilities = ["list", "read"]
}

# Allow access to their own configuration keys
key_prefix "dmlogn8n/config/service/{{service_name}}/" {
  policy = "write"
  capabilities = ["list", "read", "create", "update", "delete"]
}

key_prefix "dmlogn8n/config/environment/{{environment}}/" {
  policy = "read"
  capabilities = ["list", "read"]
}

# Allow reading global configuration
key_prefix "dmlogn8n/config/global/" {
  policy = "read"
  capabilities = ["list", "read"]
}

# Allow managing their own health checks
agent_prefix "agent-{{service_name}}" {
  policy = "write"
  capabilities = ["list", "read"]
}

# Allow firing events for their services
event_prefix "{{service_name}}-" {
  policy = "write"
  capabilities = ["fire", "list"]
}

# Allow reading agent topology and service dependencies
key_prefix "dmlogn8n/topology/" {
  policy = "read"
  capabilities = ["list", "read"]
}

key_prefix "dmlogn8n/dependencies/" {
  policy = "read"
  capabilities = ["list", "read"]
}

# Allow access to metrics for their services
key_prefix "dmlogn8n/metrics/{{service_name}}/" {
  policy = "write"
  capabilities = ["list", "read", "create", "update", "delete"]
}