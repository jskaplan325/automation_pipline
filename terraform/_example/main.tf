# Example Terraform Module
# This shows how to structure your Terraform for the portal
#
# Variables defined here should match your catalog YAML parameters

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
  name     = "rg-${var.project_name}-${var.environment}"
  location = var.region

  tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform-portal"
  }
}

# Example: Storage Account
resource "azurerm_storage_account" "main" {
  name                     = "st${replace(var.project_name, "-", "")}${var.environment}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = var.size == "large" ? "Premium" : "Standard"
  account_replication_type = var.size == "small" ? "LRS" : "GRS"

  tags = azurerm_resource_group.main.tags
}

# Outputs - these can be shown to users after deployment
output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "storage_account_name" {
  value = azurerm_storage_account.main.name
}

output "storage_account_primary_endpoint" {
  value = azurerm_storage_account.main.primary_blob_endpoint
}
