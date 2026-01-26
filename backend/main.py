from dotenv import load_dotenv
import os
import tempfile

load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from contextlib import asynccontextmanager
from slowapi.errors import RateLimitExceeded
from graph import carlos_graph
from llm_pool import get_pool
from cache import get_cache, stream_cached_design, initialize_cache, close_cache
from feedback import (
    DeploymentFeedback,
    get_feedback_store,
    initialize_feedback_store,
    close_feedback_store,
)
from user_store import (
    initialize_user_store,
    close_user_store,
)
from design_history_store import (
    initialize_design_history_store,
    close_design_history_store,
    get_design_history_store,
)
from audit import (
    AuditRecord,
    AuditAction,
    AuditSeverity,
    AuditQueryParams,
    get_audit_store,
    initialize_audit_store,
    close_audit_store,
)
from auth import (
    User,
    UserCreate,
    Token,
    authenticate_user,
    create_access_token,
    create_user,
    get_current_active_user,
    get_or_create_oauth_user,
    require_admin,
    seed_admin_user,
    get_all_users,
    set_user_admin,
    set_user_disabled,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    SECRET_KEY,
)
from oauth import oauth, OAUTH_REDIRECT_BASE, is_google_enabled, is_github_enabled
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import RedirectResponse
from document_parser import (
    extract_text_from_path,
    extract_text_and_diagrams_from_path,
    supports_diagram_extraction,
    get_diagram_extraction_status,
    MAX_FILE_SIZE,
)
from document_tasks import create_task, get_task, get_user_tasks, TaskStatus
from middleware.rate_limit import limiter, rate_limit_exceeded_handler
from middleware.audit import AuditMiddleware
import json
from datetime import datetime, timezone, timedelta
import httpx

# HTTP client for persistent connections (connection pooling)
http_client: httpx.AsyncClient = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    global http_client

    # Startup
    print("🚀 Starting Carlos the Architect backend...")

    # Initialize LLM connection pool
    pool = get_pool(size=10)
    await pool.initialize()

    # Initialize HTTP client with connection pooling
    http_client = httpx.AsyncClient(
        timeout=30.0,
        limits=httpx.Limits(
            max_connections=100,
            max_keepalive_connections=20
        )
    )
    print("🌐 HTTP connection pool initialized")

    # Initialize design cache (Redis if available, otherwise in-memory)
    await initialize_cache(ttl_hours=24)

    # Initialize feedback store (Redis if available, otherwise in-memory)
    await initialize_feedback_store()

    # Initialize audit store (Cosmos DB if available, otherwise in-memory)
    await initialize_audit_store()

    # Initialize user store (Cosmos DB if available, otherwise in-memory)
    await initialize_user_store()

    # Initialize design history store (Cosmos DB if available, otherwise in-memory)
    await initialize_design_history_store()

    # Seed default admin user
    await seed_admin_user()

    print("✅ Backend ready to serve requests")

    yield

    # Shutdown
    print("🛑 Shutting down Carlos the Architect backend...")

    # Close HTTP client
    if http_client:
        await http_client.aclose()
        print("🌐 HTTP connection pool closed")

    # Close cache connection
    await close_cache()

    # Close feedback store
    await close_feedback_store()

    # Close audit store
    await close_audit_store()

    # Close user store
    await close_user_store()

    # Close design history store
    await close_design_history_store()

    print("✅ Shutdown complete")


# API Tags for documentation grouping
tags_metadata = [
    {
        "name": "Health",
        "description": "Health check and status endpoints for monitoring and orchestration.",
    },
    {
        "name": "Authentication",
        "description": "User authentication including login, registration, and OAuth providers (Google, GitHub).",
    },
    {
        "name": "Design",
        "description": "AI-powered cloud architecture design generation. Supports both synchronous and streaming responses.",
    },
    {
        "name": "Documents",
        "description": "Document upload and processing for extracting requirements from PDF, DOCX, TXT, MD, and XLSX files.",
    },
    {
        "name": "Feedback",
        "description": "Deployment feedback and analytics to track design outcomes and improve future recommendations.",
    },
    {
        "name": "Cache",
        "description": "Design pattern cache management for faster responses on common architecture patterns.",
    },
    {
        "name": "History",
        "description": "Design history management for saving and retrieving past architecture designs.",
    },
    {
        "name": "Admin",
        "description": "Administrative endpoints for audit logs and user management. Requires admin privileges.",
    },
]

app = FastAPI(
    title="Carlos the Architect API",
    description="""
## AI-Powered Cloud Architecture Design

Carlos the Architect is an intelligent assistant that generates production-ready cloud architecture designs
based on natural language requirements.

### Features

- **Multi-Agent Design Pipeline**: Requirements gathering, security analysis, cost optimization, and reliability assessment
- **Streaming Responses**: Real-time token streaming for immediate feedback during design generation
- **Document Processing**: Upload existing documentation to inform design decisions
- **Deployment Feedback**: Track design outcomes to continuously improve recommendations
- **OAuth Authentication**: Sign in with Google or GitHub

### Getting Started

1. Register or login to get an access token
2. Submit your requirements to `/design-stream` for real-time generation
3. Optionally upload context documents via `/upload-document`
4. Provide deployment feedback to improve future designs

### Rate Limits

- Design endpoints: 10 requests/hour
- Document uploads: 30 uploads/hour
- Login attempts: 20/minute
    """,
    version="1.1.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
    contact={
        "name": "Carlos the Architect",
        "url": "https://github.com/rtrentin73/carlos-the-architect",
    },
    license_info={
        "name": "MIT",
    },
)

# Configure rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Get allowed origins from environment or use defaults
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:5174").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session middleware for OAuth state management
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)


@app.get("/health", tags=["Health"], summary="Health check")
async def health():
    """
    Health check endpoint for container orchestration (Kubernetes, Docker, etc.).

    Returns the current health status and LLM connection pool statistics.
    Use this endpoint for liveness and readiness probes.
    """
    pool = get_pool()
    pool_stats = pool.get_pool_stats()

    return {
        "status": "healthy",
        "pools": pool_stats
    }


