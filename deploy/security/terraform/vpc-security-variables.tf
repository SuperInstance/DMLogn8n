# Variables for VPC Security Configuration

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "dmlog"
}

variable "environment" {
  description = "Environment (dev, staging, production)"
  type        = string
  validation {
    condition = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be one of: dev, staging, production."
  }
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnets" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnets" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.20.0/24"]
}

variable "database_subnets" {
  description = "CIDR blocks for database subnets"
  type        = list(string)
  default     = ["10.0.100.0/24", "10.0.200.0/24"]
}

variable "bastion_allowed_ips" {
  description = "CIDR blocks allowed to access bastion hosts"
  type        = list(string)
  default     = ["0.0.0.0/0"] # Override this in production
}

variable "enable_traffic_mirroring" {
  description = "Enable VPC traffic mirroring for security monitoring"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "DMLog"
    ManagedBy   = "Terraform"
    Security    = "Enhanced"
  }
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}