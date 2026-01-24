from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage
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
from llm_pool import get_pool
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
    terraform_tokens: list  # Token chunks from Terraform Coder for streaming
    # Token fields for all streaming agents
    requirements_tokens: list  # Token chunks from Requirements Gathering
    refine_tokens: list  # Token chunks from Refine Requirements
    security_tokens: list  # Token chunks from Security Analyst
    cost_tokens: list  # Token chunks from Cost Analyst
    reliability_tokens: list  # Token chunks from Reliability Engineer
    audit_tokens: list  # Token chunks from Auditor
    recommender_tokens: list  # Token chunks from Recommender


# Connection pool is now managed in llm_pool.py
# Agents will use pool context managers: pool.get_main_llm(), pool.get_ronei_llm(), pool.get_mini_llm()


async def requirements_gathering_node(state: CarlosState):
    """Ask clarifying questions about requirements before designing (uses mini model with streaming)."""
    pool = get_pool()
    messages = [
        SystemMessage(content=REQUIREMENTS_GATHERING_INSTRUCTIONS),
        HumanMessage(content=f"Initial User Requirements:\n{state['requirements']}")
    ]
    response = ""
    tokens = []
    async with pool.get_mini_llm() as llm:
        async for chunk in llm.astream(messages):
            token = chunk.content
            response += token
            tokens.append(token)
    convo = state.get("conversation", "")
    convo += "**Requirements Team:**\n" + response + "\n\n"

    # Set refined_requirements to original for now - will be updated with user answers
    return {
        "refined_requirements": state['requirements'],
        "clarification_needed": True,
        "conversation": convo,
        "requirements_tokens": tokens
    }


