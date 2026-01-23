#!/bin/bash
# Setup script for Terraform backend storage in Azure
# Run this once before using Terraform

set -e

RESOURCE_GROUP="carlos-tfstate-rg"
STORAGE_ACCOUNT="carlostfstate"
CONTAINER_NAME="tfstate"
LOCATION="eastus"

echo "Creating resource group for Terraform state..."
az group create --name $RESOURCE_GROUP --location $LOCATION

echo "Creating storage account..."
az storage account create \
    --name $STORAGE_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku Standard_LRS \
    --encryption-services blob

echo "Creating blob container..."
az storage container create \
    --name $CONTAINER_NAME \
    --account-name $STORAGE_ACCOUNT

echo "Enabling versioning for state file protection..."
az storage account blob-service-properties update \
    --account-name $STORAGE_ACCOUNT \
    --enable-versioning true

echo ""
echo "Terraform backend setup complete!"
echo ""
echo "Add these values to your Terraform backend configuration:"
echo "  resource_group_name  = \"$RESOURCE_GROUP\""
echo "  storage_account_name = \"$STORAGE_ACCOUNT\""
echo "  container_name       = \"$CONTAINER_NAME\""
echo "  key                  = \"carlos.terraform.tfstate\""