# Auth endpoints
@app.post("/auth/register", response_model=User, tags=["Authentication"], summary="Register new user")
async def register(user_data: UserCreate):
    """
    Register a new local user account.

    - **username**: Unique username (required)
    - **password**: Password for the account (required)
    - **email**: Optional email address

    Returns the created user object. After registration, use `/auth/login` to obtain an access token.
    """
    return await create_user(user_data)


@app.post("/auth/login", response_model=Token, tags=["Authentication"], summary="Login")
@limiter.limit("20/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate with username and password to obtain a JWT access token.

    The token should be included in subsequent requests as a Bearer token:
    ```
    Authorization: Bearer <access_token>
    ```

    Tokens expire after 24 hours. Rate limited to 20 attempts per minute.
    """
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/auth/me", response_model=User, tags=["Authentication"], summary="Get current user")
async def get_me(current_user: User = Depends(get_current_active_user)):
    """
    Get the currently authenticated user's profile.

    Requires a valid Bearer token. Returns user details including:
    - username
    - email (if provided)
    - admin status
    - authentication provider (local, google, github)
    """
    return current_user


def _build_document_context(task_ids: list, username: str) -> str:
    """
    Build document context from completed document tasks.

    Retrieves extracted text and diagram analysis from document tasks
    and formats them as additional context for design generation.

    Args:
        task_ids: List of document task IDs to include
        username: Username for ownership verification

    Returns:
        Formatted document context string to prepend to requirements
    """
    if not task_ids:
        return ""

    context_parts = []

    for task_id in task_ids:
        task = get_task(task_id)

        # Skip invalid, unowned, or incomplete tasks
        if not task:
            print(f"  ⚠️ Document task {task_id} not found, skipping")
            continue
        if task.username != username:
            print(f"  ⚠️ Document task {task_id} belongs to another user, skipping")
            continue
        if task.status != TaskStatus.COMPLETED:
            print(f"  ⚠️ Document task {task_id} not completed (status: {task.status.value}), skipping")
            continue

        # Build context for this document
        doc_context = f"\n## Document: {task.filename}\n"

        # Add extracted text
        if task.extracted_text:
            doc_context += f"\n### Content\n{task.extracted_text}\n"

        # Add diagram analysis if available
        if task.diagrams_found > 0 and task.diagram_summary:
            doc_context += f"\n### Diagram Analysis\n{task.diagram_summary}\n"

            # Add detailed diagram information for architecture understanding
            for diagram in task.diagrams:
                if diagram.get("analysis"):
                    doc_context += f"\n**{diagram.get('diagram_id', 'Diagram')}:**\n"
                    doc_context += f"- Type: {diagram.get('diagram_type', 'unknown')}\n"
                    if diagram.get("components"):
                        doc_context += f"- Components: {', '.join(diagram['components'][:15])}\n"
                    if diagram.get("technologies"):
                        doc_context += f"- Technologies: {', '.join(diagram['technologies'])}\n"
                    if diagram.get("connections"):
                        doc_context += f"- Data flows: {'; '.join(diagram['connections'][:10])}\n"

        context_parts.append(doc_context)

    if not context_parts:
        return ""

    # Format as reference documentation
    header = "# Reference Documentation\n\nThe following documents have been provided as context for this architecture design:\n"
    return header + "\n---\n".join(context_parts) + "\n\n---\n\n# User Requirements\n\n"


async def _process_document_background(task_id: str, file_path: str):
    """Background task to process document with text and diagram extraction"""
    task = get_task(task_id)
    if not task:
        return

    try:
        task.update_status(TaskStatus.PROCESSING)
        print(f"📄 Processing document {task.filename} for task {task_id}")

        # Check if file supports diagram extraction
        if supports_diagram_extraction(task.filename):
            # Extract text AND diagrams
            extracted_text, diagram_result = extract_text_and_diagrams_from_path(
                file_path,
                analyze_with_vision=True  # Enable GPT-4 Vision analysis
            )

            # Verify we actually extracted content
            if not extracted_text or not extracted_text.strip():
                raise ValueError(
                    f"No text could be extracted from document. "
                    f"Extraction method: {diagram_result.extraction_method}. "
                    f"Details: {diagram_result.diagram_summary or 'Unknown error'}"
                )

            # Convert diagrams to serializable dicts
            diagrams_data = [
                {
                    "diagram_id": d.diagram_id,
                    "page_number": d.page_number,
                    "caption": d.caption,
                    "diagram_type": d.diagram_type.value if d.diagram_type else "unknown",
                    "confidence": d.confidence,
                    "analysis": d.analysis,
                    "components": d.components,
                    "connections": d.connections,
                    "technologies": d.technologies,
                }
                for d in diagram_result.diagrams
            ]

            # Update task with text and diagram results
            task.update_status(
                TaskStatus.COMPLETED,
                extracted_text=extracted_text,
                diagrams_found=diagram_result.diagrams_found,
                diagrams=diagrams_data,
                diagram_summary=diagram_result.diagram_summary,
                extraction_method=diagram_result.extraction_method
            )

            if diagram_result.diagrams_found > 0:
                print(f"✅ Document {task.filename} processed: {len(extracted_text)} chars, {diagram_result.diagrams_found} diagrams (task {task_id})")
            else:
                print(f"✅ Document {task.filename} processed: {len(extracted_text)} chars, no diagrams found (task {task_id})")
        else:
            # Extract text only for non-diagram-supporting files
            extracted_text = extract_text_from_path(file_path)

            # Verify we actually extracted content
            if not extracted_text or not extracted_text.strip():
                raise ValueError("No text could be extracted from document")

            task.update_status(
                TaskStatus.COMPLETED,
                extracted_text=extracted_text,
                extraction_method="text-only"
            )
            print(f"✅ Document {task.filename} processed: {len(extracted_text)} chars (task {task_id})")

    except Exception as e:
        error_msg = str(e)
        task.update_status(TaskStatus.FAILED, error=error_msg)
        print(f"❌ Failed to process document {task.filename}: {error_msg}")

    finally:
        # Clean up temp file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"⚠️  Failed to remove temp file {file_path}: {e}")


@app.post("/upload-document", tags=["Documents"], summary="Upload document for processing")
@limiter.limit("30/hour")
async def upload_document(
    request: Request,
    file: UploadFile = File(..., description="Document file to upload"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload a document for asynchronous text and diagram extraction.

    **Supported formats:** PDF, DOCX, TXT, MD, XLSX, PNG, JPG, JPEG, GIF, BMP, TIFF, WEBP

    **Size limit:** 50MB

    **Diagram Extraction (PDFs and images):**
    When Azure AI Document Intelligence is configured with the `prebuilt-layout` model:
    - Automatically detects diagrams, flowcharts, and architectural figures
    - Extracts diagram metadata (page number, caption, bounding box)
    - Reports confidence score for each detected diagram

    **GPT-4 Vision Analysis (optional):**
    When Azure OpenAI GPT-4 Vision is configured:
    - Analyzes detected diagrams to identify components and connections
    - Classifies diagram types (architecture, flowchart, sequence, etc.)
    - Extracts technologies and services shown in diagrams

    **Azure AI Document Intelligence (required for images/diagram detection):**
    - **Images:** Required for PNG, JPG, etc. - provides OCR text extraction
    - **PDFs:** Enhanced extraction for scanned PDFs, embedded images, and diagrams
    - Falls back to standard text extraction for PDFs if not configured

    **Without Azure AI Document Intelligence:**
    - Image uploads will return an error
    - PDFs use pypdf (text-based PDFs only, no OCR or diagram detection)

    Documents are processed in the background. After uploading:
    1. You receive a `task_id` immediately
    2. Poll `GET /documents/{task_id}` to check processing status
    3. Once complete, the response includes:
       - `extracted_text`: Full text content
       - `diagrams_found`: Number of diagrams detected
       - `diagrams`: Array of diagram details (page, caption, type, analysis)
       - `diagram_summary`: Summary of all detected diagrams

    Use `GET /documents/diagram-capabilities` to check if diagram extraction is configured.

    Rate limited to 30 uploads per hour.
    """
    print(f"📤 Document upload from {current_user.username}: {file.filename}")

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Validate file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024:.0f}MB"
        )

    if file_size == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    # Create task
    task = create_task(file.filename or "unknown", current_user.username, file_size)

    # Save to temp file
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f"{task.task_id}_{file.filename}")

    try:
        with open(temp_path, "wb") as f:
            f.write(content)

        # Schedule background processing
        background_tasks.add_task(_process_document_background, task.task_id, temp_path)

        return {
            "task_id": task.task_id,
            "filename": file.filename,
            "status": task.status.value,
            "message": f"⏳ Processing {file.filename}... Check /documents/{task.task_id} for status"
        }

    except Exception as e:
        # Clean up task and file on error
        task.update_status(TaskStatus.FAILED, error=str(e))
        if os.path.exists(temp_path):
            os.remove(temp_path)

        raise HTTPException(
            status_code=500,
            detail=f"Failed to save document: {str(e)}"
        )


