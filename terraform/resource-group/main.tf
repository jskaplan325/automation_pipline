# Azure Resource Group Module
# Creates a standalone resource group for organizing Azure resources
#
# This module follows the portal's plug-and-play pattern:
# - Uses standard variables (project_name, environment, region)
# - Applies consistent tagging
# - Outputs resource details for downstream consumption

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = "rg-${var.project_name}-${var.environment}-${var.region_short}"
  location = var.region

  tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform-portal"
    CostCenter  = var.cost_center
  }
}
