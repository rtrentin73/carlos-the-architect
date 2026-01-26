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
│                          ┌──────────────▼──────────────┐   │
│                          │      Azure OpenAI           │   │
│                          │        (GPT-4o)             │   │
│                          └─────────────────────────────┘   │
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

Go to your repository **Settings → Secrets and variables → Actions → Secrets**, and add:

**Required Azure Secrets:**

| Secret | Description |
|--------|-------------|
| `AZURE_CREDENTIALS` | Full JSON output from service principal creation |
| `AZURE_CLIENT_ID` | `appId` from service principal |
| `AZURE_CLIENT_SECRET` | `password` from service principal |
| `AZURE_SUBSCRIPTION_ID` | Your Azure subscription ID |
| `AZURE_TENANT_ID` | `tenant` from service principal |
| `AZURE_OPENAI_ENDPOINT` | Your Azure OpenAI endpoint URL |
| `AZURE_OPENAI_API_KEY` | Your Azure OpenAI API key |

**Required Application Secrets:**

| Secret | Description |
|--------|-------------|
| `JWT_SECRET_KEY` | Secret key for JWT token signing (generate a random 32+ char string) |
| `ADMIN_PASSWORD` | Password for default admin account (change from default `carlos-admin-2024`!) |
| `VITE_BACKEND_URL` | Backend API URL for frontend (e.g., `http://YOUR_IP:8000`) - **must include port** |
| `ALLOWED_ORIGINS` | CORS allowed origins (e.g., `http://YOUR_IP,http://localhost:5173`) |
| `OAUTH_REDIRECT_BASE` | Frontend URL for OAuth redirects (e.g., `http://YOUR_IP`) |

**Optional OAuth Secrets:**

| Secret | Description |
|--------|-------------|
| `GOOGLE_CLIENT_ID` | Google OAuth client ID (from Google Cloud Console) |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `GITHUB_CLIENT_ID` | GitHub OAuth client ID (from GitHub Developer Settings) |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth client secret |

### 4. Configure GitHub Variables (Optional)

Go to **Settings → Secrets and variables → Actions → Variables**, and add:

| Variable | Default | Description |
|----------|---------|-------------|
| `AZURE_LOCATION` | `westus` | Azure region for resources |
| `ENVIRONMENT` | `prod` | Environment name (prod, staging, dev) |
| `PROJECT_NAME` | `carlos` | Project name for resource naming |
| `APP_SERVICE_SKU` | `F1` | App Service Plan SKU (F1=Free, B1=Basic, S1=Standard) |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | `gpt-4o` | Azure OpenAI model deployment name |
| `AZURE_OPENAI_API_VERSION` | `2024-08-01-preview` | Azure OpenAI API version |

### 5. Deploy

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

## Costs

Estimated monthly costs:

| Resource | SKU | Est. Cost |
|----------|-----|-----------|
| App Service Plan | F1 (Free) | $0 |
| Static Web App | Free | $0 |
| Storage (TF state) | Standard | ~$1/month |
| **Total** | | **~$1/month** |

*Note: F1 tier has limitations (60 min/day compute). For production, use B1 (~$13/month) or higher.*

## Troubleshooting

### Backend not starting

Check App Service logs:
```bash
az webapp log tail --name carlos-prod-backend --resource-group carlos-prod-rg
```

### CORS errors

Ensure `ALLOWED_ORIGINS` in App Service settings includes your frontend URL.

### "Cannot connect to server" error

This error appears when the frontend cannot reach the backend. Common causes:

1. **Missing port in VITE_BACKEND_URL**: Must include port (e.g., `http://20.245.72.209:8000`, not `http://20.245.72.209`)
2. **VITE_BACKEND_URL is a build-time variable**: Changes require rebuilding the frontend Docker image
3. **Backend not running**: Check App Service logs
4. **Firewall blocking port 8000**: Ensure port 8000 is open in Azure NSG

To verify the configured backend URL, open browser DevTools Console and check the network requests.

### Quota errors

If you see quota errors for B1 VMs, either:
1. Use F1 (Free) tier: Set `APP_SERVICE_SKU=F1` in GitHub Variables
2. Request quota increase in Azure Portal

### Terraform state issues

If state is corrupted, you can import existing resources:
```bash
terraform import azurerm_resource_group.main /subscriptions/<sub>/resourceGroups/carlos-prod-rg
```
