from typing import TypedDict, Annotated, Optional
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage
from historical_learning import get_historical_context
from reference_search import get_reference_context
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
    TERRAFORM_VALIDATOR_INSTRUCTIONS,
    TERRAFORM_CODER_CORRECTOR_INSTRUCTIONS,
)
from llm_pool import get_pool
from schemas import (
    CostAnalysis,
    SecurityAnalysis,
    ReliabilityMetrics,
    format_cost_analysis,
    format_security_analysis,
    format_reliability_analysis,
)
import operator
import json

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
    terraform_validation: str  # Validation report from Terraform Validator
    terraform_validator_tokens: list  # Token chunks from Terraform Validator for streaming
    # Terraform feedback loop fields
    terraform_correction_iteration: int  # Track correction attempts (max 2-3)
    terraform_validation_status: str  # PASS, PASS_WITH_WARNINGS, or NEEDS_FIXES
    terraform_corrector_tokens: list  # Token chunks from Terraform Corrector for streaming
    # Token fields for all streaming agents
    requirements_tokens: list  # Token chunks from Requirements Gathering
    refine_tokens: list  # Token chunks from Refine Requirements
    security_tokens: list  # Token chunks from Security Analyst
    cost_tokens: list  # Token chunks from Cost Analyst
    reliability_tokens: list  # Token chunks from Reliability Engineer
    audit_tokens: list  # Token chunks from Auditor
    recommender_tokens: list  # Token chunks from Recommender
    # Structured data fields for programmatic access
    cost_data: Optional[dict]  # Structured cost analysis data
    security_data: Optional[dict]  # Structured security analysis data
    reliability_data: Optional[dict]  # Structured reliability metrics data
    # Historical learning context from past feedback
    historical_context: str  # Learning context from past deployments
    # Reference search context from web search
    reference_context: str  # Formatted references for prompts
    references: list  # Structured reference data for frontend


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


async def historical_learning_node(state: CarlosState):
    """Fetch historical context from past deployment feedback before design generation.

    This node queries the feedback store for similar past designs and extracts
    patterns that worked well (high ratings) and patterns to avoid (issues).
    The context is injected into design prompts to help Carlos and Ronei learn
    from real deployment outcomes.
    """
    requirements = state.get('refined_requirements') or state['requirements']
    priorities = state.get("priorities", {}) or {}

    # Get cloud provider hint from priorities if available
    cloud_provider = priorities.get("cloud_provider")

    try:
        historical_context = await get_historical_context(
            requirements=requirements,
            cloud_provider=cloud_provider
        )
        if historical_context:
            print(f"  Historical context loaded: {len(historical_context)} chars")
        else:
            print("  No relevant historical context found")
    except Exception as e:
        print(f"  Historical learning error (continuing without): {e}")
        historical_context = ""

    return {"historical_context": historical_context}


async def reference_search_node(state: CarlosState):
    """Search for relevant documentation and best practices before design generation.

    This node queries the web for architecture references, best practices,
    and documentation relevant to the user's requirements. The results are
    injected into design prompts so Carlos and Ronei can cite authoritative sources.
    """
    requirements = state.get('refined_requirements') or state['requirements']
    priorities = state.get("priorities", {}) or {}

    # Get cloud provider hint from priorities if available
    cloud_provider = priorities.get("cloud_provider")

    try:
        reference_context, references = await get_reference_context(
            requirements=requirements,
            cloud_provider=cloud_provider
        )
        if reference_context:
            print(f"  Reference context loaded: {len(reference_context)} chars, {len(references)} refs")
        else:
            print("  No references found (search may be disabled or timed out)")
    except Exception as e:
        print(f"  Reference search error (continuing without): {e}")
        reference_context = ""
        references = []

    return {"reference_context": reference_context, "references": references}


