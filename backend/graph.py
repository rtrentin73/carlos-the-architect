from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from tasks import (
    REQUIREMENTS_GATHERING_INSTRUCTIONS,
    CARLOS_INSTRUCTIONS,
    AUDITOR_INSTRUCTIONS,
    SECURITY_ANALYST_INSTRUCTIONS,
    COST_ANALYST_INSTRUCTIONS,
    RELIABILITY_ENGINEER_INSTRUCTIONS,
    RONEI_INSTRUCTIONS,
    DESIGN_RECOMMENDER_INSTRUCTIONS,
    TERRAFORM_CODER_INSTRUCTIONS,
)
import os
import operator

class CarlosState(TypedDict):
    requirements: str
    refined_requirements: str  # Requirements after clarification
    user_answers: str  # User's answers to clarification questions
    clarification_needed: bool  # Whether we need to gather more info
    design_doc: str
    ronei_design: str
    audit_status: str  # "pending", "approved", "needs_revision"
    audit_report: str
    recommendation: str
    conversation: Annotated[str, operator.add]  # running log of agent messages (concatenated when parallel)
    security_report: str
    cost_report: str
    reliability_report: str
    design_tokens: list  # Token chunks from Carlos for streaming
    ronei_tokens: list  # Token chunks from Ronei for streaming
    terraform_code: str  # Generated Terraform infrastructure code


def create_llm(temperature: float = 0.7):
    """Create LLM client - supports both Azure OpenAI and Azure AI Foundry."""
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    model = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")

    if not endpoint or not api_key:
        raise ValueError("AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY must be set")

    # Azure AI Foundry endpoints contain 'services.ai.azure.com'
    if "services.ai.azure.com" in endpoint:
        # Azure AI Foundry - use OpenAI-compatible client
        # Foundry inference endpoint format
        base_url = endpoint.rstrip("/")
        if not base_url.endswith("/models"):
            base_url = f"{base_url}/models"

        # Add api-version query parameter for Azure AI Foundry
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
        if "?" in base_url:
            base_url = f"{base_url}&api-version={api_version}"
        else:
            base_url = f"{base_url}?api-version={api_version}"

        return ChatOpenAI(
            model=model,
            base_url=base_url,
            api_key=api_key,
            temperature=temperature,
            default_headers={"api-key": api_key},
        )
    else:
        # Traditional Azure OpenAI
        return AzureChatOpenAI(
            azure_deployment=model,
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
            azure_endpoint=endpoint,
            api_key=api_key,
            temperature=temperature,
        )


# Lazy LLM initialization - created on first use
_llm = None
_ronei_llm = None


def get_llm():
    """Get or create the main LLM instance."""
    global _llm
    if _llm is None:
        _llm = create_llm(temperature=0.7)
    return _llm


def get_ronei_llm():
    """Get or create Ronei's LLM instance (more creative)."""
    global _ronei_llm
    if _ronei_llm is None:
        _ronei_llm = create_llm(temperature=0.9)
    return _ronei_llm


async def requirements_gathering_node(state: CarlosState):
    """Ask clarifying questions about requirements before designing."""
    prompt = (
        f"{REQUIREMENTS_GATHERING_INSTRUCTIONS}\n\n"
        f"Initial User Requirements:\n{state['requirements']}"
    )
    response = await get_llm().ainvoke(prompt)
    convo = state.get("conversation", "")
    convo += "**Requirements Team:**\n" + response.content + "\n\n"

    # Set refined_requirements to original for now - will be updated with user answers
    return {
        "refined_requirements": state['requirements'],
        "clarification_needed": True,
        "conversation": convo
    }


