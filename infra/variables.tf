variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "westus"
}

variable "environment" {
  description = "Environment name (prod, staging, dev)"
  type        = string
  default     = "prod"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "carlos"
}

variable "aks_node_count" {
  description = "Number of nodes in the AKS cluster"
  type        = number
  default     = 1
}

variable "aks_vm_size" {
  description = "VM size for AKS nodes"
  type        = string
  default     = "Standard_B2s"
}

variable "azure_openai_endpoint" {
  description = "Azure OpenAI endpoint URL"
  type        = string
  sensitive   = true
}

variable "azure_openai_api_key" {
  description = "Azure OpenAI API key"
  type        = string
  sensitive   = true
}

variable "azure_openai_deployment_name" {
  description = "Azure OpenAI deployment name"
  type        = string
  default     = "gpt-4o"
}

variable "azure_openai_api_version" {
  description = "Azure OpenAI API version"
  type        = string
  default     = "2024-08-01-preview"
}

variable "redis_sku" {
  description = "Azure Cache for Redis SKU (Basic, Standard, Premium)"
  type        = string
  default     = "Basic"
}

variable "redis_capacity" {
  description = "Azure Cache for Redis capacity (0-6 for Basic/Standard, 1-5 for Premium)"
  type        = number
  default     = 0
}

variable "redis_family" {
  description = "Azure Cache for Redis family (C for Basic/Standard, P for Premium)"
  type        = string
  default     = "C"
}
