# Carlos the Architect

![Carlos](frontend/src/assets/splash.jpg)

## How It Works

### High-Level Flow

1. **You enter requirements** in the New Blueprint view ("Tell Carlos what you need to build...").
2. **You can tune context** with:
   - Scenario preset (e.g., Public Web App, Data Pipeline, Event-driven Microservices)
   - Cost vs Performance preference
   - Compliance level
   - Reliability target
   - Design strictness (Flexible vs Strict, e.g. AWS-native, avoid K8s)
3. The **frontend sends a POST** to the backend `/design` endpoint with your text and these settings.
4. The **FastAPI backend** calls a LangGraph workflow with multiple agents:
   - Carlos (Lead Cloud Architect) drafts the initial architecture in markdown and adds a Mermaid `flowchart` diagram under the High-Level Overview.
   - Security Analyst reviews security posture.
   - Cost Optimization Specialist reviews cost posture.
   - SRE / Reliability Engineer reviews reliability/operations.
   - Chief Architecture Auditor reads all of the above and issues a final verdict.
5. The **backend returns JSON** with:
   - `design` (markdown blueprint + inline mermaid block)
   - `security_report`, `cost_report`, `reliability_report`
   - `audit_status`, `audit_report`
   - `agent_chat` (markdown transcript of the agents talking)
   - `terraform_code` (validated Terraform configuration)
6. The **frontend renders**:
   - Blueprint markdown (with the Mermaid diagram rendered inline)
   - Security Audits tab (all specialist reports + final verdict)
   - Agent Chat tab (conversation with icons per agent)
   - Analytics tab (scenario popularity, approval rates, recent blockers)
   - History tab (previous designs, persisted in localStorage)
   - **Deployment Tracker** - collect feedback on deployed designs
7. **Caching & Persistence**:
   - **Azure Cache for Redis** caches design patterns for instant responses on similar requirements
   - **Azure Cosmos DB** stores deployment feedback for analytics and future learning

---

## Project Structure

- `backend/`
  - `main.py` – FastAPI app, `/design` endpoint, CORS setup, feedback endpoints.
  - `graph.py` – LangGraph state machine and nodes (Carlos, Security, Cost, Reliability, Auditor).
  - `tasks.py` – Agent instruction prompts.
  - `cache.py` – Azure Cache for Redis integration for design pattern caching.
  - `feedback.py` – Azure Cosmos DB integration for deployment feedback tracking.
  - `requirements.txt` – Python dependencies.
- `frontend/`
  - `src/App.jsx` – Main React app, views, and UI logic.
  - `src/components/Splash.jsx` – Initial splash screen.
  - `src/components/DeploymentTracker.jsx` – Feedback collection for deployed designs.
  - `src/components/StarRating.jsx` – Interactive star rating component.
  - `vite.config.js`, `package.json` – Vite/React configuration and dependencies.
- `infra/`
  - `main.tf` – Terraform configuration for Azure resources (AKS, ACR, Redis, Cosmos DB, Document Intelligence).
  - `variables.tf` – Terraform variable definitions.
  - `outputs.tf` – Terraform outputs for CI/CD.
- `k8s/`
  - `backend-deployment.yaml` – Kubernetes deployment for backend.
  - `frontend-deployment.yaml` – Kubernetes deployment for frontend.
  - `namespace.yaml` – Kubernetes namespace configuration.

---

## Changelog & Releases

This project maintains a `CHANGELOG.md` using the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.

Changelog updates and GitHub Releases are automated using **Release Please**:

- On every push to `main`, Release Please will open (or update) a **release PR** that updates `CHANGELOG.md` and bumps the release version.
- When you merge the release PR, Release Please will create a **git tag** and a **GitHub Release** automatically.

To ensure changes are categorized correctly, use **Conventional Commits** in your commit messages or PR titles, for example:

- `feat: add new scenario presets`
- `fix: handle missing Azure OpenAI env vars`
- `chore: update dependencies`

---

## Prerequisites

- **Python** 3.9+ (virtualenv recommended)
- **Node.js** 18+ and **npm**
- An **Azure OpenAI** deployment with a chat model (e.g. GPT-4x class) and the following environment variables set for the backend:
  - `AZURE_OPENAI_ENDPOINT`
  - `AZURE_OPENAI_API_KEY`
  - `AZURE_OPENAI_DEPLOYMENT_NAME`
  - `AZURE_OPENAI_API_VERSION`

These are read in `backend/graph.py` via `os.getenv`, with `.env` loaded by `python-dotenv` in `backend/main.py`.

