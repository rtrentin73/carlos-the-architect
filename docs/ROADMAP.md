# Carlos Enterprise Roadmap

## Vision

Transform Carlos from a specialized cloud architecture design tool into an **enterprise-grade, multi-domain AI automation platform** while maintaining its core strengths in architecture design and cost optimization.

---

## Current State (v1.1)

**Strengths:**
- ✅ Specialized domain expertise (cloud architecture)
- ✅ Cost-optimized LLM usage (50-70% savings)
- ✅ Competitive design approach (Carlos vs Ronei)
- ✅ Real-time streaming UX
- ✅ Document upload and requirements extraction
- ✅ Interactive clarification loops
- ✅ Terraform code generation with validation
- ✅ **Design pattern caching** (Azure Cache for Redis) - instant responses for similar requirements
- ✅ **Deployment feedback loop** (Azure Cosmos DB) - track deployment outcomes and user satisfaction
- ✅ **Azure Kubernetes Service (AKS)** deployment with auto-scaling
- ✅ **GitHub Actions CI/CD** pipeline with Terraform infrastructure-as-code
- ✅ **OAuth authentication** (Google & GitHub) - optional social login with graceful degradation
- ✅ **Production audit logs** - comprehensive request/response auditing with admin dashboard
- ✅ **Historical learning from feedback data** - designs now incorporate patterns from successful past deployments

**Limitations:**
- ❌ Fixed orchestration pattern (hard-coded LangGraph DAG)
- ❌ Limited to architecture design domain

---

## Roadmap Phases

### Phase 1: Foundation - Data Persistence & Observability (Q1 2026)
**Goal:** Establish data persistence and observability infrastructure

### Phase 2: Enterprise Reliability (Q2 2026)
**Goal:** Auto-scaling, high availability, and production-ready operations

### Phase 3: Learning & Intelligence (Q3 2026)
**Goal:** Historical learning from past designs and user feedback

### Phase 4: Flexible Orchestration (Q4 2026)
**Goal:** Dynamic, user-configurable agent workflows

### Phase 5: Cross-Domain Expansion (Q1 2027)
**Goal:** Extend beyond cloud architecture to multiple domains

### Phase 6: Enterprise Governance (Q2 2027)
**Goal:** Production audit, compliance, and organizational controls

---

## Phase 1: Foundation - Data Persistence & Observability

**Duration:** 8-10 weeks

### 1.1 Database Integration (Weeks 1-3)

**Objective:** Add Azure Cosmos DB for workflow history and state persistence

**Implementation:**

#### Backend Changes

1. **Add Cosmos DB Client** ([backend/database.py](backend/database.py))
```python
from azure.cosmos import CosmosClient, PartitionKey
import os

class CarlosDatabase:
    def __init__(self):
        endpoint = os.getenv("COSMOS_ENDPOINT")
        key = os.getenv("COSMOS_KEY")
        self.client = CosmosClient(endpoint, key)
        self.database = self.client.get_database_client("carlos-db")

        # Containers
        self.designs = self.database.get_container_client("designs")
        self.users = self.database.get_container_client("users")
        self.analytics = self.database.get_container_client("analytics")

    async def save_design(self, user_id: str, design_data: dict):
        """Save design with full workflow history"""
        document = {
            "id": design_data["design_id"],
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "requirements": design_data["requirements"],
            "refined_requirements": design_data["refined_requirements"],
            "carlos_design": design_data["carlos_design"],
            "ronei_design": design_data["ronei_design"],
            "security_report": design_data["security_report"],
            "cost_report": design_data["cost_report"],
            "reliability_report": design_data["reliability_report"],
            "audit_report": design_data["audit_report"],
            "recommendation": design_data["recommendation"],
            "terraform_code": design_data["terraform_code"],
            "agent_execution_log": design_data["agent_log"],
            "total_tokens": design_data["total_tokens"],
            "total_cost": design_data["total_cost"],
            "execution_time_ms": design_data["execution_time_ms"]
        }
        return self.designs.upsert_item(document)

    async def get_user_history(self, user_id: str, limit: int = 50):
        """Retrieve user's design history"""
        query = "SELECT * FROM c WHERE c.user_id = @user_id ORDER BY c.timestamp DESC OFFSET 0 LIMIT @limit"
        parameters = [
            {"name": "@user_id", "value": user_id},
            {"name": "@limit", "value": limit}
        ]
        return list(self.designs.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))

    async def search_similar_requirements(self, requirements: str, limit: int = 5):
        """Search for similar past designs (using vector search in future)"""
        # Phase 1: Simple text search
        # Phase 3: Upgrade to vector embeddings with Cosmos DB vector search
        query = """
        SELECT * FROM c
        WHERE CONTAINS(c.requirements, @search_term)
        ORDER BY c.timestamp DESC
        OFFSET 0 LIMIT @limit
        """
        # Simplified for now - will add semantic search later
        pass
```

2. **Update State to Track Metadata** ([backend/graph.py](backend/graph.py))
```python
class CarlosState(TypedDict):
    # Existing fields...

    # New metadata fields
    design_id: str  # Unique ID for this design
    user_id: str
    start_time: float
    end_time: float
    total_tokens: dict  # {"gpt-4o": 1000, "gpt-4o-mini": 500}
    total_cost: float
    agent_execution_log: list  # Detailed log of each agent execution
```

3. **Add Telemetry Tracking** ([backend/telemetry.py](backend/telemetry.py))
```python
import time
from typing import Optional
from dataclasses import dataclass, field

@dataclass
class AgentExecutionMetrics:
    agent_name: str
    start_time: float
    end_time: Optional[float] = None
    tokens_used: int = 0
    model: str = ""
    success: bool = True
    error: Optional[str] = None

    def duration_ms(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0

class TelemetryTracker:
    def __init__(self):
        self.agent_metrics: list[AgentExecutionMetrics] = []
        self.design_start_time = time.time()

    def track_agent_start(self, agent_name: str) -> AgentExecutionMetrics:
        metric = AgentExecutionMetrics(
            agent_name=agent_name,
            start_time=time.time()
        )
        self.agent_metrics.append(metric)
        return metric

    def track_agent_complete(self, metric: AgentExecutionMetrics, tokens: int, model: str):
        metric.end_time = time.time()
        metric.tokens_used = tokens
        metric.model = model

    def get_summary(self) -> dict:
        total_time = time.time() - self.design_start_time
        return {
            "total_duration_ms": total_time * 1000,
            "agent_executions": [
                {
                    "agent": m.agent_name,
                    "duration_ms": m.duration_ms(),
                    "tokens": m.tokens_used,
                    "model": m.model,
                    "success": m.success
                }
                for m in self.agent_metrics
            ],
            "total_tokens": sum(m.tokens_used for m in self.agent_metrics),
            "total_cost": self._calculate_cost()
        }

    def _calculate_cost(self) -> float:
        # GPT-4o: $2.50/1M input, $10/1M output (average $6.25/1M)
        # GPT-4o-mini: $0.15/1M input, $0.60/1M output (average $0.375/1M)
        cost = 0.0
        for m in self.agent_metrics:
            if "mini" in m.model:
                cost += (m.tokens_used / 1_000_000) * 0.375
            else:
                cost += (m.tokens_used / 1_000_000) * 6.25
        return cost
```

#### Infrastructure Changes

4. **Add Cosmos DB to Terraform** ([infra/main.tf](infra/main.tf))
```hcl
resource "azurerm_cosmosdb_account" "carlos" {
  name                = "${var.project_name}-cosmos-${var.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"

  consistency_policy {
    consistency_level = "Session"
  }

  geo_location {
    location          = azurerm_resource_group.main.location
    failover_priority = 0
  }

  backup {
    type                = "Periodic"
    interval_in_minutes = 240
    retention_in_hours  = 8
  }
}

resource "azurerm_cosmosdb_sql_database" "carlos" {
  name                = "carlos-db"
  resource_group_name = azurerm_cosmosdb_account.carlos.resource_group_name
  account_name        = azurerm_cosmosdb_account.carlos.name
  throughput          = 400  # Start small, auto-scale later
}

resource "azurerm_cosmosdb_sql_container" "designs" {
  name                = "designs"
  resource_group_name = azurerm_cosmosdb_account.carlos.resource_group_name
  account_name        = azurerm_cosmosdb_account.carlos.name
  database_name       = azurerm_cosmosdb_sql_database.carlos.name
  partition_key_path  = "/user_id"
  throughput          = 400

  indexing_policy {
    indexing_mode = "consistent"

    included_path {
      path = "/*"
    }

    excluded_path {
      path = "/\"_etag\"/?"
    }
  }
}

output "cosmos_endpoint" {
  value = azurerm_cosmosdb_account.carlos.endpoint
}

output "cosmos_key" {
  value     = azurerm_cosmosdb_account.carlos.primary_key
  sensitive = true
}
```

5. **Update Kubernetes Deployment** ([k8s/backend-deployment.yaml](k8s/backend-deployment.yaml))
```yaml
env:
  # Existing Azure OpenAI vars...

  # Add Cosmos DB configuration
  - name: COSMOS_ENDPOINT
    valueFrom:
      secretKeyRef:
        name: carlos-secrets
        key: cosmos-endpoint
  - name: COSMOS_KEY
    valueFrom:
      secretKeyRef:
        name: carlos-secrets
        key: cosmos-key
```

### 1.2 Observability & Monitoring (Weeks 4-6)

**Objective:** Add comprehensive logging, metrics, and distributed tracing

**Implementation:**

1. **Add Azure Application Insights** ([backend/observability.py](backend/observability.py))
```python
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer
from opencensus.ext.flask.flask_middleware import FlaskMiddleware
import logging
import os

class CarlosObservability:
    def __init__(self, app):
        self.connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")

        # Structured logging
        logger = logging.getLogger(__name__)
        logger.addHandler(AzureLogHandler(connection_string=self.connection_string))
        logger.setLevel(logging.INFO)
        self.logger = logger

        # Distributed tracing
        self.tracer = Tracer(
            exporter=AzureExporter(connection_string=self.connection_string),
            sampler=ProbabilitySampler(1.0)
        )

        # Flask middleware for automatic request tracing
        FlaskMiddleware(app, exporter=AzureExporter(connection_string=self.connection_string))

    def log_agent_execution(self, agent_name: str, duration_ms: float, tokens: int, success: bool):
        """Log agent execution metrics"""
        self.logger.info(
            "Agent execution",
            extra={
                "custom_dimensions": {
                    "agent": agent_name,
                    "duration_ms": duration_ms,
                    "tokens_used": tokens,
                    "success": success
                }
            }
        )

    def trace_design_workflow(self, design_id: str, user_id: str):
        """Create distributed trace for entire design workflow"""
        with self.tracer.span(name="design_workflow") as span:
            span.add_attribute("design_id", design_id)
            span.add_attribute("user_id", user_id)
            return span
```

