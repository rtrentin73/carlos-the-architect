# Carlos the Architect: Agentic SDLC

## Overview

Carlos the Architect implements a **multi-agent Software Development Lifecycle (SDLC)** for cloud infrastructure design. The system uses 11 specialized AI agents orchestrated through LangGraph to automate the complete journey from requirements gathering to production-ready Terraform code, with **historical learning** from past deployment feedback.

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                           AGENTIC SDLC PIPELINE                                    │
├───────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  REQUIREMENTS ──► LEARNING ──► DESIGN ──► ANALYSIS ──► REVIEW ──► DECISION ──► CODE │
│       │              │           │           │           │           │          │ │
│  [Gathering]   [Historical]  [Carlos]   [Security]  [Auditor]  [Recommender] [TF] │
│       │         [Learning]   [Ronei]     [Cost]         │           │          │ │
│       │              │          ║        [SRE]          │           │          │ │
│       ▼              ▼          ▼           ▼           ▼           ▼          ▼ │
│   Questions     Context    2 Designs   3 Reports    Approval   Selection    IaC  │
│              from feedback                                                        │
└───────────────────────────────────────────────────────────────────────────────────┘
```

## SDLC Phases Mapped to Agents

| SDLC Phase | Agent(s) | Output | Purpose |
|------------|----------|--------|---------|
| **1. Requirements** | Requirements Gathering | Clarifying questions | Understand user needs |
| **2. Learning** | Historical Learning | Context from past designs | Learn from deployment feedback |
| **3. Design** | Carlos + Ronei (parallel) | 2 architecture designs | Competitive design generation |
| **4. Analysis** | Security, Cost, SRE (parallel) | 3 specialist reports | Multi-dimensional review |
| **5. Review** | Chief Auditor | Approval decision | Quality gate |
| **6. Decision** | Design Recommender | Final recommendation | Select best design |
| **7. Implementation** | Terraform Coder | Infrastructure-as-Code | Production-ready output |

---

## Agent Architecture

### The 11 Agents

```
┌─────────────────────────────────────────────────────────────────┐
│                      AGENT HIERARCHY                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  TIER 1: PRIMARY ARCHITECTS (GPT-4o)                           │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │     CARLOS      │    │     RONEI       │                    │
│  │  Conservative   │ vs │   Innovative    │                    │
│  │  AWS-native     │    │   Kubernetes    │                    │
│  │  temp: 0.7      │    │   temp: 0.9     │                    │
│  └─────────────────┘    └─────────────────┘                    │
│           ▲                     ▲                              │
│           └───────┬─────────────┘                              │
│                   │                                            │
│  TIER 0.5: HISTORICAL LEARNING (No LLM - Data Query)          │
│  ┌─────────────────────────────────────────┐                   │
│  │         Historical Learning              │                   │
│  │   (Queries Cosmos DB for past feedback)  │                   │
│  └─────────────────────────────────────────┘                   │
│                                                                 │
│  TIER 2: SPECIALIST ANALYSTS (GPT-4o-mini)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│  │ Security │  │   Cost   │  │   SRE    │                      │
│  │ Analyst  │  │ Analyst  │  │ Engineer │                      │
│  └──────────┘  └──────────┘  └──────────┘                      │
│                                                                 │
│  TIER 3: DECISION MAKERS (GPT-4o)                              │
│  ┌──────────┐  ┌───────────┐  ┌───────────┐                    │
│  │ Auditor  │  │Recommender│  │ Terraform │                    │
│  │  Chief   │  │  Design   │  │   Coder   │                    │
│  └──────────┘  └───────────┘  └───────────┘                    │
│                                                                 │
│  TIER 0: REQUIREMENTS (GPT-4o-mini)                            │
│  ┌───────────────────┐                                         │
│  │    Requirements   │                                         │
│  │     Gathering     │                                         │
│  └───────────────────┘                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Details