async def carlos_design_node(state: CarlosState):
    """Carlos drafts the infrastructure"""
    scenario = state.get("scenario")
    priorities = state.get("priorities", {}) or {}
    historical_context = state.get("historical_context", "")
    reference_context = state.get("reference_context", "")

    context_lines = []

    # Add historical learning context first (high priority)
    if historical_context:
        context_lines.append(historical_context)

    # Add reference materials from web search
    if reference_context:
        context_lines.append(reference_context)

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

    try:
        async with pool.get_main_llm() as llm:
            async for chunk in llm.astream(messages):
                token = chunk.content
                response += token
                tokens.append(token)
    except Exception as e:
        print(f"❌ Carlos design LLM error: {e}")
        response = f"⚠️ Design generation failed due to error: {str(e)}"
        tokens = [response]

    print(f"Design response: {response}")
    convo = state.get("conversation", "")
    convo += "**Carlos:**\n" + response + "\n\n"
    return {"design_doc": response, "audit_status": "pending", "conversation": convo, "design_tokens": tokens}


async def ronei_design_node(state: CarlosState):
    """Ronei drafts a competing infrastructure design"""
    scenario = state.get("scenario")
    priorities = state.get("priorities", {}) or {}
    historical_context = state.get("historical_context", "")
    reference_context = state.get("reference_context", "")

    context_lines = []

    # Add historical learning context (Ronei will interpret it with his flair)
    if historical_context:
        context_lines.append(historical_context)

    # Add reference materials from web search
    if reference_context:
        context_lines.append(reference_context)

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

    try:
        async with pool.get_ronei_llm() as llm:
            async for chunk in llm.astream(messages):
                token = chunk.content
                response += token
                tokens.append(token)
    except Exception as e:
        print(f"❌ Ronei design LLM error: {e}")
        response = f"⚠️ Ronei's design generation failed due to error: {str(e)}"
        tokens = [response]

    print(f"Ronei design response: {response}")
    convo = state.get("conversation", "")
    convo += "**Ronei:**\n" + response + "\n\n"
    return {"ronei_design": response, "conversation": convo, "ronei_tokens": tokens}


async def security_node(state: CarlosState):
    """Security analyst reviews the design with structured JSON output."""
    user_content = (
        f"=== Carlos' Design ===\n{state['design_doc']}\n\n"
        f"=== Ronei's Design ===\n{state.get('ronei_design', '')}\n\n"
        f"Please review both designs from a security perspective. Respond with JSON only."
    )
    messages = [
        SystemMessage(content=SECURITY_ANALYST_INSTRUCTIONS),
        HumanMessage(content=user_content)
    ]
    pool = get_pool()
    response = ""
    tokens = []

    try:
        async with pool.get_mini_llm() as llm:
            async for chunk in llm.astream(messages):
                token = chunk.content
                response += token
                tokens.append(token)
    except Exception as e:
        print(f"❌ Security analyst LLM error: {e}")
        response = f"⚠️ Security analysis unavailable due to error: {str(e)}"
        tokens = [response]

    # Parse JSON and format as markdown
    security_data = None
    security_report = response
    try:
        # Extract JSON from response (handle markdown code blocks)
        json_str = response
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0].strip()

        security_data = json.loads(json_str)
        security_analysis = SecurityAnalysis(**security_data)
        security_report = format_security_analysis(security_analysis)
    except Exception as e:
        print(f"⚠️  Failed to parse structured security output: {e}")
        # Keep original response as fallback

    convo = state.get("conversation", "")
    convo += "**Security Analyst:**\n" + security_report + "\n\n"
    return {
        "security_report": security_report,
        "security_data": security_data,
        "conversation": convo,
        "security_tokens": tokens
    }