@app.get("/documents/{task_id}", tags=["Documents"], summary="Get document processing status")
async def get_document_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Check document processing status and retrieve extracted text.

    **Response fields:**
    - `task_id`: Unique task identifier
    - `filename`: Original filename
    - `status`: `pending` | `processing` | `completed` | `failed`
    - `extracted_text`: Extracted text content (only when status is `completed`)
    - `error`: Error message (only when status is `failed`)

    Poll this endpoint after uploading to check when processing completes.
    """
    task = get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Verify task belongs to user
    if task.username != current_user.username:
        raise HTTPException(status_code=403, detail="Access denied")

    return task.to_dict()


@app.get("/documents", tags=["Documents"], summary="List uploaded documents")
async def list_user_documents(
    current_user: User = Depends(get_current_active_user),
    limit: int = 10
):
    """
    List recent document processing tasks for the current user.

    Returns the most recent uploads with their processing status.
    Use this to track multiple document uploads or find previous extractions.
    """
    tasks = get_user_tasks(current_user.username, limit=limit)
    return {
        "tasks": [task.to_dict() for task in tasks],
        "count": len(tasks)
    }


@app.get("/documents/diagram-capabilities", tags=["Documents"], summary="Get diagram extraction capabilities")
async def get_diagram_capabilities(
    current_user: User = Depends(get_current_active_user)
):
    """
    Check the current diagram extraction capabilities.

    Returns information about:
    - Whether Azure Document Intelligence is configured (required for diagram detection)
    - Whether GPT-4 Vision is configured (optional, for diagram analysis)
    - Supported file extensions for diagram extraction

    **Example response:**
    ```json
    {
        "document_intelligence_configured": true,
        "vision_analysis_configured": true,
        "supported_extensions": ["pdf", "png", "jpg", "jpeg", ...],
        "capabilities": {
            "text_extraction": true,
            "diagram_detection": true,
            "diagram_analysis": true
        }
    }
    ```

    Use this endpoint to verify diagram extraction is properly configured
    before uploading documents with diagrams.
    """
    return get_diagram_extraction_status()


@app.post("/design", tags=["Design"], summary="Generate architecture design (synchronous)")
@limiter.limit("10/hour")
async def design(request: Request, req: dict, current_user: User = Depends(get_current_active_user)):
    """
    Generate a complete cloud architecture design document.

    **Two-phase conversation flow:**

    1. **Initial request** - Send requirements in `text` field. Carlos may return
       clarifying questions (`clarification_needed: true`)

    2. **Follow-up request** - If clarification was needed, send answers in `user_answers`
       field to complete the design

    **Request body:**
    ```json
    {
      "text": "I need a web application with user authentication...",
      "scenario": "startup",
      "priorities": {"cost": "high", "security": "medium"},
      "user_answers": "Optional answers to clarifying questions",
      "document_task_ids": ["abc-123", "def-456"]
    }
    ```

    **Document context:** If `document_task_ids` is provided, the extracted text and
    diagram analysis from those documents will be automatically included as context
    for the design generation. This allows Carlos to understand existing architecture
    diagrams and requirements documents.

    **Response includes:**
    - `design`: Primary architecture design document
    - `ronei_design`: Alternative design perspective
    - `security_report`: Security analysis and recommendations
    - `cost_report`: Cost estimation and optimization suggestions
    - `reliability_report`: High availability and disaster recovery analysis
    - `recommendation`: Final recommendation summary
    - `terraform_code`: Infrastructure as Code (if applicable)

    Rate limited to 10 requests per hour. For real-time streaming, use `/design-stream`.
    """
    print(f"Received request from {current_user.username}: {req}")
    try:
        # Build document context if task IDs provided
        document_context = ""
        if req.get("document_task_ids"):
            document_context = _build_document_context(
                req["document_task_ids"],
                current_user.username
            )
            if document_context:
                print(f"📄 Including context from {len(req['document_task_ids'])} document(s)")

        # Build requirements with document context
        requirements_text = document_context + req["text"]

        # Build initial state
        initial_state = {
            "requirements": requirements_text,
            "conversation": "",
            "scenario": req.get("scenario"),
            "priorities": req.get("priorities", {}),
        }

        # If user provided answers to clarifying questions, include them
        if req.get("user_answers"):
            initial_state["user_answers"] = req["user_answers"]

        result = await carlos_graph.ainvoke(initial_state, version="v2")
        design_doc = result.get("design_doc", "")
        ronei_design = result.get("ronei_design", "")
        audit_status = result.get("audit_status", "unknown")
        audit_report = result.get("audit_report", "")
        conversation = result.get("conversation", "")
        security_report = result.get("security_report", "")
        cost_report = result.get("cost_report", "")
        reliability_report = result.get("reliability_report", "")
        recommendation = result.get("recommendation", "")
        print(
            f"Design generated, length={len(design_doc)}, ronei_length={len(ronei_design)}, "
            f"audit_status={audit_status}, audit_report_len={len(audit_report)}, "
            f"security_len={len(security_report)}, cost_len={len(cost_report)}, "
            f"reliability_len={len(reliability_report)}, recommendation_len={len(recommendation)}, convo_len={len(conversation)}"
        )
        # Check if we're waiting for user answers (clarification phase)
        if result.get("clarification_needed") and not result.get("design_doc"):
            return {
                "clarification_needed": True,
                "agent_chat": conversation,
                "refined_requirements": result.get("refined_requirements", ""),
            }

        return {
            "design": design_doc,
            "ronei_design": ronei_design,
            "audit_status": audit_status,
            "audit_report": audit_report,
            "recommendation": recommendation,
            "agent_chat": conversation,
            "security_report": security_report,
            "cost_report": cost_report,
            "reliability_report": reliability_report,
            "clarification_needed": False,
            # Structured data for programmatic access
            "structured_data": {
                "security": result.get("security_data"),
                "cost": result.get("cost_data"),
                "reliability": result.get("reliability_data"),
            },
            # Reference materials found during design
            "references": result.get("references", []),
        }
    except Exception as e:
        print(f"Error in design endpoint: {e}")
        return {"error": str(e)}


@app.post("/design-stream", tags=["Design"], summary="Generate architecture design (streaming)")
@limiter.limit("10/hour")
async def design_stream(request: Request, req: dict, current_user: User = Depends(get_current_active_user)):
    """
    Stream design generation with real-time agent and token events.

    **Recommended endpoint** for interactive UIs - provides immediate feedback as the
    multi-agent pipeline processes your requirements.

    **Server-Sent Events (SSE) stream with event types:**

    - `agent_start`: An agent has begun processing
    - `token`: Real-time token output from an agent
    - `field_update`: A report section has been completed
    - `agent_complete`: An agent has finished
    - `complete`: Final summary with all outputs
    - `error`: Error occurred during processing

    **Example SSE events:**
    ```
    data: {"type": "agent_start", "agent": "carlos", "timestamp": "..."}
    data: {"type": "token", "agent": "carlos", "content": "# Architecture", "timestamp": "..."}
    data: {"type": "complete", "summary": {...}, "timestamp": "..."}
    ```

    **Document context:** If `document_task_ids` is provided in the request body,
    the extracted text and diagram analysis from those documents will be automatically
    included as context for the design generation.

    **Caching:** Common architecture patterns are cached for instant responses.
    Cache hits are indicated by the `X-Cache-Status: HIT` response header.
    Note: Requests with document_task_ids bypass caching due to dynamic context.

    Rate limited to 10 requests per hour.
    """
    print(f"Received streaming request from {current_user.username}: {req}")

    # Build document context if task IDs provided
    document_context = ""
    if req.get("document_task_ids"):
        document_context = _build_document_context(
            req["document_task_ids"],
            current_user.username
        )
        if document_context:
            print(f"📄 Including context from {len(req['document_task_ids'])} document(s)")

    # Check cache for common patterns (skip if user provided answers or document context)
    cache = get_cache()
    cache_key = None
    if not req.get("user_answers") and not document_context:
        cache_key = cache.generate_cache_key(
            req.get("text", ""),
            {
                "scenario": req.get("scenario"),
                "priorities": req.get("priorities", {}),
            }
        )
        cached_design = await cache.get(cache_key)
        if cached_design:
            print(f"📦 Cache HIT for {current_user.username} (key: {cache_key})")

            async def cached_event_generator():
                async for event_data in stream_cached_design(cached_design):
                    yield f"data: {event_data}\n\n"

            return StreamingResponse(
                cached_event_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                    "X-Cache-Status": "HIT",
                }
            )
        else:
            print(f"📦 Cache MISS for {current_user.username} (key: {cache_key})")

    async def event_generator():
        final_state = {}
        try:
            # Build requirements with document context
            requirements_text = document_context + req["text"]

            # Build initial state
            initial_state = {
                "requirements": requirements_text,
                "conversation": "",
                "scenario": req.get("scenario"),
                "priorities": req.get("priorities", {}),
            }

            # If user provided answers to clarifying questions, include them
            if req.get("user_answers"):
                initial_state["user_answers"] = req["user_answers"]

            # Stream events from LangGraph
            async for event in carlos_graph.astream(
                initial_state,
                stream_mode="updates",
            ):
                # Process each node completion event
                for node_name, node_output in event.items():
                    # Emit agent_start event
                    start_event = {
                        "type": "agent_start",
                        "agent": node_name,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    yield f"data: {json.dumps(start_event)}\n\n"

                    # Token streaming mappings: token_field -> agent_name
                    token_mappings = {
                        "design_tokens": "carlos",
                        "ronei_tokens": "ronei_design",
                        "terraform_tokens": "terraform_coder",
                        "terraform_validator_tokens": "terraform_validator",
                        "terraform_corrector_tokens": "terraform_corrector",
                        "requirements_tokens": "requirements_gathering",
                        "refine_tokens": "refine_requirements",
                        "security_tokens": "security",
                        "cost_tokens": "cost",
                        "reliability_tokens": "reliability",
                        "audit_tokens": "audit",
                        "recommender_tokens": "recommender",
                    }

                    # Emit token events for all streaming agents
                    for token_field, agent_name in token_mappings.items():
                        if token_field in node_output and node_output[token_field]:
                            for token in node_output[token_field]:
                                token_event = {
                                    "type": "token",
                                    "agent": agent_name,
                                    "content": token,
                                    "timestamp": datetime.now(timezone.utc).isoformat()
                                }
                                yield f"data: {json.dumps(token_event)}\n\n"

                    # Field update mappings for final content
                    field_mappings = {
                        "security": "security_report",
                        "cost": "cost_report",
                        "reliability": "reliability_report",
                        "audit": "audit_report",
                        "recommender": "recommendation",
                        "terraform_coder": "terraform_code",
                        "terraform_validator": "terraform_validation",
                        "terraform_corrector": "terraform_code",  # Corrector updates the same field
                        "requirements_gathering": "refined_requirements",
                        "refine_requirements": "refined_requirements",
                    }

                    if node_name in field_mappings:
                        field = field_mappings[node_name]
                        if field in node_output:
                            field_event = {
                                "type": "field_update",
                                "field": field,
                                "content": node_output[field],
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            }
                            yield f"data: {json.dumps(field_event)}\n\n"

                    # Also emit audit_status if present
                    if "audit_status" in node_output:
                        status_event = {
                            "type": "field_update",
                            "field": "audit_status",
                            "content": node_output["audit_status"],
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                        yield f"data: {json.dumps(status_event)}\n\n"

                    # Accumulate state for final response
                    final_state.update(node_output)

                    # Emit agent_complete event
                    complete_event = {
                        "type": "agent_complete",
                        "agent": node_name,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    yield f"data: {json.dumps(complete_event)}\n\n"

            # Send final complete event with full state
            # Check if we're waiting for user answers (clarification phase)
            clarification_needed = final_state.get("clarification_needed", False) and not final_state.get("design_doc")

            summary_data = {
                "design": final_state.get("design_doc", ""),
                "ronei_design": final_state.get("ronei_design", ""),
                "audit_status": final_state.get("audit_status", ""),
                "audit_report": final_state.get("audit_report", ""),
                "recommendation": final_state.get("recommendation", ""),
                "agent_chat": final_state.get("conversation", ""),
                "security_report": final_state.get("security_report", ""),
                "cost_report": final_state.get("cost_report", ""),
                "reliability_report": final_state.get("reliability_report", ""),
                "terraform_code": final_state.get("terraform_code", ""),
                "terraform_validation": final_state.get("terraform_validation", ""),
                "terraform_correction_iterations": final_state.get("terraform_correction_iteration", 0),
                "terraform_validation_status": final_state.get("terraform_validation_status", ""),
                "clarification_needed": clarification_needed,
                # Structured data for programmatic access
                "structured_data": {
                    "security": final_state.get("security_data"),
                    "cost": final_state.get("cost_data"),
                    "reliability": final_state.get("reliability_data"),
                },
                # Reference materials found during design
                "references": final_state.get("references", []),
            }

            # Cache the result if appropriate (not clarification phase, has design)
            if cache_key and not clarification_needed and summary_data.get("design"):
                if cache.should_cache(req.get("text", "")):
                    await cache.set(cache_key, summary_data)
                    print(f"📦 Cached design for key: {cache_key}")

            complete_summary = {
                "type": "complete",
                "summary": summary_data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            yield f"data: {json.dumps(complete_summary)}\n\n"

        except Exception as e:
            print(f"Error in streaming endpoint: {e}")
            error_event = {
                "type": "error",
                "message": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "X-Cache-Status": "MISS",
        }
    )


@app.get("/cache/stats", tags=["Cache"], summary="Get cache statistics")
async def get_cache_stats(current_user: User = Depends(get_current_active_user)):
    """
    Get design pattern cache statistics.

    Returns cache hit/miss counts, memory usage, and TTL configuration.
    Useful for monitoring cache effectiveness.
    """
    cache = get_cache()
    stats = await cache.get_stats()
    return {
        "cache": stats,
        "status": "enabled",
        "ttl_hours": cache.ttl_hours,
    }


@app.post("/cache/clear", tags=["Cache"], summary="Clear design cache")
async def clear_cache(current_user: User = Depends(get_current_active_user)):
    """
    Clear the design pattern cache.

    Use this when you want to force fresh design generation for all patterns.
    Returns the number of entries that were cleared.
    """
    cache = get_cache()
    old_stats = await cache.get_stats()
    cleared = await cache.clear()
    return {
        "message": "Cache cleared",
        "cleared_entries": cleared,
    }


# ============================================================================
# Design History Endpoints
# ============================================================================

@app.post("/history", tags=["History"], summary="Save design to history")
async def save_design_to_history(
    design: dict,
    current_user: User = Depends(get_current_active_user)
):
    """
    Save a design to the user's design history.

    **Request body:**
    ```json
    {
      "requirements": "Original requirements text",
      "cloud_provider": "azure|aws|gcp|multi_cloud",
      "environment": "dev|staging|prod",
      "architecture": "Generated architecture document",
      "terraform": "Generated Terraform code",
      "diagram_svg": "Architecture diagram SVG",
      "cost_estimate": "Cost estimation report",
      "security_analysis": "Security analysis report",
      "reliability_analysis": "Reliability analysis report",
      "title": "Optional custom title"
    }
    ```

    Returns the saved design with a unique ID and timestamp.
    """
    try:
        store = get_design_history_store()
        print(f"💾 Saving design for {current_user.username} (persistent: {store.is_connected})")
        saved = await store.save_design(current_user.username, design)
        print(f"✅ Design {saved.get('id')} saved for {current_user.username}")
        return {
            "status": "success",
            "design": saved,
            "message": "Design saved to history"
        }
    except Exception as e:
        print(f"❌ Error saving design to history: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save design: {str(e)}"
        )


@app.get("/history", tags=["History"], summary="Get design history")
async def get_design_history(
    current_user: User = Depends(get_current_active_user),
    limit: int = 50
):
    """
    Get the user's design history.

    Returns a list of saved designs ordered by creation date (newest first).

    **Parameters:**
    - `limit`: Maximum number of designs to return (default 50)
    """
    try:
        store = get_design_history_store()
        print(f"📚 Getting design history for {current_user.username} (persistent: {store.is_connected})")
        designs = await store.get_user_designs(current_user.username, limit=limit)
        print(f"📚 Found {len(designs)} designs for {current_user.username}")
        return {
            "designs": designs,
            "count": len(designs),
            "persistent": store.is_connected,
        }
    except Exception as e:
        print(f"❌ Error getting design history: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve design history: {str(e)}"
        )


@app.get("/history/{design_id}", tags=["History"], summary="Get specific design")
async def get_design_by_id(
    design_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific design from history by its ID.

    Returns the full design document including all reports and generated code.
    """
    try:
        store = get_design_history_store()
        design = await store.get_design(design_id, current_user.username)
        if not design:
            raise HTTPException(
                status_code=404,
                detail="Design not found"
            )
        return {"design": design}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting design {design_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve design: {str(e)}"
        )


