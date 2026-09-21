# Variables for WAF and DDoS Protection

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

variable "enable_shield_advanced" {
  description = "Enable AWS Shield Advanced for enhanced DDoS protection"
  type        = bool
  default     = false
}

variable "enable_origin_shield" {
  description = "Enable CloudFront Origin Shield"
  type        = bool
  default     = true
}

variable "use_cloudfront_default_cert" {
  description = "Use CloudFront default certificate or custom ACM certificate"
  type        = bool
  default     = true
}

variable "malicious_ips" {
  description = "List of known malicious IP addresses to block"
  type        = list(string)
  default     = []
}

variable "security_alert_emails" {
  description = "Email addresses to receive security alerts"
  type        = list(string)
  default     = []
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

# VPC variables (referenced from VPC module)
variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs"
  type        = list(string)
}

variable "alb_security_group_id" {
  description = "Security group ID for ALB"
  type        = string
}