async def refine_requirements_node(state: CarlosState):
    """Refine requirements based on user's answers to clarifying questions."""
    user_answers = state.get('user_answers', '')

    if not user_answers:
        # No answers provided, use original requirements
        return {"refined_requirements": state['requirements']}

    # Create refined requirements by combining original + answers
    refine_prompt = f"""Given the initial requirements and the user's answers to clarifying questions,
create a comprehensive, refined requirements document that incorporates all the information.

Initial Requirements:
{state['requirements']}

User's Answers to Clarifying Questions:
{user_answers}

Create a single, well-structured requirements document that includes all relevant details from both.
Use markdown format with clear sections. Be specific and concrete."""

    response = await get_llm().ainvoke(refine_prompt)
    convo = state.get("conversation", "")
    convo += "**Refined Requirements:**\n" + response.content + "\n\n"

    return {
        "refined_requirements": response.content,
        "clarification_needed": False,
        "conversation": convo
    }


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

    # Use refined_requirements if available, otherwise fall back to original requirements
    requirements = state.get('refined_requirements') or state['requirements']

    prompt = f"{CARLOS_INSTRUCTIONS}\n\nUser requirements: {requirements}" + (
        f"\n\nAdditional context:\n{extra_context}" if extra_context else ""
    )
    response = ""
    tokens = []
    async for chunk in get_llm().astream(prompt):
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

    # Use refined_requirements if available, otherwise fall back to original requirements
    requirements = state.get('refined_requirements') or state['requirements']

    prompt = f"{RONEI_INSTRUCTIONS}\n\nUser requirements: {requirements}" + (
        f"\n\nAdditional context:\n{extra_context}" if extra_context else ""
    )
    response = ""
    tokens = []
    async for chunk in get_ronei_llm().astream(prompt):
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
    response = await get_llm().ainvoke(prompt)
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
    response = await get_llm().ainvoke(prompt)
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
    response = await get_llm().ainvoke(prompt)
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
    response = await get_llm().ainvoke(prompt)
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
    response = await get_llm().ainvoke(prompt)
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


async def terraform_coder_node(state: CarlosState):
    """Generate Terraform code for the recommended design."""
    # Determine which design was recommended
    recommendation = state.get("recommendation", "")
    recommended_design = state.get("design_doc", "")  # Default to Carlos

    if "RECOMMEND: RONEI" in recommendation.upper():
        recommended_design = state.get("ronei_design", "")

    prompt = (
        f"{TERRAFORM_CODER_INSTRUCTIONS}\n\n"
        f"=== User Requirements ===\n{state['requirements']}\n\n"
        f"=== Recommended Design ===\n{recommended_design}\n\n"
        f"=== Design Recommendation ===\n{recommendation}\n\n"
        f"Please generate production-ready Terraform code for this architecture."
    )
    response = await get_llm().ainvoke(prompt)
    convo = state.get("conversation", "")
    convo += "**Terraform Coder:**\n" + response.content + "\n\n"
    return {"terraform_code": response.content, "conversation": convo}

# Build graph
builder = StateGraph(CarlosState)
builder.add_node("requirements_gathering", requirements_gathering_node)
builder.add_node("refine_requirements", refine_requirements_node)
builder.add_node("design", carlos_design_node)
builder.add_node("ronei_design", ronei_design_node)
builder.add_node("security", security_node)
builder.add_node("cost", cost_node)
builder.add_node("reliability", reliability_node)
builder.add_node("audit", auditor_node)
builder.add_node("recommender", recommender_node)
builder.add_node("terraform_coder", terraform_coder_node)

# Conditional start: if user_answers exist, skip to refine_requirements, otherwise gather requirements
def should_gather_requirements(state):
    """Check if we need to gather requirements or if we already have answers."""
    return "requirements_gathering" if not state.get("user_answers") else "refine_requirements"

builder.add_conditional_edges(START, should_gather_requirements)

# After requirements gathering, check if we have answers
def check_for_answers(state):
    """After gathering requirements, check if user provided answers."""
    # If user_answers exist, go to refine_requirements to process them
    # Otherwise, end here and wait for user to provide answers
    return "refine_requirements" if state.get("user_answers") else END

builder.add_conditional_edges("requirements_gathering", check_for_answers)

# After refining requirements, run Carlos and Ronei in parallel
builder.add_edge("refine_requirements", "design")
builder.add_edge("refine_requirements", "ronei_design")

# Security waits for both designs to complete, then other specialists run sequentially
builder.add_edge("design", "security")
builder.add_edge("ronei_design", "security")
builder.add_edge("security", "cost")
builder.add_edge("cost", "reliability")
builder.add_edge("reliability", "audit")

builder.add_conditional_edges(
    "audit",
    lambda x: "recommender" if x["audit_status"] == "approved" else "design",
)

builder.add_edge("recommender", "terraform_coder")
builder.add_edge("terraform_coder", END)

carlos_graph = builder.compile()