async def cost_node(state: CarlosState):
    """Cost optimization specialist reviews the design with structured JSON output."""
    user_content = (
        f"=== Carlos' Design ===\n{state['design_doc']}\n\n"
        f"=== Ronei's Design ===\n{state.get('ronei_design', '')}\n\n"
        f"Please review both designs from a cost optimization perspective. Respond with JSON only."
    )
    messages = [
        SystemMessage(content=COST_ANALYST_INSTRUCTIONS),
        HumanMessage(content=user_content)
    ]
    pool = get_pool()
    response = ""
    tokens = []

    try:
        async with pool.get_mini_llm() as llm:
            async for chunk in llm.astream(messages):
                token = chunk.content
                response += token
                tokens.append(token)
    except Exception as e:
        print(f"❌ Cost analyst LLM error: {e}")
        response = f"⚠️ Cost analysis unavailable due to error: {str(e)}"
        tokens = [response]

    # Parse JSON and format as markdown
    cost_data = None
    cost_report = response
    try:
        # Extract JSON from response (handle markdown code blocks)
        json_str = response
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0].strip()

        cost_data = json.loads(json_str)
        cost_analysis = CostAnalysis(**cost_data)
        cost_report = format_cost_analysis(cost_analysis)
    except Exception as e:
        print(f"⚠️  Failed to parse structured cost output: {e}")
        # Keep original response as fallback

    convo = state.get("conversation", "")
    convo += "**Cost Specialist:**\n" + cost_report + "\n\n"
    return {
        "cost_report": cost_report,
        "cost_data": cost_data,
        "conversation": convo,
        "cost_tokens": tokens
    }


async def reliability_node(state: CarlosState):
    """SRE reviews the design with structured JSON output."""
    user_content = (
        f"=== Carlos' Design ===\n{state['design_doc']}\n\n"
        f"=== Ronei's Design ===\n{state.get('ronei_design', '')}\n\n"
        f"Please review both designs from a reliability and operations perspective. Respond with JSON only."
    )
    messages = [
        SystemMessage(content=RELIABILITY_ENGINEER_INSTRUCTIONS),
        HumanMessage(content=user_content)
    ]
    pool = get_pool()
    response = ""
    tokens = []

    try:
        async with pool.get_mini_llm() as llm:
            async for chunk in llm.astream(messages):
                token = chunk.content
                response += token
                tokens.append(token)
    except Exception as e:
        print(f"❌ Reliability analyst LLM error: {e}")
        response = f"⚠️ Reliability analysis unavailable due to error: {str(e)}"
        tokens = [response]

    # Parse JSON and format as markdown
    reliability_data = None
    reliability_report = response
    try:
        # Extract JSON from response (handle markdown code blocks)
        json_str = response
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0].strip()

        reliability_data = json.loads(json_str)
        reliability_metrics = ReliabilityMetrics(**reliability_data)
        reliability_report = format_reliability_analysis(reliability_metrics)
    except Exception as e:
        print(f"⚠️  Failed to parse structured reliability output: {e}")
        # Keep original response as fallback

    convo = state.get("conversation", "")
    convo += "**SRE:**\n" + reliability_report + "\n\n"
    return {
        "reliability_report": reliability_report,
        "reliability_data": reliability_data,
        "conversation": convo,
        "reliability_tokens": tokens
    }

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

    try:
        async with pool.get_main_llm() as llm:
            async for chunk in llm.astream(messages):
                token = chunk.content
                response += token
                tokens.append(token)
    except Exception as e:
        print(f"❌ Auditor LLM error: {e}")
        response = f"APPROVED\n\n⚠️ Audit review unavailable due to error: {str(e)}. Auto-approving to continue workflow."
        tokens = [response]

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

    try:
        async with pool.get_main_llm() as llm:
            async for chunk in llm.astream(messages):
                token = chunk.content
                response += token
                tokens.append(token)
    except Exception as e:
        print(f"❌ Recommender LLM error: {e}")
        response = f"RECOMMEND: CARLOS\n\n⚠️ Recommendation unavailable due to error: {str(e)}. Defaulting to Carlos' design."
        tokens = [response]

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


