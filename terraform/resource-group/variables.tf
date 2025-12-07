# Variables for Resource Group Module
# These map to catalog YAML parameters and are passed via the portal

variable "project_name" {
  description = "Name of the project (used in resource naming)"
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "Project name must be lowercase alphanumeric with hyphens only."
  }
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "test", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, test, staging, or prod."
  }
}

variable "region" {
  description = "Azure region for deployment"
  type        = string
  default     = "eastus"
}

variable "region_short" {
  description = "Short code for region (used in naming)"
  type        = string
  default     = "eus"

  validation {
    condition     = can(regex("^[a-z]{2,5}$", var.region_short))
    error_message = "Region short code must be 2-5 lowercase letters."
  }
}

variable "cost_center" {
  description = "Cost center for billing allocation"
  type        = string
  default     = "default"
}