2. **Add Custom Metrics** ([backend/metrics.py](backend/metrics.py))
```python
from prometheus_client import Counter, Histogram, Gauge
import time

# Design workflow metrics
design_requests_total = Counter(
    'carlos_design_requests_total',
    'Total design requests',
    ['status']
)

design_duration_seconds = Histogram(
    'carlos_design_duration_seconds',
    'Design workflow duration',
    buckets=[10, 30, 60, 120, 300, 600]
)

agent_execution_duration = Histogram(
    'carlos_agent_execution_seconds',
    'Individual agent execution time',
    ['agent_name', 'model']
)

active_designs = Gauge(
    'carlos_active_designs',
    'Number of designs currently being processed'
)

llm_tokens_used = Counter(
    'carlos_llm_tokens_total',
    'Total LLM tokens consumed',
    ['model', 'agent']
)

llm_cost_usd = Counter(
    'carlos_llm_cost_usd_total',
    'Total LLM cost in USD',
    ['model']
)
```

3. **Add Health Check Endpoints** ([backend/main.py](backend/main.py))
```python
@app.get("/health")
async def health_check():
    """Kubernetes liveness probe"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe - checks dependencies"""
    checks = {}

    # Check Azure OpenAI connectivity
    try:
        llm = get_llm()
        await llm.ainvoke([HumanMessage(content="health check")])
        checks["azure_openai"] = "healthy"
    except Exception as e:
        checks["azure_openai"] = f"unhealthy: {str(e)}"

    # Check Cosmos DB connectivity
    try:
        db = CarlosDatabase()
        # Simple query to verify connection
        checks["cosmos_db"] = "healthy"
    except Exception as e:
        checks["cosmos_db"] = f"unhealthy: {str(e)}"

    all_healthy = all(v == "healthy" for v in checks.values())
    status_code = 200 if all_healthy else 503

    return Response(
        content=json.dumps({"status": "ready" if all_healthy else "not ready", "checks": checks}),
        status_code=status_code,
        media_type="application/json"
    )

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )
```

### 1.3 Frontend History & Analytics (Weeks 7-10)

**Objective:** Display historical designs and analytics in the UI

**Implementation:**

1. **Add History View** ([frontend/src/components/History.jsx](frontend/src/components/History.jsx))
```jsx
export function History() {
  const [designs, setDesigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDesign, setSelectedDesign] = useState(null);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const response = await fetch(`${backendUrl}/history`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await response.json();
      setDesigns(data.designs);
    } catch (error) {
      console.error('Failed to load history:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-3 gap-6 h-full">
      {/* Left: List of designs */}
      <div className="col-span-1 overflow-auto">
        <h2 className="text-xl font-bold mb-4">Design History</h2>
        {designs.map(design => (
          <DesignCard
            key={design.id}
            design={design}
            onClick={() => setSelectedDesign(design)}
            selected={selectedDesign?.id === design.id}
          />
        ))}
      </div>

      {/* Right: Selected design details */}
      <div className="col-span-2 overflow-auto">
        {selectedDesign ? (
          <DesignDetails design={selectedDesign} />
        ) : (
          <EmptyState message="Select a design to view details" />
        )}
      </div>
    </div>
  );
}
```

2. **Add Analytics Dashboard** ([frontend/src/components/Analytics.jsx](frontend/src/components/Analytics.jsx))
```jsx
export function Analytics() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    const response = await fetch(`${backendUrl}/analytics`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
    });
    const data = await response.json();
    setStats(data);
  };

  return (
    <div className="space-y-6">
      <StatsOverview
        totalDesigns={stats?.total_designs}
        avgCost={stats?.avg_cost}
        avgDuration={stats?.avg_duration}
        tokensSaved={stats?.tokens_saved_vs_all_gpt4o}
      />

      <CostTrends data={stats?.cost_over_time} />

      <TopRequirements patterns={stats?.common_requirements} />

      <AgentPerformance metrics={stats?.agent_metrics} />
    </div>
  );
}
```

**Deliverables:**
- ✅ Cosmos DB integrated with full workflow persistence
- ✅ Azure Application Insights for logging and tracing
- ✅ Prometheus metrics endpoint
- ✅ Health and readiness checks
- ✅ Frontend history and analytics views

**Estimated Cost Impact:**
- Cosmos DB (400 RU/s): ~$24/month
- Application Insights: ~$2-5/month (low volume)
- **Total: ~$26-29/month additional**

---

## Phase 2: Enterprise Reliability

**Duration:** 8-10 weeks

### 2.1 Auto-Scaling & High Availability (Weeks 1-4)

**Objective:** Replace manual Kubernetes scaling with Azure Container Apps auto-scaling

**Implementation:**

#### Option A: Migrate to Azure Container Apps (Recommended)

**Pros:**
- ✅ Built-in auto-scaling (0 to N instances)
- ✅ Managed service (no Kubernetes operations)
- ✅ KEDA-based event-driven scaling
- ✅ Lower operational overhead
- ✅ Pay-per-use pricing

**Cons:**
- ❌ Less control than Kubernetes
- ❌ Migration effort required

**Migration Steps:**

1. **Create Container Apps Environment** ([infra/main.tf](infra/main.tf))
```hcl
resource "azurerm_container_app_environment" "carlos" {
  name                       = "${var.project_name}-env-${var.environment}"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.carlos.id
}

resource "azurerm_container_app" "backend" {
  name                         = "carlos-backend"
  container_app_environment_id = azurerm_container_app_environment.carlos.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"

  template {
    container {
      name   = "carlos-backend"
      image  = "${azurerm_container_registry.main.login_server}/carlos-backend:latest"
      cpu    = 0.5
      memory = "1Gi"

      env {
        name        = "AZURE_OPENAI_ENDPOINT"
        secret_name = "azure-openai-endpoint"
      }
      env {
        name        = "AZURE_OPENAI_API_KEY"
        secret_name = "azure-openai-api-key"
      }
      env {
        name        = "COSMOS_ENDPOINT"
        secret_name = "cosmos-endpoint"
      }
      env {
        name        = "COSMOS_KEY"
        secret_name = "cosmos-key"
      }
    }

    min_replicas = 0  # Scale to zero when idle
    max_replicas = 10

    # HTTP-based scaling
    http_scale_rule {
      name                = "http-rule"
      concurrent_requests = 100
    }
  }

  ingress {
    external_enabled = true
    target_port      = 8000

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  registry {
    server               = azurerm_container_registry.main.login_server
    username             = azurerm_container_registry.main.admin_username
    password_secret_name = "acr-password"
  }

  secret {
    name  = "azure-openai-endpoint"
    value = var.azure_openai_endpoint
  }
  secret {
    name  = "azure-openai-api-key"
    value = var.azure_openai_api_key
  }
  secret {
    name  = "cosmos-endpoint"
    value = azurerm_cosmosdb_account.carlos.endpoint
  }
  secret {
    name  = "cosmos-key"
    value = azurerm_cosmosdb_account.carlos.primary_key
  }
  secret {
    name  = "acr-password"
    value = azurerm_container_registry.main.admin_password
  }
}
```

#### Option B: Enhanced Kubernetes with HPA (Alternative)

**Pros:**
- ✅ Keep existing Kubernetes expertise
- ✅ More control over scaling behavior
- ✅ Can use spot instances for cost savings

**Implementation:**

1. **Add Horizontal Pod Autoscaler** ([k8s/backend-hpa.yaml](k8s/backend-hpa.yaml))
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: carlos-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: carlos-backend
  minReplicas: 1
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
      - type: Pods
        value: 2
        periodSeconds: 30
      selectPolicy: Max
```

2. **Add KEDA for Advanced Scaling** ([k8s/keda-scaledobject.yaml](k8s/keda-scaledobject.yaml))
```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: carlos-backend-scaler
spec:
  scaleTargetRef:
    name: carlos-backend
  minReplicaCount: 1
  maxReplicaCount: 10
  cooldownPeriod: 300
  triggers:
  - type: prometheus
    metadata:
      serverAddress: http://prometheus:9090
      metricName: carlos_design_requests_rate
      threshold: '10'
      query: sum(rate(carlos_design_requests_total[1m]))
```

### 2.2 Multi-Region Deployment (Weeks 5-7)

**Objective:** Deploy Carlos across multiple Azure regions for high availability

**Implementation:**

1. **Add Traffic Manager** ([infra/main.tf](infra/main.tf))
```hcl
resource "azurerm_traffic_manager_profile" "carlos" {
  name                   = "${var.project_name}-tm-${var.environment}"
  resource_group_name    = azurerm_resource_group.main.name
  traffic_routing_method = "Performance"  # Route to nearest region

  dns_config {
    relative_name = "${var.project_name}-${var.environment}"
    ttl           = 30
  }

  monitor_config {
    protocol                     = "HTTPS"
    port                         = 443
    path                         = "/health"
    interval_in_seconds          = 30
    timeout_in_seconds           = 10
    tolerated_number_of_failures = 3
  }
}

# Deploy to primary region (e.g., East US)
module "primary_region" {
  source = "./modules/regional-deployment"

  region              = "eastus"
  project_name        = var.project_name
  environment         = var.environment
  is_primary          = true
  cosmos_endpoint     = azurerm_cosmosdb_account.carlos.endpoint
  cosmos_key          = azurerm_cosmosdb_account.carlos.primary_key
}

# Deploy to secondary region (e.g., West US 2)
module "secondary_region" {
  source = "./modules/regional-deployment"

  region              = "westus2"
  project_name        = var.project_name
  environment         = var.environment
  is_primary          = false
  cosmos_endpoint     = azurerm_cosmosdb_account.carlos.endpoint
  cosmos_key          = azurerm_cosmosdb_account.carlos.primary_key
}

