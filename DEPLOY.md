# Azure Deployment Guide

This guide explains how to deploy Carlos the Architect to Azure using Terraform and GitHub Actions.

## Prerequisites

- Azure subscription
- Azure CLI installed and logged in
- GitHub repository with Actions enabled
- Terraform CLI (for local testing)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Azure Cloud                              │
│  ┌─────────────────┐     ┌─────────────────────────────┐   │
│  │ Static Web App  │     │     App Service (Linux)      │   │
│  │   (Frontend)    │────▶│        (Backend API)         │   │
│  │   React/Vite    │     │    FastAPI + LangGraph       │   │
│  └─────────────────┘     └──────────────┬──────────────┘   │
│                                          │                   │
│  ┌─────────────────┐     ┌──────────────▼──────────────┐   │
│  │ Container       │     │      Azure OpenAI           │   │
│  │ Registry (ACR)  │     │        (GPT-4o)             │   │
│  └─────────────────┘     └─────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Setup Steps

### 1. Create Azure Service Principal

```bash
# Create service principal for GitHub Actions
az ad sp create-for-rbac \
    --name "carlos-github-actions" \
    --role contributor \
    --scopes /subscriptions/<SUBSCRIPTION_ID> \
    --sdk-auth
```

Save the JSON output - you'll need it for GitHub secrets.

### 2. Setup Terraform Backend Storage

```bash
cd infra
chmod +x setup-backend.sh
./setup-backend.sh
```

### 3. Configure GitHub Secrets

Go to your repository Settings → Secrets and variables → Actions, and add:

| Secret | Description |
|--------|-------------|
| `AZURE_CREDENTIALS` | Full JSON output from service principal creation |
| `AZURE_CLIENT_ID` | `appId` from service principal |
| `AZURE_CLIENT_SECRET` | `password` from service principal |
| `AZURE_SUBSCRIPTION_ID` | Your Azure subscription ID |
| `AZURE_TENANT_ID` | `tenant` from service principal |
| `AZURE_OPENAI_ENDPOINT` | Your Azure OpenAI endpoint URL |
| `AZURE_OPENAI_API_KEY` | Your Azure OpenAI API key |

### 4. Deploy

Push to the `main` branch or manually trigger the workflow:

```bash
git push origin main
```

Or go to Actions → Deploy to Azure → Run workflow

## Local Development with Terraform

```bash
cd infra

# Copy example variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Apply changes
terraform apply
```

## Outputs

After deployment, Terraform will output:

- `backend_url` - Backend API URL (https://carlos-prod-backend.azurewebsites.net)
- `frontend_url` - Frontend URL (https://carlos-prod-frontend.azurestaticapps.net)
- `acr_login_server` - Container registry URL

## Costs

Estimated monthly costs (East US region):

| Resource | SKU | Est. Cost |
|----------|-----|-----------|
| App Service Plan | B1 | ~$13/month |
| Container Registry | Basic | ~$5/month |
| Static Web App | Free | $0 |
| Storage (TF state) | Standard | ~$1/month |
| **Total** | | **~$19/month** |

## Troubleshooting

### Backend not starting

Check App Service logs:
```bash
az webapp log tail --name carlos-prod-backend --resource-group carlos-prod-rg
```

### CORS errors

Ensure `ALLOWED_ORIGINS` in App Service settings includes your frontend URL.

### Terraform state issues

If state is corrupted, you can import existing resources:
```bash
terraform import azurerm_resource_group.main /subscriptions/<sub>/resourceGroups/carlos-prod-rg
```