#### 1. Requirements Gathering Agent
- **Model:** GPT-4o-mini (cost-optimized)
- **Role:** Initial clarification of user needs
- **Output:** 3-5 clarifying questions about:
  - Workload characteristics (traffic, data volume, users)
  - Performance requirements (latency, throughput, SLAs)
  - Security & compliance needs
  - Budget constraints
  - Deployment preferences

#### 1.5 Historical Learning Node
- **Model:** None (data query only)
- **Role:** Learn from past deployment feedback
- **Data Source:** Azure Cosmos DB (deployment feedback)
- **Process:**
  1. Extract keywords from refined requirements
  2. Query similar past designs from feedback store
  3. Categorize feedback by success (4-5 stars) vs problems (1-2 stars)
  4. Extract patterns that worked well
  5. Extract warnings from problematic deployments
- **Output:** Formatted context injected into design prompts
- **Graceful Degradation:** Returns empty context on failure (5s timeout)

#### 2. Carlos (Lead Cloud Architect)
- **Model:** GPT-4o (main pool)
- **Temperature:** 0.7 (balanced)
- **Personality:** Pragmatic, conservative, dog-themed
- **Focus:** AWS-native managed services, proven patterns, simplicity
- **Output:** Complete architecture design with Mermaid diagram
- **Philosophy:** "If it ain't broke, don't fix it"

#### 3. Ronei (Rival Architect - "The Cat")
- **Model:** GPT-4o (ronei pool)
- **Temperature:** 0.9 (more creative)
- **Personality:** Cutting-edge, competitive, cat-themed
- **Focus:** Kubernetes, microservices, serverless, service mesh
- **Output:** Alternative architecture design with Mermaid diagram
- **Philosophy:** "Innovation drives excellence"

#### 4. Security Analyst
- **Model:** GPT-4o-mini
- **Focus Areas:**
  - Network exposure & segmentation
  - Identity & access management
  - Data encryption (transit + rest)
  - Logging & monitoring
  - Incident response readiness

#### 5. Cost Optimization Specialist
- **Model:** GPT-4o-mini
- **Focus Areas:**
  - Major cost drivers identification
  - Reserved instances / savings plans
  - Spot/preemptible instance opportunities
  - Storage lifecycle & archival
  - FinOps best practices

#### 6. Site Reliability Engineer (SRE)
- **Model:** GPT-4o-mini
- **Focus Areas:**
  - Failure scenarios & blast radius
  - Capacity planning & auto-scaling
  - Observability (metrics, logs, traces)
  - Health checks & alerting
  - Operational runbooks

#### 7. Chief Architecture Auditor
- **Model:** GPT-4o (main pool)
- **Role:** Final quality gate
- **Decision:** APPROVED or NEEDS REVISION
- **Output:** Executive summary with strengths and required changes

#### 8. Design Recommender
- **Model:** GPT-4o (main pool)
- **Role:** Select the winning design
- **Decision:** Must choose exactly one (Carlos OR Ronei)
- **Output:** Recommendation with justification and tradeoffs

#### 9. Terraform Coder
- **Model:** GPT-4o (main pool)
- **Role:** Generate production-ready infrastructure-as-code
- **Output:**
  - `main.tf` - Resource definitions
  - `variables.tf` - Input variables
  - `outputs.tf` - Output values
  - `versions.tf` - Provider configuration
  - Deployment instructions

---

## Workflow Graph

### LangGraph State Machine

