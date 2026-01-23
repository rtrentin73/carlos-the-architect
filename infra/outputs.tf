output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "backend_url" {
  description = "Backend App Service URL"
  value       = "https://${azurerm_linux_web_app.backend.default_hostname}"
}

output "backend_name" {
  description = "Backend App Service name"
  value       = azurerm_linux_web_app.backend.name
}

output "frontend_url" {
  description = "Frontend Static Web App URL"
  value       = "https://${azurerm_static_web_app.frontend.default_host_name}"
}

output "frontend_api_token" {
  description = "Static Web App deployment token"
  value       = azurerm_static_web_app.frontend.api_key
  sensitive   = true
}
