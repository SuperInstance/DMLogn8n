# Variables for External Secrets Management

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

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "database_host" {
  description = "Database hostname"
  type        = string
}

variable "database_name" {
  description = "Database name"
  type        = string
  default     = "dmlog"
}

variable "redis_host" {
  description = "Redis hostname"
  type        = string
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

# External API Keys (sensitive variables)
variable "stripe_secret_key" {
  description = "Stripe secret key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "sendgrid_api_key" {
  description = "SendGrid API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "twilio_auth_token" {
  description = "Twilio auth token"
  type        = string
  sensitive   = true
  default     = ""
}

variable "google_client_id" {
  description = "Google OAuth client ID"
  type        = string
  sensitive   = true
  default     = ""
}

variable "google_secret" {
  description = "Google OAuth client secret"
  type        = string
  sensitive   = true
  default     = ""
}