```
                              START
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Has User Answers?    │
                    └───────────────────────┘
                           │         │
                          NO        YES
                           │         │
                           ▼         │
              ┌────────────────────┐ │
              │   Requirements     │ │
              │    Gathering       │ │
              └────────────────────┘ │
                           │         │
                           ▼         │
              ┌────────────────────┐ │
              │ Clarification      │ │
              │ Needed?            │ │
              └────────────────────┘ │
                    │         │      │
                   YES       NO      │
                    │         │      │
                    ▼         ▼      ▼
                  END    ┌─────────────────┐
            (wait for    │     Refine      │
             answers)    │  Requirements   │
                         └─────────────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │   HISTORICAL    │
                         │    LEARNING     │
                         │ (query feedback)│
                         └─────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
           ┌──────────────┐            ┌──────────────┐
           │    CARLOS    │            │    RONEI     │
           │   (design)   │  PARALLEL  │   (design)   │
           │ +historical  │            │ +historical  │
           │   context    │            │   context    │
           └──────────────┘            └──────────────┘
                    │                           │
                    └─────────────┬─────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
              ▼                   ▼                   ▼
       ┌────────────┐      ┌────────────┐      ┌────────────┐
       │  SECURITY  │      │    COST    │      │    SRE     │
       │  ANALYST   │      │  ANALYST   │      │  ENGINEER  │
       └────────────┘      └────────────┘      └────────────┘
              │                   │                   │
              └───────────────────┼───────────────────┘
                                  │
                                  ▼
                         ┌──────────────┐
                         │   AUDITOR    │
                         │   (review)   │
                         └──────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
               APPROVED                   NEEDS REVISION
                    │                           │
                    ▼                           │
           ┌──────────────┐                     │
           │ RECOMMENDER  │                     │
           │  (decision)  │                     │
           └──────────────┘                     │
                    │                           │
                    ▼                           │
           ┌──────────────┐                     │
           │  TERRAFORM   │◄────────────────────┘
           │    CODER     │      (revision loop)
           └──────────────┘
                    │
                    ▼
                   END
```

### Parallel Execution Points

The workflow optimizes performance through strategic parallelization:

1. **Design Phase:** Carlos and Ronei work simultaneously
2. **Analysis Phase:** Security, Cost, and SRE analysts work in parallel

```
Sequential Time:  ████████████████████████████████████  (13 LLM calls)
Parallel Time:    ████████████                          (5 effective rounds)
                  ▲
                  └── 60% faster with parallelization
```

---

## State Management

### CarlosState TypedDict

```python
class CarlosState(TypedDict):
    # Input
    requirements: str                    # Original user input
    user_answers: str                    # Answers to clarification questions

    # Requirements Phase
    refined_requirements: str            # Merged requirements + answers
    clarification_needed: bool           # Flow control flag

    # Historical Learning Phase
    historical_context: str              # Patterns from past deployments

    # Design Phase
    design_doc: str                      # Carlos' architecture
    ronei_design: str                    # Ronei's architecture
    design_tokens: list                  # Streaming tokens (Carlos)
    ronei_tokens: list                   # Streaming tokens (Ronei)

    # Analysis Phase
    security_report: str                 # Security findings
    cost_report: str                     # Cost analysis
    reliability_report: str              # SRE assessment

    # Review Phase
    audit_status: str                    # "pending" | "approved" | "needs_revision"
    audit_report: str                    # Auditor's verdict

    # Decision Phase
    recommendation: str                  # "RECOMMEND: CARLOS" | "RECOMMEND: RONEI"

    # Implementation Phase
    terraform_code: str                  # Generated IaC

    # Observability
    conversation: Annotated[str, operator.add]  # Full agent transcript
```

