"""
Structured output schemas for Carlos the Architect agents.

These Pydantic models define the JSON structure for agent outputs,
enabling reliable parsing and programmatic analysis.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class ServiceCategory(str, Enum):
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORKING = "networking"
    DATABASE = "database"
    ANALYTICS = "analytics"
    SECURITY = "security"
    MONITORING = "monitoring"
    AI_ML = "ai_ml"
    IDENTITY = "identity"
    OTHER = "other"


class AzureService(BaseModel):
    """Individual Azure service in the design"""
    name: str = Field(description="Service name (e.g., 'Azure Kubernetes Service')")
    sku: str = Field(description="SKU/tier (e.g., 'Standard_B2s')")
    quantity: int = Field(default=1, description="Number of instances")
    monthly_cost_usd: float = Field(description="Estimated monthly cost in USD")
    category: ServiceCategory = Field(description="Service category")
    notes: Optional[str] = Field(default=None, description="Additional notes about configuration")


class CostAnalysis(BaseModel):
    """Structured cost analysis output from Cost Analyst agent"""
    total_monthly_cost_usd: float = Field(description="Total estimated monthly cost")
    total_annual_cost_usd: float = Field(description="Total estimated annual cost")
    services: List[AzureService] = Field(description="List of Azure services with costs")
    cost_breakdown_by_category: dict = Field(
        description="Cost breakdown by category (category -> monthly cost)"
    )
    cost_drivers: List[str] = Field(
        description="Top 3-5 services driving the cost"
    )
    optimization_opportunities: List[str] = Field(
        description="Specific cost optimization recommendations"
    )
    reserved_instance_savings: Optional[float] = Field(
        default=None,
        description="Potential savings with reserved instances (percentage)"
    )
    cost_confidence: str = Field(
        default="medium",
        description="Confidence level: low, medium, high"
    )


class SecurityFinding(BaseModel):
    """Individual security finding"""
    severity: str = Field(description="Severity: critical, high, medium, low")
    title: str = Field(description="Short title of the finding")
    description: str = Field(description="Detailed description of the issue")
    recommendation: str = Field(description="How to remediate the issue")
    affected_services: List[str] = Field(description="Services affected by this finding")
    cwe_id: Optional[str] = Field(default=None, description="CWE identifier if applicable")


class SecurityAnalysis(BaseModel):
    """Structured security analysis output from Security Analyst agent"""
    overall_security_score: int = Field(ge=0, le=100, description="Security score 0-100")
    findings: List[SecurityFinding] = Field(description="List of security findings")
    compliance_frameworks: List[str] = Field(
        description="Compliance frameworks this design aligns with (e.g., SOC2, HIPAA, PCI-DSS)"
    )
    security_controls: List[str] = Field(
        description="Security controls implemented in the design"
    )
    encryption_at_rest: bool = Field(description="Whether data at rest is encrypted")
    encryption_in_transit: bool = Field(description="Whether data in transit is encrypted")
    identity_management: str = Field(
        description="Identity management approach (e.g., 'Azure AD with RBAC')"
    )
    network_segmentation: bool = Field(description="Whether network is properly segmented")
    critical_findings_count: int = Field(description="Number of critical findings")
    high_findings_count: int = Field(description="Number of high severity findings")


class ReliabilityMetrics(BaseModel):
    """Structured reliability analysis output from SRE agent"""
    estimated_sla_percentage: float = Field(
        ge=0, le=100,
        description="Estimated composite SLA percentage"
    )
    single_points_of_failure: List[str] = Field(
        description="Identified single points of failure"
    )
    redundancy_measures: List[str] = Field(
        description="Redundancy measures in place"
    )
    disaster_recovery_rto_hours: Optional[float] = Field(
        default=None,
        description="Recovery Time Objective in hours"
    )
    disaster_recovery_rpo_hours: Optional[float] = Field(
        default=None,
        description="Recovery Point Objective in hours"
    )
    monitoring_recommendations: List[str] = Field(
        description="Recommended monitoring and alerting"
    )
    scaling_approach: str = Field(
        description="Scaling strategy (manual, auto-scaling, etc.)"
    )
    backup_strategy: str = Field(
        description="Backup strategy description"
    )
    availability_zones: bool = Field(
        description="Whether design uses multiple availability zones"
    )
    multi_region: bool = Field(
        description="Whether design spans multiple regions"
    )
    health_check_endpoints: List[str] = Field(
        default=[],
        description="Recommended health check endpoints"
    )


def format_cost_analysis(cost_data: CostAnalysis) -> str:
    """Convert structured cost data to markdown for display"""
    md = f"""## Cost Analysis