@app.delete("/history/{design_id}", tags=["History"], summary="Delete design from history")
async def delete_design_from_history(
    design_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a specific design from history.

    The design must belong to the current user.
    """
    try:
        store = get_design_history_store()
        deleted = await store.delete_design(design_id, current_user.username)
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Design not found"
            )
        return {
            "status": "success",
            "message": f"Design {design_id} deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting design {design_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete design: {str(e)}"
        )


@app.delete("/history", tags=["History"], summary="Clear design history")
async def clear_design_history(
    current_user: User = Depends(get_current_active_user)
):
    """
    Clear all designs from the user's history.

    This action cannot be undone.
    """
    try:
        store = get_design_history_store()
        count = await store.clear_user_history(current_user.username)
        return {
            "status": "success",
            "message": f"Cleared {count} designs from history",
            "deleted_count": count
        }
    except Exception as e:
        print(f"❌ Error clearing design history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear history: {str(e)}"
        )


# ============================================================================
# Deployment Feedback Endpoints
# ============================================================================

@app.post("/feedback/deployment", tags=["Feedback"], summary="Submit deployment feedback")
async def submit_deployment_feedback(
    feedback: DeploymentFeedback,
    current_user: User = Depends(get_current_active_user)
):
    """
    Submit feedback about a deployed design.

    After deploying a Carlos-generated architecture, provide feedback to help
    improve future recommendations:

    - **Was it deployed?** Track which designs actually get implemented
    - **Did it work?** Report success or issues encountered
    - **Satisfaction rating:** 1-5 star rating
    - **Issues encountered:** Describe any problems

    This feedback is used to learn from real-world deployments and improve
    the design generation algorithms.
    """
    print(f"📊 Deployment feedback from {current_user.username} for design {feedback.design_id}")

    try:
        store = get_feedback_store()
        feedback_id = await store.save_feedback(
            username=current_user.username,
            feedback=feedback,
            requirements_summary=None  # Could be populated from design history
        )

        return {
            "status": "success",
            "feedback_id": feedback_id,
            "message": "Thank you for your feedback! This helps improve Carlos."
        }
    except Exception as e:
        print(f"❌ Error saving feedback: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save feedback: {str(e)}"
        )


@app.get("/feedback/my-feedback", tags=["Feedback"], summary="Get my feedback history")
async def get_my_feedback(
    current_user: User = Depends(get_current_active_user),
    limit: int = 20
):
    """
    Get deployment feedback previously submitted by the current user.

    Returns a list of your feedback submissions with deployment outcomes,
    ratings, and any issues reported.
    """
    try:
        store = get_feedback_store()
        feedback_list = await store.get_user_feedback(current_user.username, limit=limit)

        return {
            "feedback": [f.model_dump() for f in feedback_list],
            "count": len(feedback_list)
        }
    except Exception as e:
        print(f"❌ Error getting user feedback: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve feedback: {str(e)}"
        )


@app.get("/feedback/analytics", tags=["Feedback"], summary="Get deployment analytics")
async def get_deployment_analytics(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get aggregate deployment analytics across all users.

    **Metrics included:**
    - Total designs tracked
    - Deployment rate (% of designs that were actually deployed)
    - Success rate (% of deployed designs that succeeded)
    - Average satisfaction rating (1-5 stars)
    - Common issues encountered

    Use these analytics to understand overall design quality and identify
    areas for improvement.
    """
    try:
        store = get_feedback_store()
        analytics = await store.get_analytics()

        return {
            "analytics": analytics,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        print(f"❌ Error getting analytics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve analytics: {str(e)}"
        )


# ============================================================================
# OAuth Authentication Endpoints
# ============================================================================

@app.get("/auth/providers", tags=["Authentication"], summary="List OAuth providers")
async def get_auth_providers():
    """
    Get available OAuth authentication providers.

    Returns which OAuth providers (Google, GitHub) are configured and available
    for use. Use this to conditionally show OAuth login buttons in the UI.
    """
    return {
        "providers": {
            "google": is_google_enabled(),
            "github": is_github_enabled(),
        }
    }


@app.get("/auth/google", tags=["Authentication"], summary="Login with Google")
async def google_login(request: Request):
    """
    Initiate Google OAuth login flow.

    Redirects the user to Google's authentication page. After successful
    authentication, the user is redirected back with a JWT token.

    **Note:** This endpoint redirects - do not call via AJAX.
    """
    if not is_google_enabled():
        raise HTTPException(
            status_code=501,
            detail="Google OAuth not configured"
        )

    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.get("/auth/google/callback", name="google_callback", tags=["Authentication"], include_in_schema=False)
async def google_callback(request: Request):
    """Handle Google OAuth callback (internal - not for direct use)."""
    if not is_google_enabled():
        raise HTTPException(
            status_code=501,
            detail="Google OAuth not configured"
        )

    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")

        if not user_info:
            return RedirectResponse(
                url=f"{OAUTH_REDIRECT_BASE}/auth/callback?error=no_user_info"
            )

        # Get or create user
        user = await get_or_create_oauth_user(
            provider="google",
            oauth_id=user_info.get("sub"),
            email=user_info.get("email", ""),
            name=user_info.get("name", ""),
            avatar_url=user_info.get("picture"),
        )

        # Issue JWT token
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        # Redirect to frontend with token
        return RedirectResponse(
            url=f"{OAUTH_REDIRECT_BASE}/auth/callback?token={access_token}"
        )

    except Exception as e:
        print(f"❌ Google OAuth error: {e}")
        return RedirectResponse(
            url=f"{OAUTH_REDIRECT_BASE}/auth/callback?error=oauth_failed"
        )


@app.get("/auth/github", tags=["Authentication"], summary="Login with GitHub")
async def github_login(request: Request):
    """
    Initiate GitHub OAuth login flow.

    Redirects the user to GitHub's authentication page. After successful
    authentication, the user is redirected back with a JWT token.

    **Note:** This endpoint redirects - do not call via AJAX.
    """
    if not is_github_enabled():
        raise HTTPException(
            status_code=501,
            detail="GitHub OAuth not configured"
        )

    redirect_uri = request.url_for("github_callback")
    return await oauth.github.authorize_redirect(request, redirect_uri)


@app.get("/auth/github/callback", name="github_callback", tags=["Authentication"], include_in_schema=False)
async def github_callback(request: Request):
    """Handle GitHub OAuth callback (internal - not for direct use)."""
    if not is_github_enabled():
        raise HTTPException(
            status_code=501,
            detail="GitHub OAuth not configured"
        )

    try:
        token = await oauth.github.authorize_access_token(request)

        # Fetch user info from GitHub API
        resp = await oauth.github.get("user", token=token)
        user_info = resp.json()

        if not user_info:
            return RedirectResponse(
                url=f"{OAUTH_REDIRECT_BASE}/auth/callback?error=no_user_info"
            )

        # Get user's primary email if not public
        email = user_info.get("email")
        if not email:
            # Fetch emails from GitHub API
            email_resp = await oauth.github.get("user/emails", token=token)
            emails = email_resp.json()
            for e in emails:
                if e.get("primary"):
                    email = e.get("email")
                    break

        # Get or create user
        user = await get_or_create_oauth_user(
            provider="github",
            oauth_id=str(user_info.get("id")),
            email=email or "",
            name=user_info.get("login", ""),
            avatar_url=user_info.get("avatar_url"),
        )

        # Issue JWT token
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        # Redirect to frontend with token
        return RedirectResponse(
            url=f"{OAUTH_REDIRECT_BASE}/auth/callback?token={access_token}"
        )

    except Exception as e:
        print(f"❌ GitHub OAuth error: {e}")
        return RedirectResponse(
            url=f"{OAUTH_REDIRECT_BASE}/auth/callback?error=oauth_failed"
        )


# ============================================================================
# Admin Endpoints
# ============================================================================

@app.get("/admin/audit", tags=["Admin"], summary="Query audit logs")
async def get_audit_logs(
    username: str = None,
    action_prefix: str = None,
    severity: str = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(require_admin)
):
    """
    Query audit logs with optional filtering. **Admin only.**

    **Filter parameters:**
    - `username`: Filter by specific user
    - `action_prefix`: Filter by action category (e.g., `auth.`, `design.`, `admin.`)
    - `severity`: Filter by severity level (`info`, `warning`, `error`, `critical`)

    **Pagination:**
    - `limit`: Max records to return (default 50, max 1000)
    - `offset`: Skip first N records

    **Action categories:**
    - `auth.*`: Authentication events (login, logout, register)
    - `design.*`: Design generation events
    - `document.*`: Document upload/processing events
    - `feedback.*`: Feedback submissions
    - `admin.*`: Administrative actions
    - `cache.*`: Cache operations
    """
    try:
        store = get_audit_store()

        # Build query params
        params = AuditQueryParams(
            username=username if username else None,
            action_prefix=action_prefix if action_prefix else None,
            severity=AuditSeverity(severity) if severity else None,
            limit=min(limit, 1000),
            offset=offset,
        )

        records = await store.query(params)

        return {
            "records": [
                {
                    "audit_id": r.audit_id,
                    "timestamp": r.timestamp.isoformat(),
                    "username": r.username,
                    "action": r.action.value,
                    "endpoint": r.endpoint,
                    "method": r.method,
                    "status_code": r.status_code,
                    "severity": r.severity.value,
                    "duration_ms": r.duration_ms,
                    "error_message": r.error_message,
                }
                for r in records
            ],
            "count": len(records),
            "offset": offset,
            "limit": limit,
        }
    except Exception as e:
        print(f"❌ Error querying audit logs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query audit logs: {str(e)}"
        )


@app.get("/admin/audit/stats", tags=["Admin"], summary="Get audit statistics")
async def get_audit_stats(
    days: int = 30,
    current_user: User = Depends(require_admin)
):
    """
    Get aggregate audit statistics for the dashboard. **Admin only.**

    **Parameters:**
    - `days`: Time period to analyze (default 30 days)

    **Returns:**
    - Total events count
    - Unique users count
    - Error count
    - Events grouped by action category
    - Events grouped by severity level
    - Storage backend type (cosmosdb or in-memory)
    """
    try:
        store = get_audit_store()
        stats = await store.get_stats(days=days)

        return {
            "stats": stats,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        print(f"❌ Error getting audit stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get audit stats: {str(e)}"
        )


@app.get("/admin/audit/export", tags=["Admin"], summary="Export audit logs")
async def export_audit_logs(
    format: str = "json",
    username: str = None,
    action_prefix: str = None,
    limit: int = 1000,
    current_user: User = Depends(require_admin)
):
    """
    Export audit logs as a downloadable file. **Admin only.**

    **Parameters:**
    - `format`: Output format - `json` or `csv` (default: json)
    - `username`: Filter by specific user
    - `action_prefix`: Filter by action category
    - `limit`: Max records to export (default 1000, max 10000)

    Returns a downloadable file with Content-Disposition header set.
    """
    try:
        store = get_audit_store()

        params = AuditQueryParams(
            username=username if username else None,
            action_prefix=action_prefix if action_prefix else None,
            limit=min(limit, 10000),
        )

        records = await store.query(params)

        if format == "csv":
            import io
            import csv

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                "audit_id", "timestamp", "username", "action", "endpoint",
                "method", "status_code", "severity", "duration_ms", "error_message"
            ])

            for r in records:
                writer.writerow([
                    r.audit_id,
                    r.timestamp.isoformat(),
                    r.username or "",
                    r.action.value,
                    r.endpoint,
                    r.method,
                    r.status_code or "",
                    r.severity.value,
                    r.duration_ms or "",
                    r.error_message or "",
                ])

            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=audit_export.csv"}
            )
        else:
            # JSON format
            export_data = [
                {
                    "audit_id": r.audit_id,
                    "timestamp": r.timestamp.isoformat(),
                    "username": r.username,
                    "action": r.action.value,
                    "endpoint": r.endpoint,
                    "method": r.method,
                    "status_code": r.status_code,
                    "severity": r.severity.value,
                    "duration_ms": r.duration_ms,
                    "error_message": r.error_message,
                    "metadata": r.metadata,
                }
                for r in records
            ]

            return StreamingResponse(
                iter([json.dumps(export_data, indent=2)]),
                media_type="application/json",
                headers={"Content-Disposition": "attachment; filename=audit_export.json"}
            )
    except Exception as e:
        print(f"❌ Error exporting audit logs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export audit logs: {str(e)}"
        )