async def terraform_validator_node(state: CarlosState):
    """Validate the generated Terraform code with streaming."""
    terraform_code = state.get("terraform_code", "")
    recommendation = state.get("recommendation", "")
    recommended_design = state.get("design_doc", "")

    if "RECOMMEND: RONEI" in recommendation.upper():
        recommended_design = state.get("ronei_design", "")

    user_content = (
        f"=== User Requirements ===\n{state['requirements']}\n\n"
        f"=== Recommended Design ===\n{recommended_design}\n\n"
        f"=== Generated Terraform Code ===\n{terraform_code}\n\n"
        f"Please validate this Terraform code."
    )
    messages = [
        SystemMessage(content=TERRAFORM_VALIDATOR_INSTRUCTIONS),
        HumanMessage(content=user_content)
    ]

    pool = get_pool()
    validation_report = ""
    tokens = []

    async with pool.get_mini_llm() as llm:
        async for chunk in llm.astream(messages):
            token = chunk.content
            validation_report += token
            tokens.append(token)

    convo = state.get("conversation", "")
    convo += "**Terraform Validator:**\n" + validation_report + "\n\n"

    # Debug: Print first 500 chars of validation report to see what LLM returned
    print(f"\n{'='*60}")
    print(f"  📝 TERRAFORM VALIDATOR OUTPUT (first 500 chars):")
    print(f"{'='*60}")
    print(validation_report[:500])
    print(f"{'='*60}\n")

    # Parse validation status from the report
    # Look for explicit "Status:" line first, then fall back to keyword detection
    validation_status = "PASS"
    upper_report = validation_report.upper()

    # Primary detection: Look for "Status: NEEDS FIXES" or similar patterns
    # Handle various markdown formats like **Status:** NEEDS FIXES or **Status: NEEDS FIXES**
    import re
    status_match = re.search(r'STATUS[:\s*]+\s*(NEEDS\s*FIX(?:ES)?|PASS\s*WITH\s*WARNINGS?|PASS)(?:\s*\**)?', upper_report)
    if status_match:
        status_text = status_match.group(1).strip()
        print(f"  📋 Status regex matched: '{status_text}'")
        if "NEEDS" in status_text and "FIX" in status_text:
            validation_status = "NEEDS_FIXES"
        elif "WARNING" in status_text:
            validation_status = "PASS_WITH_WARNINGS"
        else:
            validation_status = "PASS"
    else:
        print(f"  ⚠️ Status regex did not match, using fallback detection")
        # Fallback: Look for keywords anywhere in the report
        if "NEEDS FIXES" in upper_report or "NEEDS_FIXES" in upper_report or "NEEDS FIX" in upper_report or "NEED TO FIX" in upper_report:
            validation_status = "NEEDS_FIXES"
        elif "PASS WITH WARNINGS" in upper_report or "PASS_WITH_WARNINGS" in upper_report:
            validation_status = "PASS_WITH_WARNINGS"

    # Additional check: If there are critical issues mentioned, override to NEEDS_FIXES
    if "❌ CRITICAL" in validation_report.upper() or "## ❌" in validation_report:
        # Check if critical issues section has actual content (not just empty)
        critical_section = re.search(r'❌[^\n]*\n+(.*?)(?=\n##|\Z)', validation_report, re.DOTALL | re.IGNORECASE)
        if critical_section:
            critical_content = critical_section.group(1).strip()
            # If there's actual content after the header (not just "None" or empty)
            if critical_content and "none" not in critical_content.lower()[:50] and len(critical_content) > 10:
                validation_status = "NEEDS_FIXES"

    print(f"  📋 Terraform validation status parsed: {validation_status}")

    return {
        "terraform_validation": validation_report,
        "terraform_validation_status": validation_status,
        "conversation": convo,
        "terraform_validator_tokens": tokens
    }


def terraform_validation_router(state: CarlosState):
    """Route based on validation status and iteration count.

    Returns:
        - "terraform_corrector" if issues need fixing and iterations remain
        - "end" if validation passed or max iterations reached
    """
    MAX_CORRECTION_ITERATIONS = 2

    validation_status = state.get("terraform_validation_status", "PASS")
    current_iteration = state.get("terraform_correction_iteration", 0)

    print(f"\n{'='*60}")
    print(f"  🔀 TERRAFORM VALIDATION ROUTER")
    print(f"     Status: {validation_status}")
    print(f"     Current iteration: {current_iteration}")
    print(f"     Max iterations: {MAX_CORRECTION_ITERATIONS}")
    print(f"{'='*60}\n")

    # If validation passed (with or without warnings after corrections), we're done
    if validation_status == "PASS":
        print(f"  ✅ Terraform validation PASSED - proceeding to END")
        return "end"

    # If passed with warnings, accept it (warnings are advisory)
    if validation_status == "PASS_WITH_WARNINGS":
        print(f"  ✅ Terraform validation PASSED WITH WARNINGS (acceptable) - proceeding to END")
        return "end"

    # If needs fixes, check if we have iterations remaining
    if validation_status == "NEEDS_FIXES":
        if current_iteration < MAX_CORRECTION_ITERATIONS:
            print(f"  🔄 Terraform NEEDS FIXES - routing to terraform_corrector (iteration {current_iteration + 1}/{MAX_CORRECTION_ITERATIONS})")
            return "terraform_corrector"
        else:
            print(f"  ⚠️ Max correction iterations ({MAX_CORRECTION_ITERATIONS}) reached - returning best effort code")
            return "end"

    # Default: end
    print(f"  ❓ Unknown status '{validation_status}' - defaulting to END")
    return "end"


