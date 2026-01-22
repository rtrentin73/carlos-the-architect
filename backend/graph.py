from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langchain_openai import AzureChatOpenAI
from tasks import (
    CARLOS_INSTRUCTIONS,
    AUDITOR_INSTRUCTIONS,
    SECURITY_ANALYST_INSTRUCTIONS,
    COST_ANALYST_INSTRUCTIONS,
    RELIABILITY_ENGINEER_INSTRUCTIONS,
    RONEI_INSTRUCTIONS,
    DESIGN_RECOMMENDER_INSTRUCTIONS,
)
import os

class CarlosState(TypedDict):
    requirements: str
    design_doc: str
    ronei_design: str
    audit_status: str  # "pending", "approved", "needs_revision"
    audit_report: str
    recommendation: str
    conversation: str  # running log of agent messages
    security_report: str
    cost_report: str
    reliability_report: str
    design_tokens: list  # Token chunks from Carlos for streaming
    ronei_tokens: list  # Token chunks from Ronei for streaming

# Create LLM with explicit env vars
llm = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    temperature=0.7,
)

# Ronei's LLM - more creative and sassy
ronei_llm = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    temperature=0.9,  # Higher temperature for more creative/sassy responses
)

async def carlos_design_node(state: CarlosState):
    """Carlos drafts the infrastructure"""
    scenario = state.get("scenario")
    priorities = state.get("priorities", {}) or {}

    context_lines = []
    if scenario and scenario != "custom":
        context_lines.append(f"Scenario preset: {scenario} (interpret and adapt as needed).")

    cp = priorities.get("cost_performance")
    if cp == "cost_optimized":
        context_lines.append("Non-functional priority: minimize monthly cost while keeping the design sane.")
    elif cp == "performance_optimized":
        context_lines.append("Non-functional priority: favor performance and low latency, even at higher cost.")
    elif cp == "balanced":
        context_lines.append("Non-functional priority: balanced cost vs performance.")

    compliance = priorities.get("compliance")
    if compliance == "regulated":
        context_lines.append("Assume a regulated workload (e.g., PCI/HIPAA); call out controls explicitly.")
    elif compliance == "strict":
        context_lines.append("Assume very strict compliance/government requirements; be conservative.")

    rel = priorities.get("reliability")
    if rel == "high":
        context_lines.append("Target high availability (around 99.9–99.99%) with appropriate redundancy.")
    elif rel == "extreme":
        context_lines.append("Target extreme reliability with multi-region or multi-AZ resilience.")

    strict = priorities.get("strictness")
    if strict == "flexible":
        context_lines.append(
            "Design can be flexible: mix managed services, containers, and Kubernetes if it clearly helps. No hard guardrails."
        )
    elif strict == "balanced":
        context_lines.append(
            "Be opinionated but pragmatic: prefer managed/PaaS services and only introduce Kubernetes or complex stacks when clearly justified."
        )
    elif strict == "strict":
        context_lines.append(
            "Be strongly opinionated: stick to AWS-native managed services where possible, avoid Kubernetes unless absolutely necessary, and avoid unnecessary complexity."
        )

    extra_context = "\n".join(context_lines)

    prompt = f"{CARLOS_INSTRUCTIONS}\n\nUser requirements: {state['requirements']}" + (
        f"\n\nAdditional context:\n{extra_context}" if extra_context else ""
    )
    response = ""
    tokens = []
    async for chunk in llm.astream(prompt):
        token = chunk.content
        response += token
        tokens.append(token)
    print(f"Design response: {response}")
    convo = state.get("conversation", "")
    convo += "**Carlos:**\n" + response + "\n\n"
    return {"design_doc": response, "audit_status": "pending", "conversation": convo, "design_tokens": tokens}


async def ronei_design_node(state: CarlosState):
    """Ronei drafts a competing infrastructure design"""
    scenario = state.get("scenario")
    priorities = state.get("priorities", {}) or {}

    context_lines = []
    if scenario and scenario != "custom":
        context_lines.append(f"Scenario preset: {scenario} (I'll show Carlos how it's really done).")

    cp = priorities.get("cost_performance")
    if cp == "cost_optimized":
        context_lines.append("Non-functional priority: optimize for innovation and velocity, cost is secondary.")
    elif cp == "performance_optimized":
        context_lines.append("Non-functional priority: bleeding-edge performance with the latest tech.")
    elif cp == "balanced":
        context_lines.append("Non-functional priority: modern balance with cutting-edge solutions.")

    compliance = priorities.get("compliance")
    if compliance == "regulated":
        context_lines.append("Compliance: I'll handle it with modern zero-trust and service mesh magic.")
    elif compliance == "strict":
        context_lines.append("Compliance: Government level? No problem, I'll containerize security itself!")

    rel = priorities.get("reliability")
    if rel == "high":
        context_lines.append("Reliability: High availability with Kubernetes chaos engineering.")
    elif rel == "extreme":
        context_lines.append("Reliability: Extreme resilience with multi-cloud and service mesh.")

    strict = priorities.get("strictness")
    if strict == "flexible":
        context_lines.append("Design freedom: Unleashed! Kubernetes, serverless, edge computing - bring it on!")
    elif strict == "balanced":
        context_lines.append("Design approach: Modern and pragmatic, but I'll push the envelope.")
    elif strict == "strict":
        context_lines.append("Design constraints: Even if Carlos says no, I'll find a way to modernize!")

    extra_context = "\n".join(context_lines)

    prompt = f"{RONEI_INSTRUCTIONS}\n\nUser requirements: {state['requirements']}" + (
        f"\n\nAdditional context:\n{extra_context}" if extra_context else ""
    )
    response = ""
    tokens = []
    async for chunk in ronei_llm.astream(prompt):
        token = chunk.content
        response += token
        tokens.append(token)
    print(f"Ronei design response: {response}")
    convo = state.get("conversation", "")
    convo += "**Ronei:**\n" + response + "\n\n"
    return {"ronei_design": response, "conversation": convo, "ronei_tokens": tokens}


