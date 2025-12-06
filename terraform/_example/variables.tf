# Variables - These map to catalog YAML parameters
# The portal passes these as -var arguments or via .tfvars

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
    condition     = contains(["dev", "test", "prod"], var.environment)
    error_message = "Environment must be dev, test, or prod."
  }
}

variable "region" {
  description = "Azure region for deployment"
  type        = string
  default     = "eastus"
}

variable "size" {
  description = "T-shirt size for resources (small, medium, large)"
  type        = string
  default     = "small"

  validation {
    condition     = contains(["small", "medium", "large"], var.size)
    error_message = "Size must be small, medium, or large."
  }
}