async def terraform_coder_corrector_node(state: CarlosState):
    """Fix Terraform code based on validator feedback with streaming."""
    terraform_code = state.get("terraform_code", "")
    validation_report = state.get("terraform_validation", "")
    recommendation = state.get("recommendation", "")
    current_iteration = state.get("terraform_correction_iteration", 0)

    # Determine which design was recommended
    recommended_design = state.get("design_doc", "")
    if "RECOMMEND: RONEI" in recommendation.upper():
        recommended_design = state.get("ronei_design", "")

    # Increment iteration count
    new_iteration = current_iteration + 1

    # Build the corrector prompt with context
    system_prompt = TERRAFORM_CODER_CORRECTOR_INSTRUCTIONS.replace("{iteration}", str(new_iteration))

    user_content = (
        f"=== User Requirements ===\n{state['requirements']}\n\n"
        f"=== Recommended Design ===\n{recommended_design}\n\n"
        f"=== Previous Terraform Code ===\n{terraform_code}\n\n"
        f"=== Validator Feedback (Iteration {new_iteration}) ===\n{validation_report}\n\n"
        f"Please fix all identified issues and produce corrected Terraform code."
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content)
    ]

    pool = get_pool()
    corrected_code = ""
    tokens = []

    async with pool.get_main_llm() as llm:
        async for chunk in llm.astream(messages):
            token = chunk.content
            corrected_code += token
            tokens.append(token)

    convo = state.get("conversation", "")
    convo += f"**Terraform Coder (Correction {new_iteration}):**\n" + corrected_code + "\n\n"

    return {
        "terraform_code": corrected_code,
        "terraform_correction_iteration": new_iteration,
        "conversation": convo,
        "terraform_corrector_tokens": tokens
    }


# Build graph
builder = StateGraph(CarlosState)
builder.add_node("requirements_gathering", requirements_gathering_node)
builder.add_node("refine_requirements", refine_requirements_node)
builder.add_node("historical_learning", historical_learning_node)
builder.add_node("reference_search", reference_search_node)
builder.add_node("design", carlos_design_node)
builder.add_node("ronei_design", ronei_design_node)
builder.add_node("security", security_node)
builder.add_node("cost", cost_node)
builder.add_node("reliability", reliability_node)
builder.add_node("audit", auditor_node)
builder.add_node("recommender", recommender_node)
builder.add_node("terraform_coder", terraform_coder_node)
builder.add_node("terraform_validator", terraform_validator_node)
builder.add_node("terraform_corrector", terraform_coder_corrector_node)

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

# After refining requirements, fetch historical context, search references, then run designs in parallel
builder.add_edge("refine_requirements", "historical_learning")
builder.add_edge("historical_learning", "reference_search")
builder.add_edge("reference_search", "design")
builder.add_edge("reference_search", "ronei_design")

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
builder.add_edge("terraform_coder", "terraform_validator")

# Terraform validation feedback loop:
# - If validation passes or max iterations reached -> END
# - If validation needs fixes -> terraform_corrector -> terraform_validator (loop)
builder.add_conditional_edges(
    "terraform_validator",
    terraform_validation_router,
    {"terraform_corrector": "terraform_corrector", "end": END}
)
builder.add_edge("terraform_corrector", "terraform_validator")

carlos_graph = builder.compile()