async def security_node(state: CarlosState):
    """Security analyst reviews the design."""
    prompt = (
        f"{SECURITY_ANALYST_INSTRUCTIONS}\n\n"
        f"=== Carlos' Design ===\n{state['design_doc']}\n\n"
        f"=== Ronei's Design ===\n{state.get('ronei_design', '')}\n\n"
        f"Please review both designs from a security perspective."
    )
    response = await llm.ainvoke(prompt)
    convo = state.get("conversation", "")
    convo += "**Security Analyst:**\n" + response.content + "\n\n"
    return {"security_report": response.content, "conversation": convo}


async def cost_node(state: CarlosState):
    """Cost optimization specialist reviews the design."""
    prompt = (
        f"{COST_ANALYST_INSTRUCTIONS}\n\n"
        f"=== Carlos' Design ===\n{state['design_doc']}\n\n"
        f"=== Ronei's Design ===\n{state.get('ronei_design', '')}\n\n"
        f"Please review both designs from a cost optimization perspective."
    )
    response = await llm.ainvoke(prompt)
    convo = state.get("conversation", "")
    convo += "**Cost Specialist:**\n" + response.content + "\n\n"
    return {"cost_report": response.content, "conversation": convo}


async def reliability_node(state: CarlosState):
    """SRE reviews the design."""
    prompt = (
        f"{RELIABILITY_ENGINEER_INSTRUCTIONS}\n\n"
        f"=== Carlos' Design ===\n{state['design_doc']}\n\n"
        f"=== Ronei's Design ===\n{state.get('ronei_design', '')}\n\n"
        f"Please review both designs from a reliability and operations perspective."
    )
    response = await llm.ainvoke(prompt)
    convo = state.get("conversation", "")
    convo += "**SRE:**\n" + response.content + "\n\n"
    return {"reliability_report": response.content, "conversation": convo}

async def auditor_node(state: CarlosState):
    """Final auditor aggregates all specialist feedback."""
    prompt = (
        f"{AUDITOR_INSTRUCTIONS}\n\n"
        f"=== Carlos' Design ===\n{state['design_doc']}\n\n"
        f"=== Ronei's Design ===\n{state.get('ronei_design', '')}\n\n"
        f"=== Security Report ===\n{state.get('security_report', '')}\n\n"
        f"=== Cost Report ===\n{state.get('cost_report', '')}\n\n"
        f"=== Reliability Report ===\n{state.get('reliability_report', '')}\n\n"
    )
    response = await llm.ainvoke(prompt)
    status = "approved" if "APPROVED" in response.content.upper() else "needs_revision"
    convo = state.get("conversation", "")
    convo += "**Chief Auditor:**\n" + response.content + "\n\n"
    return {"audit_status": status, "audit_report": response.content, "conversation": convo}


async def recommender_node(state: CarlosState):
    """Recommend Carlos vs Ronei based on all outputs."""
    prompt = (
        f"{DESIGN_RECOMMENDER_INSTRUCTIONS}\n\n"
        f"=== User Requirements ===\n{state['requirements']}\n\n"
        f"=== Carlos' Design ===\n{state.get('design_doc', '')}\n\n"
        f"=== Ronei's Design ===\n{state.get('ronei_design', '')}\n\n"
        f"=== Security Report ===\n{state.get('security_report', '')}\n\n"
        f"=== Cost Report ===\n{state.get('cost_report', '')}\n\n"
        f"=== Reliability Report ===\n{state.get('reliability_report', '')}\n\n"
        f"=== Chief Auditor Verdict ===\n{state.get('audit_report', '')}\n\n"
    )
    response = await llm.ainvoke(prompt)
    content = (response.content or "").strip()
    upper = content.upper()
    if not (upper.startswith("RECOMMEND: CARLOS") or upper.startswith("RECOMMEND: RONEI")):
        if "CARLOS" in upper and "RONEI" not in upper:
            content = "RECOMMEND: CARLOS\n\n" + content
        elif "RONEI" in upper and "CARLOS" not in upper:
            content = "RECOMMEND: RONEI\n\n" + content
        else:
            content = "RECOMMEND: CARLOS\n\n" + content
    convo = state.get("conversation", "")
    convo += "**Design Recommender:**\n" + content + "\n\n"
    return {"recommendation": content, "conversation": convo}

# Build graph
builder = StateGraph(CarlosState)
builder.add_node("design", carlos_design_node)
builder.add_node("ronei_design", ronei_design_node)
builder.add_node("security", security_node)
builder.add_node("cost", cost_node)
builder.add_node("reliability", reliability_node)
builder.add_node("audit", auditor_node)
builder.add_node("recommender", recommender_node)

builder.add_edge(START, "design")
builder.add_edge("design", "ronei_design")
builder.add_edge("ronei_design", "security")
builder.add_edge("security", "cost")
builder.add_edge("cost", "reliability")
builder.add_edge("reliability", "audit")

builder.add_conditional_edges(
    "audit",
    lambda x: "recommender" if x["audit_status"] == "approved" else "design",
)

builder.add_edge("recommender", END)

carlos_graph = builder.compile()