Create a `.env` file in `backend/` (or project root, depending on how you run it) with values like:

```bash
# Azure OpenAI (required)
AZURE_OPENAI_ENDPOINT="https://your-resource-name.openai.azure.com"
AZURE_OPENAI_API_KEY="your-key-here"
AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o"
AZURE_OPENAI_API_VERSION="2024-08-01-preview"

# Azure Cache for Redis (optional - enables design caching)
REDIS_HOST="your-redis.redis.cache.windows.net"
REDIS_PORT="6380"
REDIS_PASSWORD="your-redis-key"
REDIS_SSL="true"

# Azure Cosmos DB (optional - enables deployment feedback tracking)
COSMOSDB_ENDPOINT="https://your-cosmos.documents.azure.com:443/"
COSMOSDB_KEY="your-cosmos-key"
COSMOSDB_DATABASE="carlos-feedback"
COSMOSDB_CONTAINER="deployments"

# Azure AI Document Intelligence (optional - enables OCR for images and scanned PDFs)
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="https://your-docint.cognitiveservices.azure.com/"
AZURE_DOCUMENT_INTELLIGENCE_KEY="your-document-intelligence-key"
```

> **Note:** Redis, Cosmos DB, and Document Intelligence are optional for local development. Without them, the app uses in-memory storage (data is lost on restart) and image/scanned PDF upload is disabled.

---

## Required Python Packages

Backend dependencies are listed in `requirements.txt` and installed via `pip install -r requirements.txt`. Key packages:

- `fastapi` – web framework for the API
- `uvicorn[standard]` – ASGI server
- `python-dotenv` – loads environment variables from `.env`
- `langgraph` – orchestrates the multi-agent workflow
- `langchain` – LLM orchestration utilities
- `langchain-openai` – Azure OpenAI client bindings
- `openai` – core OpenAI client (used under the hood)
- `pydantic` – data validation and settings

---

## Backend Setup & Run

From the project root:

1. **Create and activate a virtual environment (optional but recommended):**

```bash
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\\Scripts\\activate  # Windows (PowerShell or CMD)
```

2. **Install Python dependencies:**

```bash
pip install -r requirements.txt
```

3. **Run the FastAPI app with Uvicorn:**

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- API base URL: `http://localhost:8000`
- Main endpoint: `POST /design`

If everything is correctly configured, you should see logs like:

- `Received request: { ... }`
- `Design generated, length=..., audit_status=..., ...`

---

## Frontend Setup & Run

In a separate terminal, from the project root:

1. **Install frontend dependencies:**

```bash
cd frontend
npm install
```

This installs the required npm packages, including:

- `react`, `react-dom` – React UI library
- `vite` – dev server and bundler
- `react-markdown` – render blueprint and reports as markdown
- `remark-gfm` – GitHub-flavored markdown support
- `mermaid` – render architecture diagrams from Mermaid code blocks
- `lucide-react` – icon set for the UI
- `@tailwindcss/typography`, `@tailwindcss/vite`, `tailwindcss` – styling utilities

2. **Run the Vite dev server:**

```bash
npm run dev
```

By default the app runs on `http://localhost:5173` (and CORS is configured in the backend to allow `5173` and `5174`).

Open your browser at:

```text
http://localhost:5173
```

You should see the Carlos AI splash screen, then the main dashboard.

---

## Using the App

1. **Open New Blueprint tab** (default when you land).
2. **Describe your system** in natural language.
3. Optionally **choose presets and priorities** (scenario, cost vs performance, compliance, reliability, design strictness).
4. Click **Send** to ask Carlos.
5. Watch the **Blueprint** render, including:
   - High-level text sections
   - Inline **Mermaid architecture diagram**
6. Switch to **Security Audits** to read specialist reports and the Chief Auditor verdict.
7. Switch to **Agent Chat** to see the conversation between Carlos and the other agents.
8. Use **Cloud History** to reopen previous designs.
9. Use **Analytics** to see:
   - How many designs you’ve created
   - Approval vs Needs Revision counts
   - Scenario popularity
   - Recent blockers from the auditor
10. Click **Download Blueprint Package** on the Blueprint tab to save a markdown file containing:
    - Requirements
    - Settings (scenario & priorities)
    - Design
    - All specialist reports
    - Final verdict
    - Agent conversation

---

## Authentication & User Management

Carlos includes a complete authentication system with local accounts and OAuth support.

### User Registration
- Users can register with username/password on the login page
- OAuth login with Google and GitHub (when configured)

