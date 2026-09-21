variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "dmlog"
}

variable "cluster_version" {
  description = "EKS cluster version"
  type        = string
  default     = "1.28"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "private_subnets" {
  description = "Private subnets CIDR blocks"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "public_subnets" {
  description = "Public subnets CIDR blocks"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}

variable "database_subnets" {
  description = "Database subnets CIDR blocks"
  type        = list(string)
  default     = ["10.0.201.0/24", "10.0.202.0/24"]
}

variable "enable_cluster_autoscaler" {
  description = "Enable cluster autoscaler"
  type        = bool
  default     = true
}

variable "node_groups" {
  description = "EKS node groups configuration"
  type = map(object({
    instance_types = list(string)
    desired_size   = number
    max_size       = number
    min_size       = number
    disk_size      = number
  }))
  default = {
    general = {
      instance_types = ["t3.medium", "t3.large"]
      desired_size   = 2
      max_size       = 10
      min_size       = 1
      disk_size      = 50
    }
    system = {
      instance_types = ["t3.medium"]
      desired_size   = 1
      max_size       = 3
      min_size       = 1
      disk_size      = 50
    }
  }
}

variable "database_config" {
  description = "RDS database configuration"
  type = object({
    engine         = string
    engine_version = string
    instance_class = string
    allocated_storage = number
    max_allocated_storage = number
    storage_type   = string
    storage_encrypted = bool
    backup_retention_period = number
    backup_window = string
    maintenance_window = string
    deletion_protection = bool
  })
  default = {
    engine         = "postgres"
    engine_version = "15.4"
    instance_class = "db.m5.large"
    allocated_storage = 100
    max_allocated_storage = 1000
    storage_type   = "gp2"
    storage_encrypted = true
    backup_retention_period = 7
    backup_window = "03:00-04:00"
    maintenance_window = "sun:04:00-sun:05:00"
    deletion_protection = false
  }
}

variable "redis_config" {
  description = "ElastiCache Redis configuration"
  type = object({
    node_type = string
    num_cache_nodes = number
    port = number
    parameter_group_name = string
    at_rest_encryption_enabled = bool
    transit_encryption_enabled = bool
    auth_token = string
    automatic_failover_enabled = bool
    multi_az_enabled = bool
  })
  default = {
    node_type = "cache.m5.large"
    num_cache_nodes = 1
    port = 6379
    parameter_group_name = "default.redis7"
    at_rest_encryption_enabled = true
    transit_encryption_enabled = true
    auth_token = ""
    automatic_failover_enabled = true
    multi_az_enabled = true
  }
}

variable "domain_name" {
  description = "Root domain name"
  type        = string
  default     = "dmlog.com"
}

variable "subdomains" {
  description = "Application subdomains"
  type = object({
    api = string
    app = string
    monitoring = string
  })
  default = {
    api = "api"
    app = "app"
    monitoring = "monitoring"
  }
}

variable "cloudflare_api_token" {
  description = "Cloudflare API token"
  type        = string
  sensitive   = true
}

variable "ssl_certificate_arn" {
  description = "ARN of SSL certificate"
  type        = string
  default     = ""
}

variable "enable_monitoring" {
  description = "Enable monitoring stack"
  type        = bool
  default     = true
}

variable "enable_logging" {
  description = "Enable logging stack"
  type        = bool
  default     = true
}

variable "enable_backup" {
  description = "Enable backup configuration"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
}