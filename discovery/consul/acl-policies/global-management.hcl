# Global Management Policy
# Provides full access to all resources for platform administrators

key_prefix "" {
  policy = "read"
  capabilities = ["list", "read", "create", "update", "delete"]
}

key_prefix "dmlogn8n/" {
  policy = "write"
  capabilities = ["list", "read", "create", "update", "delete"]
}

service_prefix "" {
  policy = "read"
  capabilities = ["list", "read", "register", "deregister"]
}

service_prefix "dmlogn8n-" {
  policy = "write"
  capabilities = ["list", "read", "register", "deregister"]
}

node_prefix "" {
  policy = "read"
  capabilities = ["list", "read"]
}

agent_prefix "" {
  policy = "read"
  capabilities = ["list", "read"]
}

operator = "write"

session_prefix "" {
  policy = "write"
  capabilities = ["create", "read", "update", "delete"]
}

event_prefix "" {
  policy = "write"
  capabilities = ["fire", "list"]
}

query_prefix "" {
  policy = "write"
  capabilities = ["create", "read", "update", "delete"]
}

namespace_prefix "" {
  policy = "write"
  capabilities = ["list", "read", "create", "update", "delete"]
}

partition_prefix "" {
  policy = "write"
  capabilities = ["list", "read", "create", "update", "delete"]
}

intention_prefix "" {
  policy = "write"
  capabilities = ["create", "read", "update", "delete"]
}

ca_prefix "" {
  policy = "write"
  capabilities = ["read", "create", "update", "delete"]
}

peering_prefix "" {
  policy = "write"
  capabilities = ["create", "read", "update", "delete"]
}