**Total Monthly Cost:** ${cost_data.total_monthly_cost_usd:,.2f}
**Total Annual Cost:** ${cost_data.total_annual_cost_usd:,.2f}
**Confidence:** {cost_data.cost_confidence.title()}

### Cost Breakdown by Category

"""
    for category, cost in cost_data.cost_breakdown_by_category.items():
        md += f"- **{category.replace('_', ' ').title()}:** ${cost:,.2f}/month\n"

    md += "\n### Services\n\n"
    md += "| Service | SKU | Qty | Monthly Cost |\n"
    md += "|---------|-----|-----|-------------|\n"
    for svc in cost_data.services:
        md += f"| {svc.name} | {svc.sku} | {svc.quantity} | ${svc.monthly_cost_usd:,.2f} |\n"

    md += "\n### Cost Drivers\n\n"
    for i, driver in enumerate(cost_data.cost_drivers, 1):
        md += f"{i}. {driver}\n"

    md += "\n### Optimization Opportunities\n\n"
    for opp in cost_data.optimization_opportunities:
        md += f"- {opp}\n"

    if cost_data.reserved_instance_savings:
        md += f"\n**Potential RI Savings:** {cost_data.reserved_instance_savings:.0f}%\n"

    return md


def format_security_analysis(security_data: SecurityAnalysis) -> str:
    """Convert structured security data to markdown for display"""
    # Determine score color/emoji
    score = security_data.overall_security_score
    if score >= 80:
        score_indicator = "🟢"
    elif score >= 60:
        score_indicator = "🟡"
    else:
        score_indicator = "🔴"

    md = f"""## Security Analysis

**Overall Security Score:** {score_indicator} {score}/100

**Critical Findings:** {security_data.critical_findings_count}
**High Severity Findings:** {security_data.high_findings_count}

### Security Controls

"""
    for control in security_data.security_controls:
        md += f"- ✅ {control}\n"

    md += f"""
### Encryption Status

- **Data at Rest:** {"✅ Encrypted" if security_data.encryption_at_rest else "❌ Not encrypted"}
- **Data in Transit:** {"✅ Encrypted" if security_data.encryption_in_transit else "❌ Not encrypted"}

### Identity & Access

- **Identity Management:** {security_data.identity_management}
- **Network Segmentation:** {"✅ Yes" if security_data.network_segmentation else "❌ No"}

### Compliance Alignment

"""
    for framework in security_data.compliance_frameworks:
        md += f"- {framework}\n"

    if security_data.findings:
        md += "\n### Security Findings\n\n"
        for finding in security_data.findings:
            severity_emoji = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢"
            }.get(finding.severity.lower(), "⚪")

            md += f"""#### {severity_emoji} {finding.title}

**Severity:** {finding.severity.upper()}
**Affected Services:** {', '.join(finding.affected_services)}

{finding.description}

**Recommendation:** {finding.recommendation}

"""

    return md


def format_reliability_analysis(reliability_data: ReliabilityMetrics) -> str:
    """Convert structured reliability data to markdown for display"""
    sla = reliability_data.estimated_sla_percentage
    if sla >= 99.9:
        sla_indicator = "🟢"
    elif sla >= 99:
        sla_indicator = "🟡"
    else:
        sla_indicator = "🔴"

    md = f"""## Reliability Analysis

**Estimated SLA:** {sla_indicator} {sla:.2f}%

### High Availability Features

- **Availability Zones:** {"✅ Yes" if reliability_data.availability_zones else "❌ No"}
- **Multi-Region:** {"✅ Yes" if reliability_data.multi_region else "❌ No"}
- **Scaling Approach:** {reliability_data.scaling_approach}

### Disaster Recovery

"""
    if reliability_data.disaster_recovery_rto_hours:
        md += f"- **RTO:** {reliability_data.disaster_recovery_rto_hours:.1f} hours\n"
    if reliability_data.disaster_recovery_rpo_hours:
        md += f"- **RPO:** {reliability_data.disaster_recovery_rpo_hours:.1f} hours\n"
    md += f"- **Backup Strategy:** {reliability_data.backup_strategy}\n"

    if reliability_data.single_points_of_failure:
        md += "\n### Single Points of Failure ⚠️\n\n"
        for spof in reliability_data.single_points_of_failure:
            md += f"- {spof}\n"
    else:
        md += "\n### Single Points of Failure\n\n✅ No single points of failure identified\n"

    md += "\n### Redundancy Measures\n\n"
    for measure in reliability_data.redundancy_measures:
        md += f"- ✅ {measure}\n"

    md += "\n### Monitoring Recommendations\n\n"
    for rec in reliability_data.monitoring_recommendations:
        md += f"- {rec}\n"

    return md