@app.get("/admin/users", tags=["Admin"], summary="List all users")
async def list_users(current_user: User = Depends(require_admin)):
    """
    List all registered users. **Admin only.**

    Returns user details including username, email, admin status, and account status.
    """
    users = await get_all_users()
    return {
        "users": [
            {
                "username": u.username,
                "email": u.email,
                "is_admin": u.is_admin,
                "disabled": u.disabled,
            }
            for u in users
        ],
        "count": len(users)
    }


@app.post("/admin/users/{username}/promote", tags=["Admin"], summary="Promote user to admin")
async def promote_user(
    username: str,
    current_user: User = Depends(require_admin)
):
    """
    Grant admin privileges to a user. **Admin only.**

    Admins can access the admin dashboard, view audit logs, and manage other users.
    You cannot modify your own admin status.
    """
    if username == current_user.username:
        raise HTTPException(
            status_code=400,
            detail="Cannot modify your own admin status"
        )

    user = await set_user_admin(username, True)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {"message": f"User {username} promoted to admin", "user": user.model_dump()}


@app.post("/admin/users/{username}/demote", tags=["Admin"], summary="Remove admin privileges")
async def demote_user(
    username: str,
    current_user: User = Depends(require_admin)
):
    """
    Remove admin privileges from a user. **Admin only.**

    The user will retain their account but lose access to admin features.
    You cannot modify your own admin status.
    """
    if username == current_user.username:
        raise HTTPException(
            status_code=400,
            detail="Cannot modify your own admin status"
        )

    user = await set_user_admin(username, False)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {"message": f"User {username} demoted from admin", "user": user.model_dump()}


@app.post("/admin/users/{username}/enable", tags=["Admin"], summary="Enable user account")
async def enable_user(
    username: str,
    current_user: User = Depends(require_admin)
):
    """
    Re-enable a disabled user account. **Admin only.**

    The user will be able to log in and use the application again.
    You cannot modify your own account status.
    """
    if username == current_user.username:
        raise HTTPException(
            status_code=400,
            detail="Cannot modify your own account status"
        )

    user = await set_user_disabled(username, False)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {"message": f"User {username} enabled", "user": user.model_dump()}


@app.post("/admin/users/{username}/disable", tags=["Admin"], summary="Disable user account")
async def disable_user(
    username: str,
    current_user: User = Depends(require_admin)
):
    """
    Disable a user account. **Admin only.**

    Disabled users cannot log in or access any endpoints.
    Use this to temporarily suspend accounts without deleting them.
    You cannot modify your own account status.
    """
    if username == current_user.username:
        raise HTTPException(
            status_code=400,
            detail="Cannot modify your own account status"
        )

    user = await set_user_disabled(username, True)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {"message": f"User {username} disabled", "user": user.model_dump()}
