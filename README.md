# Carlos the Architect

![Carlos](frontend/src/assets/splash.jpg)

git remote set-url origin https://github.com/yourusername/carlos-the-architect.git
---

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
6. The **frontend renders**:
   - Blueprint markdown (with the Mermaid diagram rendered inline)
   - Security Audits tab (all specialist reports + final verdict)
   - Agent Chat tab (conversation with icons per agent)
   - Analytics tab (scenario popularity, approval rates, recent blockers)
   - History tab (previous designs, persisted in localStorage)

---

## Project Structure

- `backend/`
  - `main.py` – FastAPI app, `/design` endpoint, CORS setup.
  - `graph.py` – LangGraph state machine and nodes (Carlos, Security, Cost, Reliability, Auditor).
  - `tasks.py` – Agent instruction prompts.
  - `requirements.txt` (at project root) – Python dependencies.
- `frontend/`
  - `src/App.jsx` – Main React app, views, and UI logic.
  - `src/components/Splash.jsx` – Initial splash screen.
  - `vite.config.js`, `package.json` – Vite/React configuration and dependencies.

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
AZURE_OPENAI_ENDPOINT="https://your-resource-name.openai.azure.com"
AZURE_OPENAI_API_KEY="your-key-here"
AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o"
AZURE_OPENAI_API_VERSION="2024-08-01-preview"
```

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

## Troubleshooting

- **Backend 500 or `error` in response**
  - Check that your Azure OpenAI environment variables are set correctly.
  - Confirm the deployment name and API version match what you actually provisioned.

- **CORS / network issues**
  - Frontend expects the backend at `http://localhost:8000`.
  - CORS in `backend/main.py` allows `http://localhost:5173` and `http://localhost:5174`.

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

- **Frontend**
  - React 18 + Vite
  - `react-markdown` + `remark-gfm`
  - `mermaid` for diagrams
  - `lucide-react` for icons

This README describes the current local development flow. If you plan to deploy Carlos the Architect, you’ll likely want to add:

- A production ASGI server configuration (e.g., gunicorn + uvicorn workers)
- A static build/deploy pipeline for the Vite frontend
- Secure handling of Azure OpenAI credentials (e.g., environment-specific config, key vaults).