# Traffic Manager endpoints
resource "azurerm_traffic_manager_azure_endpoint" "primary" {
  name               = "primary-${module.primary_region.region}"
  profile_id         = azurerm_traffic_manager_profile.carlos.id
  weight             = 100
  target_resource_id = module.primary_region.frontend_id
  priority           = 1
}

resource "azurerm_traffic_manager_azure_endpoint" "secondary" {
  name               = "secondary-${module.secondary_region.region}"
  profile_id         = azurerm_traffic_manager_profile.carlos.id
  weight             = 100
  target_resource_id = module.secondary_region.frontend_id
  priority           = 2
}
```

### 2.3 Disaster Recovery & Backup (Weeks 8-10)

**Implementation:**

1. **Enable Cosmos DB Multi-Region Writes**
```hcl
resource "azurerm_cosmosdb_account" "carlos" {
  # ... existing config ...

  enable_multiple_write_locations = true

  geo_location {
    location          = "eastus"
    failover_priority = 0
  }

  geo_location {
    location          = "westus2"
    failover_priority = 1
  }

  backup {
    type                = "Continuous"  # Point-in-time restore up to 30 days
    interval_in_minutes = 240
    retention_in_hours  = 720  # 30 days
  }
}
```

2. **Add Backup Jobs** ([infra/backup.tf](infra/backup.tf))
```hcl
resource "azurerm_data_protection_backup_vault" "carlos" {
  name                = "${var.project_name}-backup-vault"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  datastore_type      = "VaultStore"
  redundancy          = "GeoRedundant"
}

resource "azurerm_data_protection_backup_policy_blob_storage" "carlos" {
  name               = "carlos-blob-backup-policy"
  vault_id           = azurerm_data_protection_backup_vault.carlos.id
  retention_duration = "P30D"
}
```

**Deliverables:**
- ✅ Auto-scaling with Container Apps or KEDA
- ✅ Multi-region deployment with Traffic Manager
- ✅ Cosmos DB geo-replication
- ✅ Automated backups with point-in-time restore
- ✅ 99.95% SLA for frontend and backend

**Cost Impact:**
- Container Apps: ~$0-50/month (pay per use)
- Traffic Manager: ~$7/month (2 endpoints)
- Multi-region Cosmos DB: +$24/month (replica)
- Backup Vault: ~$5/month
- **Total: ~$36-86/month additional**

---

## Phase 3: Learning & Intelligence

**Duration:** 10-12 weeks

### 3.1 Requirements Analysis & Pattern Recognition (Weeks 1-4)

**Objective:** Learn from historical designs to improve recommendations

**Implementation:**

1. **Add Vector Embeddings for Semantic Search** ([backend/embeddings.py](backend/embeddings.py))
```python
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
)
from langchain_openai import AzureOpenAIEmbeddings

class CarlosSemanticSearch:
    def __init__(self):
        # Azure Cognitive Search for vector storage
        self.search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.search_key = os.getenv("AZURE_SEARCH_KEY")

        # Azure OpenAI embeddings
        self.embeddings = AzureOpenAIEmbeddings(
            azure_deployment="text-embedding-ada-002",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY")
        )

        self.index_name = "carlos-designs"
        self._ensure_index_exists()

    def _ensure_index_exists(self):
        """Create search index with vector fields"""
        index_client = SearchIndexClient(
            endpoint=self.search_endpoint,
            credential=AzureKeyCredential(self.search_key)
        )

        fields = [
            SearchField(name="id", type=SearchFieldDataType.String, key=True),
            SearchField(name="requirements", type=SearchFieldDataType.String, searchable=True),
            SearchField(name="requirements_vector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                       searchable=True, vector_search_dimensions=1536,
                       vector_search_profile_name="carlos-vector-profile"),
            SearchField(name="carlos_design", type=SearchFieldDataType.String),
            SearchField(name="ronei_design", type=SearchFieldDataType.String),
            SearchField(name="recommendation", type=SearchFieldDataType.String),
            SearchField(name="terraform_code", type=SearchFieldDataType.String),
            SearchField(name="timestamp", type=SearchFieldDataType.DateTimeOffset),
            SearchField(name="user_id", type=SearchFieldDataType.String, filterable=True),
        ]

        vector_search = VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name="carlos-hnsw")],
            profiles=[VectorSearchProfile(name="carlos-vector-profile", algorithm_configuration_name="carlos-hnsw")]
        )

        index = SearchIndex(name=self.index_name, fields=fields, vector_search=vector_search)
        index_client.create_or_update_index(index)

    async def index_design(self, design_data: dict):
        """Index a design with vector embeddings"""
        requirements_vector = await self.embeddings.aembed_query(design_data["requirements"])

        document = {
            "id": design_data["design_id"],
            "requirements": design_data["requirements"],
            "requirements_vector": requirements_vector,
            "carlos_design": design_data["carlos_design"],
            "ronei_design": design_data["ronei_design"],
            "recommendation": design_data["recommendation"],
            "terraform_code": design_data["terraform_code"],
            "timestamp": design_data["timestamp"],
            "user_id": design_data["user_id"]
        }

        search_client = SearchClient(
            endpoint=self.search_endpoint,
            index_name=self.index_name,
            credential=AzureKeyCredential(self.search_key)
        )

        search_client.upload_documents(documents=[document])

    async def find_similar_designs(self, requirements: str, top_k: int = 5) -> list:
        """Find similar past designs using vector similarity"""
        requirements_vector = await self.embeddings.aembed_query(requirements)

        search_client = SearchClient(
            endpoint=self.search_endpoint,
            index_name=self.index_name,
            credential=AzureKeyCredential(self.search_key)
        )

        results = search_client.search(
            search_text=None,
            vector_queries=[{
                "vector": requirements_vector,
                "k_nearest_neighbors": top_k,
                "fields": "requirements_vector"
            }]
        )

        return [
            {
                "requirements": result["requirements"],
                "carlos_design": result["carlos_design"],
                "recommendation": result["recommendation"],
                "similarity_score": result["@search.score"]
            }
            for result in results
        ]
```

2. **Add Learning Agent** ([backend/agents/learner.py](backend/agents/learner.py))
```python
async def learning_agent_node(state: CarlosState):
    """Analyze similar past designs to improve current design"""
    semantic_search = CarlosSemanticSearch()

    # Find similar requirements
    similar_designs = await semantic_search.find_similar_designs(
        state["requirements"],
        top_k=3
    )

    if not similar_designs:
        # No similar designs found, continue as normal
        return {"conversation": ""}

    # Extract insights from similar designs
    insights_prompt = f"""Based on these similar past designs, provide insights for the current requirements.

Current Requirements:
{state['requirements']}

Similar Past Designs:
{json.dumps(similar_designs, indent=2)}

Provide:
1. What worked well in past similar designs
2. What issues were encountered
3. Recommended approaches for this new design
4. Any cost or performance learnings

Keep it concise (3-5 bullet points)."""

    messages = [
        SystemMessage(content="You analyze past designs to extract learnings."),
        HumanMessage(content=insights_prompt)
    ]

    response = await get_mini_llm().ainvoke(messages)
    insights = response.content

    convo = state.get("conversation", "")
    convo += f"**Learning Agent:**\n{insights}\n\n"

    return {
        "conversation": convo,
        "historical_insights": insights
    }
```

3. **Update Carlos and Ronei to Use Insights** ([backend/graph.py](backend/graph.py))
```python
async def carlos_design_node(state: CarlosState):
    """Carlos drafts the infrastructure with historical context"""
    requirements = state.get('refined_requirements') or state['requirements']
    historical_insights = state.get('historical_insights', '')

    user_content = f"User requirements: {requirements}"

    if historical_insights:
        user_content += f"\n\nInsights from similar past designs:\n{historical_insights}"

    messages = [
        SystemMessage(content=CARLOS_INSTRUCTIONS),
        HumanMessage(content=user_content)
    ]

    # ... rest of implementation
```

### 3.2 Feedback Loop & Design Ratings (Weeks 5-7)

**Objective:** Collect user feedback to improve agent recommendations

**Implementation:**

1. **Add Feedback API** ([backend/main.py](backend/main.py))
```python
class DesignFeedback(BaseModel):
    design_id: str
    rating: int  # 1-5 stars
    implemented: bool  # Did they actually use this design?
    feedback_text: Optional[str]
    cost_estimate_accuracy: Optional[int]  # 1-5 how accurate was cost estimate
    security_concerns_found: Optional[List[str]]
    modifications_made: Optional[str]

@app.post("/feedback")
async def submit_feedback(
    feedback: DesignFeedback,
    user_id: str = Depends(get_current_user_id)
):
    """Submit feedback for a design"""
    db = CarlosDatabase()

    # Store feedback
    await db.save_feedback(user_id, feedback.dict())

    # Update design rating
    await db.update_design_rating(feedback.design_id, feedback.rating)

    # If implemented, mark as successful
    if feedback.implemented:
        await db.mark_design_implemented(feedback.design_id)

    return {"status": "success", "message": "Feedback recorded"}