### State Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          STATE EVOLUTION                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  USER INPUT                                                             │
│      │                                                                  │
│      ▼                                                                  │
│  ┌─────────────────┐                                                    │
│  │  requirements   │ ─────► "Build a scalable web app on AWS"          │
│  └─────────────────┘                                                    │
│           │                                                             │
│           ▼                                                             │
│  ┌─────────────────┐                                                    │
│  │ clarification   │ ─────► true (questions generated)                 │
│  │    _needed      │                                                    │
│  └─────────────────┘                                                    │
│           │                                                             │
│           ▼                                                             │
│  ┌─────────────────┐                                                    │
│  │  user_answers   │ ─────► "Expected 10k users, $500/mo budget..."    │
│  └─────────────────┘                                                    │
│           │                                                             │
│           ▼                                                             │
│  ┌─────────────────┐                                                    │
│  │    refined_     │ ─────► Merged requirements + context              │
│  │  requirements   │                                                    │
│  └─────────────────┘                                                    │
│           │                                                             │
│     ┌─────┴─────┐                                                       │
│     ▼           ▼                                                       │
│  ┌────────┐ ┌────────┐                                                  │
│  │design_ │ │ ronei_ │ ─────► Two complete architecture docs           │
│  │  doc   │ │ design │        with Mermaid diagrams                    │
│  └────────┘ └────────┘                                                  │
│        │         │                                                      │
│        └────┬────┘                                                      │
│             │                                                           │
│     ┌───────┼───────┐                                                   │
│     ▼       ▼       ▼                                                   │
│  ┌──────┐┌──────┐┌──────┐                                               │
│  │secur-││cost_ ││relia-│ ─────► Three specialist reports              │
│  │ity_  ││report││bility│                                               │
│  │report││      ││_rep. │                                               │
│  └──────┘└──────┘└──────┘                                               │
│        │    │       │                                                   │
│        └────┼───────┘                                                   │
│             ▼                                                           │
│  ┌─────────────────┐                                                    │
│  │  audit_status   │ ─────► "approved" or "needs_revision"             │
│  │  audit_report   │                                                    │
│  └─────────────────┘                                                    │
│             │                                                           │
│             ▼                                                           │
│  ┌─────────────────┐                                                    │
│  │ recommendation  │ ─────► "RECOMMEND: CARLOS" (with justification)   │
│  └─────────────────┘                                                    │
│             │                                                           │
│             ▼                                                           │
│  ┌─────────────────┐                                                    │
│  │ terraform_code  │ ─────► main.tf, variables.tf, outputs.tf, etc.    │
│  └─────────────────┘                                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Connection Pooling Strategy

### Three-Tier LLM Pool Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      LLM CONNECTION POOLS                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  MAIN POOL (10 connections)                                             │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Model: GPT-4o  │  Temperature: 0.7  │  Agents: Carlos,         │   │
│  │                 │                     │  Auditor, Recommender,   │   │
│  │                 │                     │  Terraform Coder         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  RONEI POOL (5 connections)                                             │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Model: GPT-4o  │  Temperature: 0.9  │  Agents: Ronei only      │   │
│  │                 │  (more creative)   │                          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  MINI POOL (10 connections)                                             │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Model: GPT-4o  │  Temperature: 0.7  │  Agents: Requirements,   │   │
│  │  -mini (cheap)  │                     │  Security, Cost, SRE     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  Benefits:                                                              │
│  • 30-50% latency reduction (pre-warmed connections)                   │
│  • 70%+ cost savings (mini pool for simple analysis)                   │
│  • Parallel execution without connection bottlenecks                    │
│  • Graceful degradation (temporary connections if pool exhausted)      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Pool Usage Pattern

```python
# Context manager ensures proper acquisition/release
async with pool.get_main_llm() as llm:
    response = await llm.ainvoke(messages)
    # Connection automatically returned to pool
```

---

## Streaming & Real-Time Feedback

### Server-Sent Events (SSE)

The `/design-stream` endpoint provides real-time updates:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      SSE EVENT STREAM                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Time ──────────────────────────────────────────────────────────►      │
│                                                                         │
│  ┌──────────┐  ┌─────────────────────┐  ┌──────────────┐               │
│  │agent_    │  │      token          │  │agent_        │               │
│  │start     │  │   (streaming)       │  │complete      │               │
│  │"carlos"  │  │ "Here's my design"  │  │"carlos"      │               │
│  └──────────┘  └─────────────────────┘  └──────────────┘               │
│                                                                         │
│  ┌──────────┐  ┌─────────────────────┐  ┌──────────────┐               │
│  │agent_    │  │    field_update     │  │agent_        │               │
│  │start     │  │ "security_report"   │  │complete      │               │
│  │"security"│  │                     │  │"security"    │               │
│  └──────────┘  └─────────────────────┘  └──────────────┘               │
│                                                                         │
│                                          ┌──────────────┐               │
│                                          │   complete   │               │
│                                          │ {full state} │               │
│                                          └──────────────┘               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Event Types

