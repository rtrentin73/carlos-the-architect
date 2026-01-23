terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.80"
    }
  }

  backend "azurerm" {
    resource_group_name  = "carlos-tfstate-rg"
    storage_account_name = "carlostfstate"
    container_name       = "tfstate"
    key                  = "carlos.terraform.tfstate"
  }
}

provider "azurerm" {
  features {}
}