async def refine_requirements_node(state: CarlosState):
    """Refine requirements based on user's answers (uses mini model with streaming)."""
    user_answers = state.get('user_answers', '')

    if not user_answers:
        # No answers provided, use original requirements
        return {"refined_requirements": state['requirements'], "refine_tokens": []}

    # Create refined requirements by combining original + answers
    system_instruction = """Given the initial requirements and the user's answers to clarifying questions,
create a comprehensive, refined requirements document that incorporates all the information.
Create a single, well-structured requirements document that includes all relevant details from both.
Use markdown format with clear sections. Be specific and concrete."""

    user_content = f"""Initial Requirements:
{state['requirements']}

User's Answers to Clarifying Questions:
{user_answers}"""

    messages = [
        SystemMessage(content=system_instruction),
        HumanMessage(content=user_content)
    ]

    pool = get_pool()
    response = ""
    tokens = []
    async with pool.get_mini_llm() as llm:
        async for chunk in llm.astream(messages):
            token = chunk.content
            response += token
            tokens.append(token)
    convo = state.get("conversation", "")
    convo += "**Refined Requirements:**\n" + response + "\n\n"

    return {
        "refined_requirements": response,
        "clarification_needed": False,
        "conversation": convo,
        "refine_tokens": tokens
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

    user_content = f"User requirements: {requirements}"
    if extra_context:
        user_content += f"\n\nAdditional context:\n{extra_context}"

    messages = [
        SystemMessage(content=CARLOS_INSTRUCTIONS),
        HumanMessage(content=user_content)
    ]

    pool = get_pool()
    response = ""
    tokens = []
    async with pool.get_main_llm() as llm:
        async for chunk in llm.astream(messages):
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

    user_content = f"User requirements: {requirements}"
    if extra_context:
        user_content += f"\n\nAdditional context:\n{extra_context}"

    messages = [
        SystemMessage(content=RONEI_INSTRUCTIONS),
        HumanMessage(content=user_content)
    ]

    pool = get_pool()
    response = ""
    tokens = []
    async with pool.get_ronei_llm() as llm:
        async for chunk in llm.astream(messages):
            token = chunk.content
            response += token
            tokens.append(token)
    print(f"Ronei design response: {response}")
    convo = state.get("conversation", "")
    convo += "**Ronei:**\n" + response + "\n\n"
    return {"ronei_design": response, "conversation": convo, "ronei_tokens": tokens}


async def security_node(state: CarlosState):
    """Security analyst reviews the design (uses mini model with streaming)."""
    user_content = (
        f"=== Carlos' Design ===\n{state['design_doc']}\n\n"
        f"=== Ronei's Design ===\n{state.get('ronei_design', '')}\n\n"
        f"Please review both designs from a security perspective."
    )
    messages = [
        SystemMessage(content=SECURITY_ANALYST_INSTRUCTIONS),
        HumanMessage(content=user_content)
    ]
    pool = get_pool()
    response = ""
    tokens = []
    async with pool.get_mini_llm() as llm:
        async for chunk in llm.astream(messages):
            token = chunk.content
            response += token
            tokens.append(token)
    convo = state.get("conversation", "")
    convo += "**Security Analyst:**\n" + response + "\n\n"
    return {"security_report": response, "conversation": convo, "security_tokens": tokens}


async def cost_node(state: CarlosState):
    """Cost optimization specialist reviews the design (uses mini model with streaming)."""
    user_content = (
        f"=== Carlos' Design ===\n{state['design_doc']}\n\n"
        f"=== Ronei's Design ===\n{state.get('ronei_design', '')}\n\n"
        f"Please review both designs from a cost optimization perspective."
    )
    messages = [
        SystemMessage(content=COST_ANALYST_INSTRUCTIONS),
        HumanMessage(content=user_content)
    ]
    pool = get_pool()
    response = ""
    tokens = []
    async with pool.get_mini_llm() as llm:
        async for chunk in llm.astream(messages):
            token = chunk.content
            response += token
            tokens.append(token)
    convo = state.get("conversation", "")
    convo += "**Cost Specialist:**\n" + response + "\n\n"
    return {"cost_report": response, "conversation": convo, "cost_tokens": tokens}


async def reliability_node(state: CarlosState):
    """SRE reviews the design (uses mini model with streaming)."""
    user_content = (
        f"=== Carlos' Design ===\n{state['design_doc']}\n\n"
        f"=== Ronei's Design ===\n{state.get('ronei_design', '')}\n\n"
        f"Please review both designs from a reliability and operations perspective."
    )
    messages = [
        SystemMessage(content=RELIABILITY_ENGINEER_INSTRUCTIONS),
        HumanMessage(content=user_content)
    ]
    pool = get_pool()
    response = ""
    tokens = []
    async with pool.get_mini_llm() as llm:
        async for chunk in llm.astream(messages):
            token = chunk.content
            response += token
            tokens.append(token)
    convo = state.get("conversation", "")
    convo += "**SRE:**\n" + response + "\n\n"
    return {"reliability_report": response, "conversation": convo, "reliability_tokens": tokens}

async def auditor_node(state: CarlosState):
    """Final auditor aggregates all specialist feedback (uses streaming)."""
    user_content = (
        f"=== Carlos' Design ===\n{state['design_doc']}\n\n"
        f"=== Ronei's Design ===\n{state.get('ronei_design', '')}\n\n"
        f"=== Security Report ===\n{state.get('security_report', '')}\n\n"
        f"=== Cost Report ===\n{state.get('cost_report', '')}\n\n"
        f"=== Reliability Report ===\n{state.get('reliability_report', '')}\n\n"
    )
    messages = [
        SystemMessage(content=AUDITOR_INSTRUCTIONS),
        HumanMessage(content=user_content)
    ]
    pool = get_pool()
    response = ""
    tokens = []
    async with pool.get_main_llm() as llm:
        async for chunk in llm.astream(messages):
            token = chunk.content
            response += token
            tokens.append(token)
    status = "approved" if "APPROVED" in response.upper() else "needs_revision"
    convo = state.get("conversation", "")
    convo += "**Chief Auditor:**\n" + response + "\n\n"
    return {"audit_status": status, "audit_report": response, "conversation": convo, "audit_tokens": tokens}


async def recommender_node(state: CarlosState):
    """Recommend Carlos vs Ronei based on all outputs (uses streaming)."""
    user_content = (
        f"=== User Requirements ===\n{state['requirements']}\n\n"
        f"=== Carlos' Design ===\n{state.get('design_doc', '')}\n\n"
        f"=== Ronei's Design ===\n{state.get('ronei_design', '')}\n\n"
        f"=== Security Report ===\n{state.get('security_report', '')}\n\n"
        f"=== Cost Report ===\n{state.get('cost_report', '')}\n\n"
        f"=== Reliability Report ===\n{state.get('reliability_report', '')}\n\n"
        f"=== Chief Auditor Verdict ===\n{state.get('audit_report', '')}\n\n"
    )
    messages = [
        SystemMessage(content=DESIGN_RECOMMENDER_INSTRUCTIONS),
        HumanMessage(content=user_content)
    ]
    pool = get_pool()
    response = ""
    tokens = []
    async with pool.get_main_llm() as llm:
        async for chunk in llm.astream(messages):
            token = chunk.content
            response += token
            tokens.append(token)
    content = response.strip()
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
    return {"recommendation": content, "conversation": convo, "recommender_tokens": tokens}


async def terraform_coder_node(state: CarlosState):
    """Generate Terraform code for the recommended design with streaming."""
    # Determine which design was recommended
    recommendation = state.get("recommendation", "")
    recommended_design = state.get("design_doc", "")  # Default to Carlos

    if "RECOMMEND: RONEI" in recommendation.upper():
        recommended_design = state.get("ronei_design", "")

    user_content = (
        f"=== User Requirements ===\n{state['requirements']}\n\n"
        f"=== Recommended Design ===\n{recommended_design}\n\n"
        f"=== Design Recommendation ===\n{recommendation}\n\n"
        f"Please generate production-ready Terraform code for this architecture."
    )
    messages = [
        SystemMessage(content=TERRAFORM_CODER_INSTRUCTIONS),
        HumanMessage(content=user_content)
    ]

    pool = get_pool()
    terraform_code = ""
    tokens = []

    async with pool.get_main_llm() as llm:
        async for chunk in llm.astream(messages):
            token = chunk.content
            terraform_code += token
            tokens.append(token)

    convo = state.get("conversation", "")
    convo += "**Terraform Coder:**\n" + terraform_code + "\n\n"
    return {"terraform_code": terraform_code, "conversation": convo, "terraform_tokens": tokens}

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

# All three analysts (Security, Cost, Reliability) run in parallel after both designs complete
# This runs 3x faster than the previous sequential approach
builder.add_edge("design", "security")
builder.add_edge("ronei_design", "security")
builder.add_edge("design", "cost")
builder.add_edge("ronei_design", "cost")
builder.add_edge("design", "reliability")
builder.add_edge("ronei_design", "reliability")

# Audit waits for all three analysts to complete
builder.add_edge("security", "audit")
builder.add_edge("cost", "audit")
builder.add_edge("reliability", "audit")

builder.add_conditional_edges(
    "audit",
    lambda x: "recommender" if x["audit_status"] == "approved" else "design",
)

builder.add_edge("recommender", "terraform_coder")
builder.add_edge("terraform_coder", END)

carlos_graph = builder.compile()