| Event | Payload | Purpose |
|-------|---------|---------|
| `agent_start` | `{agent, timestamp}` | Agent began processing |
| `token` | `{agent, content}` | Streaming token from LLM |
| `field_update` | `{field, content}` | State field updated |
| `agent_complete` | `{agent, timestamp}` | Agent finished |
| `complete` | `{summary: state}` | Workflow complete |

---

## Historical Learning System

### Feedback-Driven Improvement

Carlos learns from past deployment outcomes stored in Azure Cosmos DB:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    HISTORICAL LEARNING FLOW                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  NEW REQUEST                          PAST FEEDBACK (Cosmos DB)         │
│  "Build an e-commerce                 ┌─────────────────────────┐      │
│   platform on AWS"                    │ Design A: ⭐⭐⭐⭐⭐ (5.0)   │      │
│        │                              │ "API Gateway + Lambda    │      │
│        ▼                              │  worked great for our    │      │
│  ┌─────────────────┐                  │  traffic patterns"       │      │
│  │ Extract Keywords│                  ├─────────────────────────┤      │
│  │ [e-commerce,    │                  │ Design B: ⭐⭐ (2.0)      │      │
│  │  platform, aws] │                  │ "Kubernetes was overkill │      │
│  └────────┬────────┘                  │  for our small team"     │      │
│           │                           └─────────────────────────┘      │
│           ▼                                      │                      │
│  ┌─────────────────┐                             │                      │
│  │ Query Similar   │◄────────────────────────────┘                      │
│  │ Past Designs    │                                                    │
│  └────────┬────────┘                                                    │
│           │                                                             │
│           ▼                                                             │
│  ┌─────────────────┐                                                    │
│  │ Generate Context│                                                    │
│  │ "Patterns that  │                                                    │
│  │  worked: ..."   │                                                    │
│  │ "Patterns to    │                                                    │
│  │  avoid: ..."    │                                                    │
│  └────────┬────────┘                                                    │
│           │                                                             │
│           ▼                                                             │
│  ┌─────────────────┐                                                    │
│  │ Inject into     │                                                    │
│  │ Carlos & Ronei  │                                                    │
│  │ Design Prompts  │                                                    │
│  └─────────────────┘                                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Learning Context Format

The historical context is formatted as markdown and prepended to design prompts:

```markdown
## Historical Learning from Past Deployments

Based on 5 similar past designs:

### Patterns That Worked Well (4-5 star deployments):
- API Gateway + Lambda combination (avg rating: 4.8/5) - appeared in 3 deployments
- Aurora Serverless for variable workloads (avg rating: 4.5/5) - appeared in 2 deployments

### Patterns to Avoid:
- **Warning**: Self-managed Kubernetes clusters - caused problems in 2 deployments
- **Warning**: Manual scaling without CloudWatch alarms - caused problems in 1 deployment

### Common Issues Encountered:
- cold start latency in serverless (3 occurrences)
- database connection pooling (2 occurrences)

Apply these learnings while designing, but use your judgment - every project is different.
```

### Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MIN_FEEDBACK_FOR_LEARNING` | 3 | Minimum records needed to include context |
| `HIGH_RATING_THRESHOLD` | 4 | Minimum rating for "successful" patterns |
| `LOW_RATING_THRESHOLD` | 2 | Maximum rating for "problematic" patterns |
| `MAX_HISTORICAL_RESULTS` | 20 | Maximum feedback records to analyze |
| `LEARNING_TIMEOUT_SECONDS` | 5.0 | Timeout for database queries |

---

## API Endpoints

### Design Endpoints

