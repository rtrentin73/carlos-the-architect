locals {
  resource_prefix = "${var.project_name}-${var.environment}"
  tags = {
    project     = var.project_name
    environment = var.environment
    managed_by  = "terraform"
  }
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = "${local.resource_prefix}-rg"
  location = var.location
  tags     = local.tags
}

# Azure Container Registry
resource "azurerm_container_registry" "main" {
  name                = "${var.project_name}${var.environment}acr"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = true
  tags                = local.tags
}

# App Service Plan (Linux)
resource "azurerm_service_plan" "main" {
  name                = "${local.resource_prefix}-plan"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = var.app_service_sku
  tags                = local.tags
}

# Backend App Service (Container)
resource "azurerm_linux_web_app" "backend" {
  name                = "${local.resource_prefix}-backend"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  service_plan_id     = azurerm_service_plan.main.id
  https_only          = true
  tags                = local.tags

  site_config {
    always_on                         = var.app_service_sku != "F1" && var.app_service_sku != "D1"
    container_registry_use_managed_identity = false

    application_stack {
      docker_image_name        = "${azurerm_container_registry.main.login_server}/carlos-backend:latest"
      docker_registry_url      = "https://${azurerm_container_registry.main.login_server}"
      docker_registry_username = azurerm_container_registry.main.admin_username
      docker_registry_password = azurerm_container_registry.main.admin_password
    }

    health_check_path = "/health"
  }

  app_settings = {
    WEBSITES_ENABLE_APP_SERVICE_STORAGE = "false"
    DOCKER_ENABLE_CI                    = "true"

    # Azure OpenAI settings
    AZURE_OPENAI_ENDPOINT        = var.azure_openai_endpoint
    AZURE_OPENAI_API_KEY         = var.azure_openai_api_key
    AZURE_OPENAI_DEPLOYMENT_NAME = var.azure_openai_deployment_name
    AZURE_OPENAI_API_VERSION     = var.azure_openai_api_version
    OPENAI_API_VERSION           = var.azure_openai_api_version

    # CORS - allow frontend
    ALLOWED_ORIGINS = "https://${local.resource_prefix}-frontend.azurestaticapps.net"
  }
}

# Static Web App for Frontend
resource "azurerm_static_web_app" "frontend" {
  name                = "${local.resource_prefix}-frontend"
  resource_group_name = azurerm_resource_group.main.name
  location            = "eastus2" # Static Web Apps have limited regions
  sku_tier            = "Free"
  sku_size            = "Free"
  tags                = local.tags
}
