# Production Environment Configuration

environment = "production"
aws_region  = "us-west-2"
project_name = "dmlog"

# VPC Configuration
vpc_cidr           = "10.0.0.0/16"
public_subnets     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
private_subnets    = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
database_subnets   = ["10.0.201.0/24", "10.0.202.0/24"]

# EKS Configuration
cluster_version = "1.28"
node_groups = {
  general = {
    instance_types = ["m5.large", "m5.xlarge"]
    desired_size   = 3
    max_size       = 20
    min_size       = 3
    disk_size      = 100
  }
  system = {
    instance_types = ["m5.large"]
    desired_size   = 1
    max_size       = 3
    min_size       = 1
    disk_size      = 50
  }
}

# Database Configuration
database_config = {
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.m5.2xlarge"
  allocated_storage = 500
  max_allocated_storage = 2000
  storage_type   = "gp2"
  storage_encrypted = true
  backup_retention_period = 30
  backup_window = "03:00-04:00"
  maintenance_window = "sun:04:00-sun:05:00"
  deletion_protection = true
  port = 5432
}

# Redis Configuration
redis_config = {
  node_type = "cache.m5.2xlarge"
  num_cache_nodes = 3
  port = 6379
  parameter_group_name = "default.redis7"
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  automatic_failover_enabled = true
  multi_az_enabled = true
}

# Domain Configuration
domain_name = "dmlog.com"
subdomains = {
  api = "api"
  app = "app"
  monitoring = "monitoring"
}

# Monitoring and Logging
enable_monitoring = true
enable_logging    = true
enable_backup     = true

# Additional Tags
tags = {
  Environment = "production"
  Team        = "platform"
  CostCenter  = "engineering"
  Owner       = "dmlog-team"
}