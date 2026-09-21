# Variables for Security Automation

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

variable "delegated_admin_account_id" {
  description = "AWS account ID for delegated administrator"
  type        = string
  default     = ""
}

variable "enable_cis_controls" {
  description = "Enable CIS AWS Foundations controls"
  type        = bool
  default     = true
}

variable "enable_pci_dss_controls" {
  description = "Enable PCI DSS controls"
  type        = bool
  default     = false
}

variable "enable_inspector_scan" {
  description = "Enable Inspector2 scanning"
  type        = bool
  default     = true
}

variable "security_alert_emails" {
  description = "Email addresses to receive security alerts"
  type        = list(string)
  default     = []
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for security notifications"
  type        = string
  default     = ""
  sensitive   = true
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

# Security Controls mappings (these would be populated based on your AWS account)
variable "cis_controls" {
  description = "CIS AWS Foundations controls to enable"
  type        = map(string)
  default     = {}
}

variable "pci_dss_controls" {
  description = "PCI DSS controls to enable"
  type        = map(string)
  default     = {}
}