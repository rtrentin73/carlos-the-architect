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

output "aks_cluster_name" {
  description = "AKS cluster name"
  value       = azurerm_kubernetes_cluster.main.name
}

output "aks_kube_config" {
  description = "AKS kubeconfig"
  value       = azurerm_kubernetes_cluster.main.kube_config_raw
  sensitive   = true
}

output "redis_hostname" {
  description = "Azure Cache for Redis hostname"
  value       = azurerm_redis_cache.main.hostname
}

output "redis_port" {
  description = "Azure Cache for Redis SSL port"
  value       = azurerm_redis_cache.main.ssl_port
}

output "redis_primary_access_key" {
  description = "Azure Cache for Redis primary access key"
  value       = azurerm_redis_cache.main.primary_access_key
  sensitive   = true
}

output "cosmosdb_endpoint" {
  description = "Azure Cosmos DB endpoint"
  value       = azurerm_cosmosdb_account.main.endpoint
}

output "cosmosdb_primary_key" {
  description = "Azure Cosmos DB primary key"
  value       = azurerm_cosmosdb_account.main.primary_key
  sensitive   = true
}

output "cosmosdb_database_name" {
  description = "Azure Cosmos DB database name"
  value       = azurerm_cosmosdb_sql_database.feedback.name
}

output "document_intelligence_endpoint" {
  description = "Azure AI Document Intelligence endpoint"
  value       = azurerm_cognitive_account.document_intelligence.endpoint
}

output "document_intelligence_key" {
  description = "Azure AI Document Intelligence primary key"
  value       = azurerm_cognitive_account.document_intelligence.primary_access_key
  sensitive   = true
}
