output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "acr_login_server" {
  description = "Azure Container Registry login server"
  value       = azurerm_container_registry.main.login_server
}

output "acr_admin_username" {
  description = "Azure Container Registry admin username"
  value       = azurerm_container_registry.main.admin_username
  sensitive   = true
}

output "acr_admin_password" {
  description = "Azure Container Registry admin password"
  value       = azurerm_container_registry.main.admin_password
  sensitive   = true
}

output "backend_url" {
  description = "Backend App Service URL"
  value       = "https://${azurerm_linux_web_app.backend.default_hostname}"
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