### Admin Dashboard
Admins have access to a dedicated dashboard with:

- **Overview Tab**: Audit statistics including total events, unique users, error counts, and events by severity/action
- **Audit Logs Tab**: Searchable and filterable logs of all API requests with export to JSON/CSV
- **User Management Tab**: View all users, promote/demote admins, enable/disable accounts, and delete users

To access the admin dashboard, log in as an admin user and click the shield icon in the sidebar.

### Default Admin Account
On first startup, a default admin account is created:
- Username: `admin` (configurable via `ADMIN_USERNAME`)
- Password: `carlos-admin-2024` (configurable via `ADMIN_PASSWORD`)

**Important:** Change the default admin password in production by setting `ADMIN_PASSWORD` environment variable.

---

## Troubleshooting

- **Backend 500 or `error` in response**
  - Check that your Azure OpenAI environment variables are set correctly.
  - Confirm the deployment name and API version match what you actually provisioned.

- **CORS / network issues**
  - Frontend expects the backend at `http://localhost:8000` (configurable via `VITE_BACKEND_URL`).
  - CORS in `backend/main.py` allows origins specified in `ALLOWED_ORIGINS` environment variable.
  - Default CORS origins: `http://localhost:5173` and `http://localhost:5174`.
  - For production, set both `VITE_BACKEND_URL` (build-time) and `ALLOWED_ORIGINS` (runtime).

- **"Cannot connect to server" error in production**
  - Ensure `VITE_BACKEND_URL` includes the port (e.g., `http://20.245.72.209:8000`, not `http://20.245.72.209`).
  - `VITE_BACKEND_URL` is a **build-time** variable - changes require rebuilding the frontend.
  - Ensure `ALLOWED_ORIGINS` on the backend includes your frontend URL.

- **No designs in history after refresh**
  - History is stored in `localStorage` (`designHistory` key); clearing browser storage will remove it.

- **Mermaid diagram not rendering**
  - The app tries to render the first ```mermaid``` block in the blueprint.
  - If Mermaid detects a syntax error, the UI will show a small warning instead of raw error text and log details to the browser console.

---

## Tech Stack

- **Backend**
  - FastAPI
  - LangGraph
  - Azure OpenAI (AzureChatOpenAI)
  - Azure Cache for Redis (design caching)
  - Azure Cosmos DB (feedback persistence)
  - Azure AI Document Intelligence (OCR for images and scanned PDFs)

- **Frontend**
  - React 18 + Vite
  - `react-markdown` + `remark-gfm`
  - `mermaid` for diagrams
  - `lucide-react` for icons

- **Infrastructure**
  - Azure Kubernetes Service (AKS)
  - Azure Container Registry (ACR)
  - Terraform (Infrastructure as Code)
  - GitHub Actions (CI/CD)

---

## Deployment

Carlos includes production-ready deployment infrastructure:

1. **Terraform** provisions Azure resources (AKS, ACR, Redis, Cosmos DB, Document Intelligence)
2. **GitHub Actions** builds Docker images and deploys to AKS on push to `main`
3. **Kubernetes** manages auto-scaling and health checks

All Azure service credentials (Redis, Cosmos DB, Document Intelligence) are automatically extracted from Terraform outputs and injected into Kubernetes secrets during deployment.

See `.github/workflows/deploy-azure.yml` for the complete CI/CD pipeline.

### Required GitHub Secrets for Deployment

**Azure Authentication:**
- `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_SUBSCRIPTION_ID`, `AZURE_TENANT_ID`
- `AZURE_CREDENTIALS` (service principal JSON)

**Azure OpenAI:**
- `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_DEPLOYMENT_NAME` (default: `gpt-4o`)
- `AZURE_OPENAI_MINI_DEPLOYMENT_NAME` (default: `gpt-4o-mini`, for cost optimization)

**Frontend/Backend Configuration:**
- `VITE_BACKEND_URL` - Backend API URL for frontend (e.g., `http://20.245.72.209:8000`)
- `ALLOWED_ORIGINS` - CORS allowed origins (e.g., `http://20.245.72.209,http://localhost:5173`)
- `OAUTH_REDIRECT_BASE` - Frontend URL for OAuth redirects (e.g., `http://20.245.72.209`)

**Authentication:**
- `JWT_SECRET_KEY` - Secret key for JWT token signing
- `ADMIN_PASSWORD` - Password for default admin account (change from default!)

**OAuth (optional):**
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` - For Google OAuth
- `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` - For GitHub OAuth
