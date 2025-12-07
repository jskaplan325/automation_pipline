# Outputs for Resource Group Module
# These values are displayed to users after deployment

output "resource_group_name" {
  description = "The name of the created resource group"
  value       = azurerm_resource_group.main.name
}

output "resource_group_id" {
  description = "The Azure resource ID of the resource group"
  value       = azurerm_resource_group.main.id
}

output "resource_group_location" {
  description = "The Azure region where the resource group was created"
  value       = azurerm_resource_group.main.location
}

output "tags" {
  description = "The tags applied to the resource group"
  value       = azurerm_resource_group.main.tags
}