```

2. **Add Feedback UI** ([frontend/src/components/FeedbackForm.jsx](frontend/src/components/FeedbackForm.jsx))
```jsx
export function FeedbackForm({ designId, onSubmit }) {
  const [rating, setRating] = useState(0);
  const [implemented, setImplemented] = useState(false);
  const [feedbackText, setFeedbackText] = useState('');

  const handleSubmit = async () => {
    await fetch(`${backendUrl}/feedback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        design_id: designId,
        rating,
        implemented,
        feedback_text: feedbackText
      })
    });

    onSubmit?.();
  };

  return (
    <div className="bg-blue-50 border-l-4 border-blue-500 p-6 rounded-lg">
      <h3 className="font-bold text-lg mb-4">📊 How was this design?</h3>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">Overall Rating</label>
          <StarRating value={rating} onChange={setRating} />
        </div>

        <div>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={implemented}
              onChange={(e) => setImplemented(e.target.checked)}
            />
            <span>I implemented this design in production</span>
          </label>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">
            Additional feedback (optional)
          </label>
          <textarea
            value={feedbackText}
            onChange={(e) => setFeedbackText(e.target.value)}
            placeholder="What worked well? What could be improved?"
            className="w-full p-3 border rounded-lg"
            rows={4}
          />
        </div>

        <button
          onClick={handleSubmit}
          disabled={rating === 0}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          Submit Feedback
        </button>
      </div>
    </div>
  );
}
```

### 3.3 Continuous Learning Pipeline (Weeks 8-12)

**Objective:** Automatically improve agent prompts based on feedback

**Implementation:**

1. **Add Prompt Optimization Agent** ([backend/agents/optimizer.py](backend/agents/optimizer.py))
```python
class PromptOptimizer:
    """Analyzes feedback to suggest prompt improvements"""

    async def analyze_feedback_trends(self, lookback_days: int = 30):
        """Analyze recent feedback to identify improvement areas"""
        db = CarlosDatabase()

        # Get low-rated designs
        low_rated = await db.get_designs_by_rating(max_rating=2, limit=50)

        # Get high-rated designs
        high_rated = await db.get_designs_by_rating(min_rating=4, limit=50)

        # Analyze patterns
        analysis_prompt = f"""Analyze these design outcomes to identify what makes a good vs bad design.

Low-Rated Designs (1-2 stars):
{json.dumps([d["requirements"] for d in low_rated[:10]], indent=2)}

High-Rated Designs (4-5 stars):
{json.dumps([d["requirements"] for d in high_rated[:10]], indent=2)}

Common feedback themes:
- Cost estimates were often {self._get_cost_accuracy_trend()}
- Security concerns: {self._get_common_security_issues()}
- Modifications users made: {self._get_common_modifications()}

Provide:
1. What patterns differentiate high vs low-rated designs?
2. What aspects of requirements lead to better outcomes?
3. What should Carlos and Ronei emphasize more?
4. What should they de-emphasize?

Be specific and actionable."""

        messages = [
            SystemMessage(content="You are a meta-learning agent that improves other agents."),
            HumanMessage(content=analysis_prompt)
        ]

        response = await get_llm().ainvoke(messages)
        recommendations = response.content

        # Store recommendations for review
        await db.save_optimizer_recommendations({
            "timestamp": datetime.utcnow().isoformat(),
            "recommendations": recommendations,
            "sample_size": len(low_rated) + len(high_rated)
        })

        return recommendations

    def _get_cost_accuracy_trend(self):
        # Analyze cost_estimate_accuracy ratings
        pass

    def _get_common_security_issues(self):
        # Extract common security_concerns_found
        pass

    def _get_common_modifications(self):
        # Analyze modifications_made text
        pass
```

2. **Add Admin Dashboard for Prompt Management** ([frontend/src/components/Admin.jsx](frontend/src/components/Admin.jsx))
```jsx
export function AdminDashboard() {
  const [recommendations, setRecommendations] = useState([]);
  const [agentPrompts, setAgentPrompts] = useState({});

  return (
    <div className="space-y-8">
      <section>
        <h2 className="text-2xl font-bold mb-4">🧠 Learning Recommendations</h2>
        <p className="text-gray-600 mb-4">
          Based on the last 30 days of user feedback, here are suggested improvements:
        </p>

        {recommendations.map(rec => (
          <RecommendationCard
            key={rec.id}
            recommendation={rec}
            onApprove={() => applyRecommendation(rec.id)}
            onDismiss={() => dismissRecommendation(rec.id)}
          />
        ))}
      </section>

      <section>
        <h2 className="text-2xl font-bold mb-4">📝 Agent Prompts</h2>
        <p className="text-gray-600 mb-4">
          Review and update agent system prompts:
        </p>

        <AgentPromptEditor
          agents={['carlos', 'ronei', 'security', 'cost', 'reliability', 'auditor']}
          prompts={agentPrompts}
          onSave={savePrompts}
        />
      </section>

      <section>
        <h2 className="text-2xl font-bold mb-4">📊 A/B Testing</h2>
        <ABTestManager />
      </section>
    </div>
  );
}
```

**Deliverables:**
- ✅ Vector-based semantic search for similar designs
- ✅ Learning agent that provides historical insights
- ✅ User feedback collection system
- ✅ Prompt optimization recommendations
- ✅ Admin dashboard for prompt management
- ✅ A/B testing framework for prompt improvements

**Cost Impact:**
- Azure Cognitive Search: ~$75/month (basic tier with vectors)
- OpenAI Embeddings: ~$1-5/month
- **Total: ~$76-80/month additional**

---

## Phase 4: Flexible Orchestration

**Duration:** 10-12 weeks

### 4.1 Dynamic Agent Composition (Weeks 1-5)

**Objective:** Allow users to customize which agents run and in what order

**Implementation:**

1. **Define Agent Registry** ([backend/agent_registry.py](backend/agent_registry.py))
```python
from typing import Callable, List, Optional
from dataclasses import dataclass

@dataclass
class AgentDefinition:
    id: str
    name: str
    description: str
    category: str  # "design", "analysis", "synthesis", "custom"
    node_function: Callable
    dependencies: List[str]  # Agent IDs that must run before this
    model_size: str  # "mini" or "full"
    estimated_cost: float  # USD per execution
    estimated_duration_seconds: int

class AgentRegistry:
    def __init__(self):
        self.agents = {}
        self._register_builtin_agents()

    def _register_builtin_agents(self):
        """Register Carlos's built-in agents"""
        self.register(AgentDefinition(
            id="requirements_gathering",
            name="Requirements Clarification",
            description="Asks clarifying questions about vague requirements",
            category="design",
            node_function=requirements_gathering_node,
            dependencies=[],
            model_size="mini",
            estimated_cost=0.001,
            estimated_duration_seconds=5
        ))

        self.register(AgentDefinition(
            id="carlos",
            name="Carlos (Pragmatic Architect)",
            description="Designs practical, proven architectures",
            category="design",
            node_function=carlos_design_node,
            dependencies=["requirements_gathering"],
            model_size="full",
            estimated_cost=0.05,
            estimated_duration_seconds=30
        ))

        self.register(AgentDefinition(
            id="ronei",
            name="Ronei (Modern Innovator)",
            description="Designs cutting-edge, innovative architectures",
            category="design",
            node_function=ronei_design_node,
            dependencies=["requirements_gathering"],
            model_size="full",
            estimated_cost=0.05,
            estimated_duration_seconds=30
        ))

        # ... register all other agents

    def register(self, agent: AgentDefinition):
        """Register a new agent"""
        self.agents[agent.id] = agent

    def get_agent(self, agent_id: str) -> Optional[AgentDefinition]:
        return self.agents.get(agent_id)

    def list_agents(self, category: Optional[str] = None) -> List[AgentDefinition]:
        agents = self.agents.values()
        if category:
            agents = [a for a in agents if a.category == category]
        return list(agents)
```

2. **Add Workflow Builder** ([backend/workflow_builder.py](backend/workflow_builder.py))
```python
from langgraph.graph import StateGraph, START, END
from typing import List, Dict

class WorkflowBuilder:
    def __init__(self, agent_registry: AgentRegistry):
        self.registry = agent_registry

    def build_workflow(self, agent_ids: List[str]) -> StateGraph:
        """Build a dynamic workflow from selected agents"""
        graph = StateGraph(CarlosState)

        # Validate dependencies
        self._validate_dependencies(agent_ids)

        # Add nodes
        for agent_id in agent_ids:
            agent = self.registry.get_agent(agent_id)
            graph.add_node(agent_id, agent.node_function)

        # Add edges based on dependencies
        self._add_edges(graph, agent_ids)

        return graph.compile()

    def _validate_dependencies(self, agent_ids: List[str]):
        """Ensure all dependencies are included"""
        for agent_id in agent_ids:
            agent = self.registry.get_agent(agent_id)
            for dep in agent.dependencies:
                if dep not in agent_ids:
                    raise ValueError(
                        f"Agent '{agent_id}' requires '{dep}' but it's not included"
                    )

    def _add_edges(self, graph: StateGraph, agent_ids: List[str]):
        """Add edges based on agent dependencies"""
        # Group agents by dependency level
        levels = self._topological_sort(agent_ids)

        # Add edges
        for i, level in enumerate(levels):
            if i == 0:
                # Connect START to first level
                for agent_id in level:
                    graph.add_edge(START, agent_id)
            else:
                # Connect previous level to current level
                for prev_agent_id in levels[i-1]:
                    for agent_id in level:
                        agent = self.registry.get_agent(agent_id)
                        if prev_agent_id in agent.dependencies:
                            graph.add_edge(prev_agent_id, agent_id)

        # Connect last level to END
        for agent_id in levels[-1]:
            graph.add_edge(agent_id, END)

    def _topological_sort(self, agent_ids: List[str]) -> List[List[str]]:
        """Group agents into dependency levels for parallel execution"""
        # Implementation of topological sort
        # Returns: [[level0_agents], [level1_agents], ...]
        pass
```

3. **Add Workflow Templates** ([backend/workflow_templates.py](backend/workflow_templates.py))
```python
class WorkflowTemplates:
    """Pre-defined workflow templates for common use cases"""

    @staticmethod
    def quick_design():
        """Fast design without extensive analysis"""
        return [
            "carlos",  # Just Carlos, no Ronei
            "security",
            "cost",
            "terraform_coder"
        ]

    @staticmethod
    def comprehensive_design():
        """Full analysis with all agents (current default)"""
        return [
            "requirements_gathering",
            "carlos",
            "ronei",
            "security",
            "cost",
            "reliability",
            "auditor",
            "recommender",
            "terraform_coder"
        ]

    @staticmethod
    def cost_optimized_design():
        """Focus on cost optimization"""
        return [
            "carlos",
            "cost",
            "finops",  # New FinOps specialist agent
            "cost_optimizer",  # New cost optimization agent
            "terraform_coder"
        ]

    @staticmethod
    def security_focused_design():
        """Focus on security and compliance"""
        return [
            "requirements_gathering",
            "carlos",
            "security",
            "compliance",  # New compliance agent
            "penetration_tester",  # New security testing agent
            "auditor",
            "terraform_coder"
        ]
```

4. **Add Workflow Selection API** ([backend/main.py](backend/main.py))
```python
class DesignRequest(BaseModel):
    text: str
    user_answers: Optional[str] = None
    workflow_template: Optional[str] = "comprehensive"  # quick, comprehensive, cost, security
    custom_agents: Optional[List[str]] = None  # For fully custom workflows

@app.post("/design-stream")
async def design_stream(
    request: DesignRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Stream design with configurable workflow"""

    # Determine which agents to run
    if request.custom_agents:
        agent_ids = request.custom_agents
    elif request.workflow_template:
        template_func = getattr(WorkflowTemplates, f"{request.workflow_template}_design")
        agent_ids = template_func()
    else:
        agent_ids = WorkflowTemplates.comprehensive_design()

    # Build dynamic workflow
    registry = AgentRegistry()
    builder = WorkflowBuilder(registry)
    workflow = builder.build_workflow(agent_ids)

    # Execute workflow
    # ... streaming implementation
```

### 4.2 Custom Agent Development (Weeks 6-9)

**Objective:** Allow users to create their own domain-specific agents

**Implementation:**

1. **Add Custom Agent API** ([backend/main.py](backend/main.py))
```python
class CustomAgentDefinition(BaseModel):
    name: str
    description: str
    system_prompt: str
    category: str
    dependencies: List[str] = []
    model_size: str = "full"  # "mini" or "full"

@app.post("/custom-agents")
async def create_custom_agent(
    agent: CustomAgentDefinition,
    user_id: str = Depends(get_current_user_id)
):
    """Create a custom agent"""
    db = CarlosDatabase()

    # Create agent function dynamically
    async def custom_agent_node(state: CarlosState):
        requirements = state.get('refined_requirements') or state['requirements']

        messages = [
            SystemMessage(content=agent.system_prompt),
            HumanMessage(content=f"Requirements:\n{requirements}")
        ]

        llm = get_mini_llm() if agent.model_size == "mini" else get_llm()
        response = await llm.ainvoke(messages)

        convo = state.get("conversation", "")
        convo += f"**{agent.name}:**\n{response.content}\n\n"

        return {
            "conversation": convo,
            f"custom_{agent.name}": response.content
        }

    # Register agent
    agent_id = f"custom_{user_id}_{agent.name.lower().replace(' ', '_')}"

    agent_def = AgentDefinition(
        id=agent_id,
        name=agent.name,
        description=agent.description,
        category=agent.category,
        node_function=custom_agent_node,
        dependencies=agent.dependencies,
        model_size=agent.model_size,
        estimated_cost=0.001 if agent.model_size == "mini" else 0.05,
        estimated_duration_seconds=10
    )

    # Store in database
    await db.save_custom_agent(user_id, agent_id, agent.dict())

    # Register in registry (in-memory for this session)
    registry = AgentRegistry()
    registry.register(agent_def)

    return {"agent_id": agent_id, "message": "Custom agent created"}

@app.get("/custom-agents")
async def list_custom_agents(user_id: str = Depends(get_current_user_id)):
    """List user's custom agents"""
    db = CarlosDatabase()
    agents = await db.get_user_custom_agents(user_id)
    return {"agents": agents}
```

2. **Add Agent Marketplace** ([frontend/src/components/AgentMarketplace.jsx](frontend/src/components/AgentMarketplace.jsx))
```jsx
export function AgentMarketplace() {
  const [builtInAgents, setBuiltInAgents] = useState([]);
  const [customAgents, setCustomAgents] = useState([]);
  const [communityAgents, setCommunityAgents] = useState([]);

  return (
    <div className="space-y-8">
      <section>
        <h2 className="text-2xl font-bold mb-4">🤖 Built-in Agents</h2>
        <div className="grid grid-cols-3 gap-4">
          {builtInAgents.map(agent => (
            <AgentCard
              key={agent.id}
              agent={agent}
              type="builtin"
            />
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-bold mb-4">✨ Your Custom Agents</h2>
        <button
          onClick={() => openAgentBuilder()}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg mb-4"
        >
          + Create New Agent
        </button>

        <div className="grid grid-cols-3 gap-4">
          {customAgents.map(agent => (
            <AgentCard
              key={agent.id}
              agent={agent}
              type="custom"
              onEdit={() => editAgent(agent)}
              onDelete={() => deleteAgent(agent.id)}
            />
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-bold mb-4">🌍 Community Agents</h2>
        <p className="text-gray-600 mb-4">
          Agents shared by the Carlos community
        </p>
        <div className="grid grid-cols-3 gap-4">
          {communityAgents.map(agent => (
            <AgentCard
              key={agent.id}
              agent={agent}
              type="community"
              onInstall={() => installAgent(agent)}
            />
          ))}
        </div>
      </section>
    </div>
  );
}
```

3. **Add Visual Workflow Builder** ([frontend/src/components/WorkflowBuilder.jsx](frontend/src/components/WorkflowBuilder.jsx))
```jsx
import ReactFlow from 'reactflow';

export function WorkflowBuilder() {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [availableAgents, setAvailableAgents] = useState([]);

  const onDrop = (event) => {
    // Drag agent from palette to canvas
    const agentId = event.dataTransfer.getData('agentId');
    const agent = availableAgents.find(a => a.id === agentId);

    // Add node to flow
    const newNode = {
      id: `${agentId}-${Date.now()}`,
      type: 'agentNode',
      position: { x: event.clientX, y: event.clientY },
      data: { agent }
    };

    setNodes([...nodes, newNode]);
  };

  const onConnect = (connection) => {
    // Connect two agents
    setEdges([...edges, connection]);
  };

  const saveWorkflow = async () => {
    // Save workflow template
    const workflow = {
      name: workflowName,
      agents: nodes.map(n => n.data.agent.id),
      connections: edges
    };

    await fetch(`${backendUrl}/workflows`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify(workflow)
    });
  };

  return (
    <div className="h-full flex">
      {/* Agent Palette */}
      <aside className="w-64 bg-gray-100 p-4">
        <h3 className="font-bold mb-4">Available Agents</h3>
        {availableAgents.map(agent => (
          <div
            key={agent.id}
            draggable
            onDragStart={(e) => e.dataTransfer.setData('agentId', agent.id)}
            className="bg-white p-3 mb-2 rounded shadow cursor-move"
          >
            <div className="font-medium">{agent.name}</div>
            <div className="text-xs text-gray-500">{agent.description}</div>
            <div className="text-xs text-gray-400 mt-1">
              ~{agent.estimated_duration_seconds}s, ${agent.estimated_cost.toFixed(3)}
            </div>
          </div>
        ))}
      </aside>

      {/* Flow Canvas */}
      <div className="flex-1 bg-gray-50">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={setNodes}
          onEdgesChange={setEdges}
          onConnect={onConnect}
          onDrop={onDrop}
          onDragOver={(e) => e.preventDefault()}
        >
          <Controls />
          <Background />
        </ReactFlow>
      </div>

      {/* Workflow Settings */}
      <aside className="w-80 bg-white p-4 border-l">
        <h3 className="font-bold mb-4">Workflow Settings</h3>

        <input
          type="text"
          placeholder="Workflow name"
          value={workflowName}
          onChange={(e) => setWorkflowName(e.target.value)}
          className="w-full p-2 border rounded mb-4"
        />

        <div className="space-y-2 mb-4">
          <div className="text-sm text-gray-600">
            <strong>Total Agents:</strong> {nodes.length}
          </div>
          <div className="text-sm text-gray-600">
            <strong>Est. Duration:</strong> {calculateTotalDuration()}s
          </div>
          <div className="text-sm text-gray-600">
            <strong>Est. Cost:</strong> ${calculateTotalCost().toFixed(3)}
          </div>
        </div>

        <button
          onClick={saveWorkflow}
          className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700"
        >
          Save Workflow
        </button>
      </aside>
    </div>
  );
}
```

### 4.3 Orchestration Patterns (Weeks 10-12)

**Implementation:**

1. **Add Pattern Support** ([backend/orchestration_patterns.py](backend/orchestration_patterns.py))
```python
class OrchestrationPattern:
    """Base class for orchestration patterns"""

    @abstractmethod
    async def execute(self, agents: List[AgentDefinition], state: CarlosState):
        pass

class SequentialPattern(OrchestrationPattern):
    """Run agents one after another"""

    async def execute(self, agents: List[AgentDefinition], state: CarlosState):
        for agent in agents:
            state = await agent.node_function(state)
        return state

class ParallelPattern(OrchestrationPattern):
    """Run all agents in parallel"""

    async def execute(self, agents: List[AgentDefinition], state: CarlosState):
        tasks = [agent.node_function(state) for agent in agents]
        results = await asyncio.gather(*tasks)

        # Merge results
        for result in results:
            state.update(result)

        return state

class GroupChatPattern(OrchestrationPattern):
    """Agents discuss and collaborate"""

    async def execute(self, agents: List[AgentDefinition], state: CarlosState):
        conversation_history = []
        max_rounds = 3

        for round in range(max_rounds):
            for agent in agents:
                # Add previous conversation as context
                state["group_chat_history"] = "\n\n".join(conversation_history)

                result = await agent.node_function(state)
                message = result.get("conversation", "")
                conversation_history.append(message)

        state["conversation"] = "\n\n".join(conversation_history)
        return state

class HandoffPattern(OrchestrationPattern):
    """Agents hand off work with explicit transitions"""

    async def execute(self, agents: List[AgentDefinition], state: CarlosState):
        for i, agent in enumerate(agents):
            # Agent decides if work is complete or needs handoff
            result = await agent.node_function(state)
            state.update(result)

            # Check if agent wants to hand off to next
            if result.get("handoff_to_next", True) and i < len(agents) - 1:
                continue
            else:
                break

        return state
```

**Deliverables:**
- ✅ Agent registry with built-in agents
- ✅ Dynamic workflow builder
- ✅ Workflow templates (quick, comprehensive, cost-focused, security-focused)
- ✅ Custom agent creation API
- ✅ Visual workflow builder UI
- ✅ Agent marketplace
- ✅ Multiple orchestration patterns (sequential, parallel, group chat, handoff)

**Cost Impact:**
- No additional infrastructure costs
- Development effort only

---

## Phase 5: Cross-Domain Expansion

**Duration:** 12-16 weeks

### 5.1 Multi-Cloud Support (Weeks 1-6)

**Objective:** Extend beyond Azure to AWS, GCP, and hybrid scenarios

**Implementation:**

1. **Add Cloud Provider Context** ([backend/cloud_providers.py](backend/cloud_providers.py))
```python
class CloudProvider(Enum):
    AZURE = "azure"
    AWS = "aws"
    GCP = "gcp"
    MULTI_CLOUD = "multi_cloud"

class ProviderPromptAdapter:
    """Adapts agent prompts for different cloud providers"""

    def adapt_carlos_prompt(self, base_prompt: str, provider: CloudProvider) -> str:
        if provider == CloudProvider.AWS:
            return base_prompt.replace("Azure", "AWS").replace(
                "AKS", "EKS"
            ).replace(
                "App Service", "Elastic Beanstalk"
            ) + "\n\nAWS-specific context:\n- Prefer AWS-native services\n- Consider AWS Well-Architected Framework\n- Use AWS best practices"

        elif provider == CloudProvider.GCP:
            return base_prompt.replace("Azure", "GCP").replace(
                "AKS", "GKE"
            ).replace(
                "App Service", "Cloud Run"
            ) + "\n\nGCP-specific context:\n- Prefer GCP-native services\n- Consider Google Cloud Architecture Framework\n- Use GCP best practices"

        elif provider == CloudProvider.MULTI_CLOUD:
            return base_prompt + "\n\nMulti-cloud context:\n- Design for cloud portability\n- Use cloud-agnostic abstractions (Kubernetes, Terraform)\n- Consider vendor lock-in implications\n- Plan for data residency and compliance across clouds"

        return base_prompt  # Azure default
```

2. **Add IaC Format Support** ([backend/agents/terraform_coder.py](backend/agents/terraform_coder.py))
```python
class IaCFormat(Enum):
    TERRAFORM = "terraform"
    PULUMI = "pulumi"
    CDK = "cdk"
    BICEP = "bicep"
    CLOUDFORMATION = "cloudformation"

async def iac_coder_node(state: CarlosState):
    """Generate IaC in requested format"""
    iac_format = state.get("iac_format", IaCFormat.TERRAFORM)
    cloud_provider = state.get("cloud_provider", CloudProvider.AZURE)

    format_instructions = {
        IaCFormat.TERRAFORM: "Generate Terraform HCL code",
        IaCFormat.PULUMI: "Generate Pulumi code in Python",
        IaCFormat.CDK: "Generate AWS CDK code in TypeScript",
        IaCFormat.BICEP: "Generate Azure Bicep code",
        IaCFormat.CLOUDFORMATION: "Generate AWS CloudFormation YAML"
    }

    instruction = format_instructions[iac_format]

    messages = [
        SystemMessage(content=f"{TERRAFORM_CODER_INSTRUCTIONS}\n\n{instruction}"),
        HumanMessage(content=f"Design:\n{state['design_doc']}")
    ]

    response = await get_llm().ainvoke(messages)

    return {
        "iac_code": response.content,
        "iac_format": iac_format.value,
        "conversation": state.get("conversation", "") + f"**IaC Coder ({iac_format.value}):**\n{response.content}\n\n"
    }
```

### 5.2 New Domain Agents (Weeks 7-12)

**Objective:** Add agents for non-architecture domains

**Pre-Built Domain Packs:**

1. **FinOps Pack** ([backend/agent_packs/finops.py](backend/agent_packs/finops.py))
```python
FINOPS_AGENT_PROMPT = """You are a FinOps specialist analyzing cloud costs.

Review the architecture design and provide:
1. Detailed cost breakdown by service
2. Reserved instance vs on-demand recommendations
3. Savings plans recommendations
4. Commitment discount opportunities
5. Cost allocation tags strategy
6. Budget alerts and anomaly detection setup
7. Showback/chargeback recommendations

Format your response with:
- Monthly cost estimate (optimistic, realistic, pessimistic)
- Annual cost projection
- Cost optimization opportunities (quick wins)
- Long-term cost reduction strategies
"""

COST_OPTIMIZER_AGENT_PROMPT = """You are a cost optimization specialist.

Given a design, suggest specific cost optimizations:
1. Right-sizing recommendations
2. Auto-scaling configurations
3. Spot instance usage opportunities
4. Data transfer optimization
5. Storage tiering strategies
6. Compute scheduling (shut down non-prod)

Provide concrete recommendations with:
- Current estimated cost
- Optimized estimated cost
- Savings percentage
- Implementation complexity (easy/medium/hard)
- Risk level (low/medium/high)
"""

# Register agents
def register_finops_agents(registry: AgentRegistry):
    registry.register(AgentDefinition(
        id="finops",
        name="FinOps Specialist",
        description="Detailed cloud cost analysis and optimization",
        category="analysis",
        node_function=finops_agent_node,
        dependencies=["carlos"],
        model_size="full",
        estimated_cost=0.03,
        estimated_duration_seconds=20
    ))

    registry.register(AgentDefinition(
        id="cost_optimizer",
        name="Cost Optimizer",
        description="Specific cost reduction recommendations",
        category="analysis",
        node_function=cost_optimizer_node,
        dependencies=["finops"],
        model_size="mini",
        estimated_cost=0.01,
        estimated_duration_seconds=15
    ))
```

2. **DevSecOps Pack** ([backend/agent_packs/devsecops.py](backend/agent_packs/devsecops.py))
```python
COMPLIANCE_AGENT_PROMPT = """You are a compliance specialist.

Review the design for compliance with:
- SOC 2 Type II
- ISO 27001
- HIPAA (if healthcare)
- PCI DSS (if payments)
- GDPR (if EU data)
- Industry-specific regulations

Provide:
1. Compliance gaps
2. Required controls
3. Audit trail requirements
4. Data residency considerations
5. Encryption requirements
6. Access control policies
"""

PENETRATION_TESTER_PROMPT = """You are a penetration tester.

Review the architecture for security vulnerabilities:
1. Attack surface analysis
2. Potential attack vectors
3. Privilege escalation risks
4. Data exfiltration risks
5. Denial of service vulnerabilities
6. Supply chain security

Provide specific recommendations to harden the architecture.
"""

# Register agents
def register_devsecops_agents(registry: AgentRegistry):
    # ... registration code
    pass
```

3. **Data Engineering Pack** ([backend/agent_packs/data_engineering.py](backend/agent_packs/data_engineering.py))
```python
DATA_ARCHITECT_PROMPT = """You are a data architect.

Design the data layer for this architecture:
1. Data storage strategy (structured, semi-structured, unstructured)
2. Data lakehouse architecture
3. ETL/ELT pipeline design
4. Data governance framework
5. Data quality checks
6. Master data management
7. Metadata management
8. Data lineage tracking
"""

DATA_GOVERNANCE_PROMPT = """You are a data governance specialist.

Define data governance policies:
1. Data classification scheme
2. Data access policies
3. Data retention policies
4. Data privacy controls
5. Consent management
6. Right to erasure (GDPR)
7. Data stewardship model
"""

# Register agents
def register_data_engineering_agents(registry: AgentRegistry):
    # ... registration code
    pass
```

### 5.3 Integration with External Tools (Weeks 13-16)

**Objective:** Connect Carlos to external APIs and services

**Implementation:**

1. **Add Tool Registry** ([backend/tools/registry.py](backend/tools/registry.py))
```python
from typing import Callable, Any

class Tool:
    def __init__(
        self,
        name: str,
        description: str,
        function: Callable,
        parameters_schema: dict
    ):
        self.name = name
        self.description = description
        self.function = function
        self.parameters_schema = parameters_schema

    async def execute(self, **kwargs) -> Any:
        return await self.function(**kwargs)

class ToolRegistry:
    def __init__(self):
        self.tools = {}
        self._register_builtin_tools()

    def _register_builtin_tools(self):
        """Register Carlos's built-in tools"""

        # Azure Pricing Calculator
        self.register(Tool(
            name="azure_pricing_calculator",
            description="Calculate accurate Azure pricing for services",
            function=self._azure_pricing_calculator,
            parameters_schema={
                "type": "object",
                "properties": {
                    "services": {"type": "array", "items": {"type": "string"}},
                    "region": {"type": "string"}
                },
                "required": ["services", "region"]
            }
        ))

        # Cost Management API
        self.register(Tool(
            name="get_actual_costs",
            description="Get actual costs from user's Azure account",
            function=self._get_actual_costs,
            parameters_schema={
                "type": "object",
                "properties": {
                    "subscription_id": {"type": "string"},
                    "timeframe": {"type": "string", "enum": ["week", "month", "year"]}
                },
                "required": ["subscription_id"]
            }
        ))

        # Well-Architected Review
        self.register(Tool(
            name="run_well_architected_review",
            description="Run automated Azure Well-Architected Review",
            function=self._run_well_architected_review,
            parameters_schema={
                "type": "object",
                "properties": {
                    "architecture_json": {"type": "object"}
                },
                "required": ["architecture_json"]
            }
        ))

    async def _azure_pricing_calculator(self, services: list, region: str):
        """Call Azure Pricing API"""
        # Implementation
        pass

    async def _get_actual_costs(self, subscription_id: str, timeframe: str = "month"):
        """Call Azure Cost Management API"""
        # Implementation
        pass

    async def _run_well_architected_review(self, architecture_json: dict):
        """Call Azure Advisor / Well-Architected Review API"""
        # Implementation
        pass

    def register(self, tool: Tool):
        self.tools[tool.name] = tool

    def get_tool(self, name: str) -> Tool:
        return self.tools.get(name)

    def list_tools(self) -> list[Tool]:
        return list(self.tools.values())
```

2. **Add Tool-Using Agents** ([backend/agents/tool_user.py](backend/agents/tool_user.py))
```python
async def cost_analyst_with_tools_node(state: CarlosState):
    """Cost analyst that uses real pricing data"""

    # Extract services from design
    design = state["design_doc"]
    services = extract_azure_services(design)

    # Use pricing calculator tool
    tool_registry = ToolRegistry()
    pricing_tool = tool_registry.get_tool("azure_pricing_calculator")

    pricing_data = await pricing_tool.execute(
        services=services,
        region=state.get("azure_region", "eastus")
    )

    # Analyze with real pricing
    messages = [
        SystemMessage(content=COST_ANALYST_INSTRUCTIONS),
        HumanMessage(content=f"""Design:
{design}

Real pricing data from Azure:
{json.dumps(pricing_data, indent=2)}

Provide a cost analysis using the real pricing data.""")
    ]

    response = await get_mini_llm().ainvoke(messages)

    return {
        "cost_report": response.content,
        "pricing_data": pricing_data,
        "conversation": state.get("conversation", "") + f"**Cost Analyst:**\n{response.content}\n\n"
    }
```

**Deliverables:**
- ✅ Multi-cloud support (Azure, AWS, GCP)
- ✅ Multiple IaC formats (Terraform, Pulumi, CDK, Bicep, CloudFormation)
- ✅ Domain agent packs (FinOps, DevSecOps, Data Engineering)
- ✅ Tool registry for external integrations
- ✅ Real pricing calculator integration
- ✅ Azure Advisor / Well-Architected Review integration

**Cost Impact:**
- No additional infrastructure costs (uses existing Azure services)
- May incur API call costs for pricing/cost management APIs (minimal)

---

## Phase 6: Enterprise Governance

**Duration:** 10-12 weeks

### 6.1 Audit Trail & Compliance (Weeks 1-4)

**Objective:** Complete audit logs for all operations

**Implementation:**

1. **Add Audit Logging** ([backend/audit.py](backend/audit.py))
```python
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class AuditEventType(Enum):
    DESIGN_REQUESTED = "design_requested"
    AGENT_EXECUTED = "agent_executed"
    WORKFLOW_COMPLETED = "workflow_completed"
    CUSTOM_AGENT_CREATED = "custom_agent_created"
    WORKFLOW_TEMPLATE_SAVED = "workflow_template_saved"
    FEEDBACK_SUBMITTED = "feedback_submitted"
    DESIGN_IMPLEMENTED = "design_implemented"
    IAC_DOWNLOADED = "iac_downloaded"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    SETTINGS_CHANGED = "settings_changed"

@dataclass
class AuditEvent:
    event_type: AuditEventType
    timestamp: datetime
    user_id: str
    ip_address: str
    details: dict
    success: bool
    error_message: Optional[str] = None

class AuditLogger:
    def __init__(self):
        self.db = CarlosDatabase()

    async def log_event(self, event: AuditEvent):
        """Log audit event to Cosmos DB"""
        document = {
            "id": f"{event.event_type.value}_{event.timestamp.isoformat()}_{event.user_id}",
            "event_type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "user_id": event.user_id,
            "ip_address": event.ip_address,
            "details": event.details,
            "success": event.success,
            "error_message": event.error_message
        }

        await self.db.audit_logs.upsert_item(document)

        # Also send to Application Insights for real-time monitoring
        logger.info(
            f"Audit: {event.event_type.value}",
            extra={
                "custom_dimensions": {
                    "user_id": event.user_id,
                    "ip_address": event.ip_address,
                    "success": event.success
                }
            }
        )

    async def get_audit_trail(
        self,
        user_id: Optional[str] = None,
        event_types: Optional[List[AuditEventType]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AuditEvent]:
        """Query audit trail"""
        # Build query
        # Return filtered audit events
        pass
```

2. **Add Audit Middleware** ([backend/middleware/audit_middleware.py](backend/middleware/audit_middleware.py))
```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Record request
        audit_logger = AuditLogger()

        start_time = datetime.utcnow()
        user_id = request.state.user_id if hasattr(request.state, 'user_id') else None
        ip_address = request.client.host

        try:
            response = await call_next(request)

            # Log successful request
            await audit_logger.log_event(AuditEvent(
                event_type=self._map_endpoint_to_event_type(request.url.path),
                timestamp=start_time,
                user_id=user_id,
                ip_address=ip_address,
                details={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code
                },
                success=response.status_code < 400
            ))

            return response

        except Exception as e:
            # Log failed request
            await audit_logger.log_event(AuditEvent(
                event_type=self._map_endpoint_to_event_type(request.url.path),
                timestamp=start_time,
                user_id=user_id,
                ip_address=ip_address,
                details={
                    "method": request.method,
                    "path": request.url.path
                },
                success=False,
                error_message=str(e)
            ))

            raise

    def _map_endpoint_to_event_type(self, path: str) -> AuditEventType:
        # Map API endpoint to audit event type
        if "/design" in path:
            return AuditEventType.DESIGN_REQUESTED
        elif "/custom-agents" in path:
            return AuditEventType.CUSTOM_AGENT_CREATED
        # ... etc
        return AuditEventType.DESIGN_REQUESTED

# Add to FastAPI app
app.add_middleware(AuditMiddleware)
```

### 6.2 RBAC & Organizational Controls (Weeks 5-8)

**Objective:** Add role-based access control and team management

**Implementation:**

1. **Define Roles** ([backend/auth/rbac.py](backend/auth/rbac.py))
```python
class Role(Enum):
    VIEWER = "viewer"  # Can view designs, no creation
    USER = "user"  # Can create designs, use built-in agents
    POWER_USER = "power_user"  # Can create custom agents, workflows
    ADMIN = "admin"  # Full access, manage users, view audit logs
    ORG_ADMIN = "org_admin"  # Manage organization settings

@dataclass
class Permission:
    name: str
    description: str

class Permissions:
    # Design permissions
    VIEW_DESIGNS = Permission("view_designs", "View design history")
    CREATE_DESIGNS = Permission("create_designs", "Create new designs")
    DELETE_DESIGNS = Permission("delete_designs", "Delete designs")

    # Agent permissions
    USE_BUILTIN_AGENTS = Permission("use_builtin_agents", "Use built-in agents")
    CREATE_CUSTOM_AGENTS = Permission("create_custom_agents", "Create custom agents")
    SHARE_AGENTS = Permission("share_agents", "Share agents with organization")

    # Workflow permissions
    CREATE_WORKFLOWS = Permission("create_workflows", "Create custom workflows")
    SHARE_WORKFLOWS = Permission("share_workflows", "Share workflows with organization")

    # Admin permissions
    VIEW_AUDIT_LOGS = Permission("view_audit_logs", "View audit logs")
    MANAGE_USERS = Permission("manage_users", "Manage users")
    MANAGE_ORG_SETTINGS = Permission("manage_org_settings", "Manage organization settings")

ROLE_PERMISSIONS = {
    Role.VIEWER: [
        Permissions.VIEW_DESIGNS,
        Permissions.USE_BUILTIN_AGENTS
    ],
    Role.USER: [
        Permissions.VIEW_DESIGNS,
        Permissions.CREATE_DESIGNS,
        Permissions.DELETE_DESIGNS,
        Permissions.USE_BUILTIN_AGENTS
    ],
    Role.POWER_USER: [
        Permissions.VIEW_DESIGNS,
        Permissions.CREATE_DESIGNS,
        Permissions.DELETE_DESIGNS,
        Permissions.USE_BUILTIN_AGENTS,
        Permissions.CREATE_CUSTOM_AGENTS,
        Permissions.CREATE_WORKFLOWS
    ],
    Role.ADMIN: [
        # All permissions
    ],
}

class RBACMiddleware:
    @staticmethod
    def check_permission(user: User, permission: Permission) -> bool:
        """Check if user has permission"""
        user_permissions = ROLE_PERMISSIONS.get(user.role, [])
        return permission in user_permissions

    @staticmethod
    def require_permission(permission: Permission):
        """Decorator to require permission for endpoint"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                user = kwargs.get('user')
                if not RBACMiddleware.check_permission(user, permission):
                    raise HTTPException(
                        status_code=403,
                        detail=f"Permission denied: {permission.description}"
                    )
                return await func(*args, **kwargs)
            return wrapper
        return decorator
```

2. **Add Organization Management** ([backend/organizations.py](backend/organizations.py))
```python
class Organization(BaseModel):
    id: str
    name: str
    created_at: datetime
    settings: OrganizationSettings

class OrganizationSettings(BaseModel):
    # Cost controls
    max_monthly_spend: Optional[float] = None
    require_approval_above: Optional[float] = None  # Require approval for designs above this cost

    # Agent controls
    allowed_agents: Optional[List[str]] = None  # If set, only these agents can be used
    blocked_agents: Optional[List[str]] = None

    # Workflow controls
    allowed_workflows: Optional[List[str]] = None
    require_security_review: bool = True
    require_cost_review: bool = True

    # Data controls
    data_retention_days: int = 90
    allow_external_sharing: bool = False

    # Compliance
    compliance_frameworks: List[str] = []  # e.g., ["SOC2", "HIPAA"]

@app.post("/organizations")
async def create_organization(
    org: Organization,
    user_id: str = Depends(get_current_user_id),
    user: User = Depends(require_permission(Permissions.MANAGE_ORG_SETTINGS))
):
    """Create new organization"""
    db = CarlosDatabase()
    await db.save_organization(org)
    return {"organization_id": org.id}

@app.get("/organizations/{org_id}/members")
async def list_organization_members(
    org_id: str,
    user: User = Depends(require_permission(Permissions.MANAGE_USERS))
):
    """List organization members"""
    db = CarlosDatabase()
    members = await db.get_organization_members(org_id)
    return {"members": members}

@app.post("/organizations/{org_id}/members")
async def add_organization_member(
    org_id: str,
    email: str,
    role: Role,
    user: User = Depends(require_permission(Permissions.MANAGE_USERS))
):
    """Add member to organization"""
    db = CarlosDatabase()
    await db.add_organization_member(org_id, email, role)
    return {"status": "success"}
```

### 6.3 Approval Workflows (Weeks 9-12)

**Objective:** Add approval gates for high-cost or sensitive designs

**Implementation:**

1. **Add Approval System** ([backend/approvals.py](backend/approvals.py))
```python
class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class ApprovalRequest(BaseModel):
    id: str
    design_id: str
    user_id: str
    organization_id: str
    requested_at: datetime
    reason: str  # Why approval is needed (e.g., "High cost", "Sensitive data")
    status: ApprovalStatus
    approver_id: Optional[str]
    approved_at: Optional[datetime]
    rejection_reason: Optional[str]

async def check_if_approval_needed(
    design_data: dict,
    user: User,
    org_settings: OrganizationSettings
) -> Optional[str]:
    """Check if design needs approval"""

    # Check cost threshold
    if org_settings.require_approval_above:
        estimated_cost = design_data.get("total_cost", 0)
        if estimated_cost > org_settings.require_approval_above:
            return f"Design cost (${estimated_cost:.2f}/month) exceeds approval threshold (${org_settings.require_approval_above:.2f})"

    # Check if uses sensitive services
    sensitive_services = ["Azure Key Vault", "Azure AD", "Cosmos DB"]
    if any(svc in design_data.get("services", []) for svc in sensitive_services):
        return "Design uses sensitive services requiring approval"

    # Check compliance requirements
    if org_settings.compliance_frameworks:
        return "Organization requires approval for all designs due to compliance requirements"

    return None

@app.post("/approvals/request")
async def request_approval(
    design_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Request approval for a design"""
    db = CarlosDatabase()

    design = await db.get_design(design_id)
    org_settings = await db.get_organization_settings(design["organization_id"])

    reason = await check_if_approval_needed(design, user, org_settings)
    if not reason:
        return {"approval_needed": False}

    approval_request = ApprovalRequest(
        id=str(uuid4()),
        design_id=design_id,
        user_id=user_id,
        organization_id=design["organization_id"],
        requested_at=datetime.utcnow(),
        reason=reason,
        status=ApprovalStatus.PENDING
    )

    await db.save_approval_request(approval_request)

    # Notify approvers
    await notify_approvers(approval_request)

    return {
        "approval_needed": True,
        "approval_id": approval_request.id,
        "reason": reason
    }

@app.post("/approvals/{approval_id}/approve")
async def approve_design(
    approval_id: str,
    user: User = Depends(require_permission(Permissions.MANAGE_USERS))
):
    """Approve a pending design"""
    db = CarlosDatabase()

    approval = await db.get_approval_request(approval_id)
    approval.status = ApprovalStatus.APPROVED
    approval.approver_id = user.id
    approval.approved_at = datetime.utcnow()

    await db.update_approval_request(approval)

    # Notify requester
    await notify_approval_decision(approval, approved=True)

    return {"status": "approved"}

@app.post("/approvals/{approval_id}/reject")
async def reject_design(
    approval_id: str,
    rejection_reason: str,
    user: User = Depends(require_permission(Permissions.MANAGE_USERS))
):
    """Reject a pending design"""
    db = CarlosDatabase()

    approval = await db.get_approval_request(approval_id)
    approval.status = ApprovalStatus.REJECTED
    approval.approver_id = user.id
    approval.approved_at = datetime.utcnow()
    approval.rejection_reason = rejection_reason

    await db.update_approval_request(approval)

    # Notify requester
    await notify_approval_decision(approval, approved=False)

    return {"status": "rejected", "reason": rejection_reason}
```

2. **Add Approval UI** ([frontend/src/components/Approvals.jsx](frontend/src/components/Approvals.jsx))
```jsx
export function ApprovalsQueue() {
  const [pendingApprovals, setPendingApprovals] = useState([]);

  useEffect(() => {
    loadPendingApprovals();
  }, []);

  const loadPendingApprovals = async () => {
    const response = await fetch(`${backendUrl}/approvals/pending`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
    });
    const data = await response.json();
    setPendingApprovals(data.approvals);
  };

  const handleApprove = async (approvalId) => {
    await fetch(`${backendUrl}/approvals/${approvalId}/approve`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
    });
    loadPendingApprovals();
  };

  const handleReject = async (approvalId, reason) => {
    await fetch(`${backendUrl}/approvals/${approvalId}/reject`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({ rejection_reason: reason })
    });
    loadPendingApprovals();
  };

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">⏳ Pending Approvals</h2>

      {pendingApprovals.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          No pending approvals
        </div>
      ) : (
        pendingApprovals.map(approval => (
          <ApprovalCard
            key={approval.id}
            approval={approval}
            onApprove={() => handleApprove(approval.id)}
            onReject={(reason) => handleReject(approval.id, reason)}
          />
        ))
      )}
    </div>
  );
}

function ApprovalCard({ approval, onApprove, onReject }) {
  const [showRejectDialog, setShowRejectDialog] = useState(false);
  const [rejectionReason, setRejectionReason] = useState('');

  return (
    <div className="bg-white border rounded-lg p-6 shadow">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="font-bold text-lg">Design Approval Request</h3>
          <p className="text-sm text-gray-600">
            From: {approval.user_email} • {formatDate(approval.requested_at)}
          </p>
        </div>
        <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm">
          Pending
        </span>
      </div>

      <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
        <p className="font-medium">Reason for approval:</p>
        <p>{approval.reason}</p>
      </div>

      <DesignSummary designId={approval.design_id} />

      <div className="flex gap-3 mt-4">
        <button
          onClick={onApprove}
          className="flex-1 bg-green-600 text-white py-2 rounded hover:bg-green-700"
        >
          ✓ Approve
        </button>
        <button
          onClick={() => setShowRejectDialog(true)}
          className="flex-1 bg-red-600 text-white py-2 rounded hover:bg-red-700"
        >
          ✗ Reject
        </button>
      </div>

      {showRejectDialog && (
        <RejectDialog
          onSubmit={(reason) => {
            onReject(reason);
            setShowRejectDialog(false);
          }}
          onCancel={() => setShowRejectDialog(false)}
        />
      )}
    </div>
  );
}
```

**Deliverables:**
- ✅ Complete audit trail for all operations
- ✅ Role-based access control (Viewer, User, Power User, Admin, Org Admin)
- ✅ Organization management with settings
- ✅ Team member management
- ✅ Approval workflows for high-cost/sensitive designs
- ✅ Approval queue UI for admins

**Cost Impact:**
- No additional infrastructure costs (uses existing Cosmos DB)

---

## Summary: Total Cost Impact

| Phase | Duration | Additional Monthly Cost | Notes |
|-------|----------|------------------------|-------|
| **Phase 1: Foundation** | 8-10 weeks | ~$26-29 | Cosmos DB + App Insights |
| **Phase 2: Reliability** | 8-10 weeks | ~$36-86 | Container Apps + Multi-region |
| **Phase 3: Learning** | 10-12 weeks | ~$76-80 | Cognitive Search + Embeddings |
| **Phase 4: Orchestration** | 10-12 weeks | $0 | Development only |
| **Phase 5: Cross-Domain** | 12-16 weeks | $0 | Development only |
| **Phase 6: Governance** | 10-12 weeks | $0 | Development only |
| **Total** | **58-72 weeks** | **~$138-195/month** | All enterprise features |

**Current Cost:** ~$30/month (AKS)
**Future Cost:** ~$168-225/month (all enterprise features)

**Cost Optimization Options:**
- Use Azure Reserved Instances (30-60% savings)
- Use Cosmos DB serverless (pay per request)
- Use Container Apps scale-to-zero (pay only when running)
- **Optimized Total:** ~$100-150/month

---

## Success Metrics

### Phase 1 Metrics
- ✅ 100% of designs persisted to Cosmos DB
- ✅ Application Insights capturing all telemetry
- ✅ Health checks passing 99.9% of the time
- ✅ Frontend history view functional

### Phase 2 Metrics
- ✅ Auto-scaling from 0 to 10 instances based on load
- ✅ 99.95% uptime SLA achieved
- ✅ Multi-region failover working (<5min)
- ✅ Point-in-time restore tested successfully

### Phase 3 Metrics
- ✅ Semantic search returning relevant designs (80%+ relevance)
- ✅ 50%+ of designs use historical insights
- ✅ User feedback submitted for 30%+ of designs
- ✅ Prompt optimization recommendations generated monthly

### Phase 4 Metrics
- ✅ Users can create custom workflows
- ✅ 20+ community-shared agents in marketplace
- ✅ 50%+ of users customize their workflows
- ✅ Average workflow execution time reduced 30%

### Phase 5 Metrics
- ✅ Support for AWS, GCP, and multi-cloud designs
- ✅ 5+ IaC formats supported
- ✅ 10+ domain agent packs available
- ✅ Real pricing data used in 80%+ of cost analyses

### Phase 6 Metrics
- ✅ Complete audit trail for all operations
- ✅ RBAC enforced across all endpoints
- ✅ 100+ organizations using Carlos
- ✅ Approval workflow processing time <2 hours

---

## Risk Mitigation

### Technical Risks

1. **LangGraph Migration to Dynamic Workflows**
   - **Risk:** Breaking existing functionality
   - **Mitigation:** Phased rollout, maintain backward compatibility, extensive testing

2. **Cosmos DB Performance at Scale**
   - **Risk:** Slow queries as data grows
   - **Mitigation:** Proper indexing, partitioning strategy, consider Cosmos DB autoscale

3. **Multi-Cloud Complexity**
   - **Risk:** Agent prompts too generic, quality degrades
   - **Mitigation:** Separate prompt adaptations per cloud, extensive testing

### Business Risks

1. **Cost Overruns**
   - **Risk:** Azure costs higher than estimated
   - **Mitigation:** Start with lower tiers, monitor costs daily, implement budget alerts

2. **User Adoption of New Features**
   - **Risk:** Users don't adopt custom workflows/agents
   - **Mitigation:** Excellent documentation, tutorials, community showcases

3. **Competitive Pressure**
   - **Risk:** Microsoft or others release competing solution
   - **Mitigation:** Focus on differentiation (cost optimization, competitive design approach)

---

## Conclusion

This roadmap transforms Carlos from a specialized tool into an **enterprise-grade AI automation platform** over 18 months, adding:

✅ **Enterprise-grade reliability** (99.95% uptime, auto-scaling, multi-region)
✅ **Auto-scaling and managed services** (Container Apps, Cosmos DB, Foundry)
✅ **Historical workflow learning** (vector search, feedback loops, prompt optimization)
✅ **Flexible orchestration patterns** (dynamic workflows, custom agents, visual builder)
✅ **Cross-domain applicability** (multi-cloud, multiple IaC formats, domain packs)
✅ **Production-ready audit and compliance** (RBAC, audit logs, approval workflows)

The total investment is ~**60-70 weeks of development** and **~$100-150/month in Azure costs**, positioning Carlos as a comprehensive enterprise solution while maintaining its core strengths in architecture design and cost optimization.