```
POST /design              Synchronous full workflow
POST /design-stream       Streaming with SSE events

Request Body:
{
  "text": "Build a web app...",        // User requirements
  "scenario": "custom",                 // Preset scenario
  "priorities": {
    "cost_performance": "balanced",
    "compliance_level": "standard",
    "reliability_level": "normal"
  },
  "user_answers": "10k users..."        // Optional: answers to questions
}
```

### Document Processing

```
POST /upload-document     Upload document for async processing
GET  /documents/{task_id} Check processing status
GET  /documents           List user's document tasks
```

### Health & Auth

```
GET  /health              Pool statistics and status
POST /auth/register       Create user account
POST /auth/login          Get JWT token
GET  /auth/me             Current user info
```

---

## File Structure

```
backend/
├── graph.py              # LangGraph workflow definition
├── tasks.py              # Agent prompts and instructions
├── llm_pool.py           # Connection pooling implementation
├── historical_learning.py # Historical learning from feedback
├── feedback.py           # Deployment feedback storage (Cosmos DB)
├── cache.py              # Design caching (Azure Redis)
├── main.py               # FastAPI server and endpoints
├── auth.py               # Authentication system
├── document_parser.py    # Document text extraction
└── document_tasks.py     # Async task management

frontend/
└── src/
    ├── App.jsx           # Main application UI
    └── components/       # React components
```

---

## Performance Characteristics

### Latency Breakdown (Typical)

| Phase | Duration | Parallelization |
|-------|----------|-----------------|
| Requirements | 2-3s | Sequential |
| Design (Carlos + Ronei) | 15-25s | Parallel |
| Analysis (Security + Cost + SRE) | 5-10s | Parallel |
| Audit | 3-5s | Sequential |
| Recommendation | 2-3s | Sequential |
| Terraform Generation | 10-20s | Sequential |
| **Total** | **40-70s** | **60% faster than sequential** |

### Cost Optimization

| Agent Type | Model | Cost/1K tokens | Usage |
|------------|-------|----------------|-------|
| Complex (Carlos, Auditor, etc.) | GPT-4o | $0.015 | ~40% of calls |
| Simple (Security, Cost, SRE) | GPT-4o-mini | $0.00015 | ~60% of calls |
| **Savings** | | | **~70% cost reduction** |

---

## Why Agentic SDLC?

### Traditional SDLC vs. Agentic SDLC

| Aspect | Traditional | Agentic (Carlos) |
|--------|-------------|------------------|
| Design generation | Single architect | Competitive dual-architect |
| Analysis | Sequential reviews | Parallel specialist analysis |
| Quality gate | Manual approval | Automated audit agent |
| Code generation | Manual IaC writing | Automated Terraform |
| Feedback loop | Days/weeks | Seconds (revision loop) |
| Consistency | Variable | Deterministic prompts |

### Benefits

1. **Speed:** 40-70 seconds vs. hours/days of manual work
2. **Quality:** Multi-perspective analysis catches more issues
3. **Consistency:** Same rigorous process every time
4. **Cost:** Optimized LLM usage with tiered pools
5. **Transparency:** Full conversation transcript for audit trail
6. **Iteration:** Built-in revision loop for continuous improvement

---

## Future Enhancements

- [ ] **Validation Agent:** Pre-flight checks before Terraform generation
- [x] **Structured Outputs:** JSON schema enforcement for reports
- [x] **Caching:** Design pattern caching with Azure Cache for Redis
- [x] **Feedback Loop:** Learn from deployment outcomes (historical learning)
- [ ] **Multi-Cloud:** Azure, GCP support alongside AWS
- [ ] **Cost Estimation:** Real-time pricing integration

---

## References

- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [ROADMAP.md](../ROADMAP.md) - Project roadmap and future plans
- [architecture-diagram.md](../architecture-diagram.md) - System architecture diagrams
- [CONNECTION_POOLING.md](../backend/CONNECTION_POOLING.md) - Pool implementation details
- [ASYNC_DOCUMENT_PROCESSING.md](../backend/ASYNC_DOCUMENT_PROCESSING.md) - Document upload system
