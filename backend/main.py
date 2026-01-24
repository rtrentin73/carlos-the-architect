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
from auth import (
    User,
    UserCreate,
    Token,
    authenticate_user,
    create_access_token,
    create_user,
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from document_parser import extract_text_from_path, MAX_FILE_SIZE
from document_tasks import create_task, get_task, get_user_tasks, TaskStatus
from middleware.rate_limit import limiter, rate_limit_exceeded_handler
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

    print("✅ Shutdown complete")


app = FastAPI(title="Carlos the Architect API", lifespan=lifespan)

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


@app.get("/health")
async def health():
    """Health check endpoint for container orchestration."""
    pool = get_pool()
    pool_stats = pool.get_pool_stats()

    return {
        "status": "healthy",
        "pools": pool_stats
    }


# Auth endpoints
@app.post("/auth/register", response_model=User)
async def register(user_data: UserCreate):
    """Register a new user."""
    return create_user(user_data)


@app.post("/auth/login", response_model=Token)
@limiter.limit("20/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and get access token."""
    user = authenticate_user(form_data.username, form_data.password)
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


@app.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """Get current user info."""
    return current_user


async def _process_document_background(task_id: str, file_path: str):
    """Background task to process document"""
    task = get_task(task_id)
    if not task:
        return

    try:
        task.update_status(TaskStatus.PROCESSING)
        print(f"📄 Processing document {task.filename} for task {task_id}")

        # Extract text from file
        extracted_text = extract_text_from_path(file_path)

        # Update task with result
        task.update_status(TaskStatus.COMPLETED, extracted_text=extracted_text)
        print(f"✅ Document {task.filename} processed successfully (task {task_id})")

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


@app.post("/upload-document")
@limiter.limit("30/hour")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload a document for asynchronous text extraction.

    Supports: PDF, DOCX, TXT, MD, XLSX (max 50MB)

    Returns a task ID to poll for processing status.
    Use GET /documents/{task_id} to check status and retrieve extracted text.
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


@app.get("/documents/{task_id}")
async def get_document_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Check document processing status and retrieve extracted text.

    Returns:
        - task_id: Unique task identifier
        - filename: Original filename
        - status: pending | processing | completed | failed
        - extracted_text: Extracted text (only when completed)
        - error: Error message (only when failed)
    """
    task = get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Verify task belongs to user
    if task.username != current_user.username:
        raise HTTPException(status_code=403, detail="Access denied")

    return task.to_dict()


@app.get("/documents")
async def list_user_documents(
    current_user: User = Depends(get_current_active_user),
    limit: int = 10
):
    """List recent document processing tasks for current user"""
    tasks = get_user_tasks(current_user.username, limit=limit)
    return {
        "tasks": [task.to_dict() for task in tasks],
        "count": len(tasks)
    }


@app.post("/design")
@limiter.limit("10/hour")
async def design(request: Request, req: dict, current_user: User = Depends(get_current_active_user)):
    """Return a full design document and its security audit.

    Can be called in two phases:
    1. Initial call with 'text' (requirements) - returns clarifying questions
    2. Follow-up call with 'user_answers' - completes the design with refined requirements

    Rate limited to 10 requests per hour per user.
    """
    print(f"Received request from {current_user.username}: {req}")
    try:
        # Build initial state
        initial_state = {
            "requirements": req["text"],
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
        }
    except Exception as e:
        print(f"Error in design endpoint: {e}")
        return {"error": str(e)}


@app.post("/design-stream")
@limiter.limit("10/hour")
async def design_stream(request: Request, req: dict, current_user: User = Depends(get_current_active_user)):
    """Stream design generation with real-time agent and token events.

    Can be called in two phases:
    1. Initial call with 'text' (requirements) - returns clarifying questions
    2. Follow-up call with 'user_answers' - completes the design with refined requirements

    Rate limited to 10 requests per hour per user.
    Caches common patterns for instant responses.
    """
    print(f"Received streaming request from {current_user.username}: {req}")

    # Check cache for common patterns (skip if user provided answers - that's a follow-up)
    cache = get_cache()
    cache_key = None
    if not req.get("user_answers"):
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
            # Build initial state
            initial_state = {
                "requirements": req["text"],
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
                "clarification_needed": clarification_needed,
                # Structured data for programmatic access
                "structured_data": {
                    "security": final_state.get("security_data"),
                    "cost": final_state.get("cost_data"),
                    "reliability": final_state.get("reliability_data"),
                },
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


@app.get("/cache/stats")
async def get_cache_stats(current_user: User = Depends(get_current_active_user)):
    """Get cache statistics."""
    cache = get_cache()
    stats = await cache.get_stats()
    return {
        "cache": stats,
        "status": "enabled",
        "ttl_hours": cache.ttl_hours,
    }


@app.post("/cache/clear")
async def clear_cache(current_user: User = Depends(get_current_active_user)):
    """Clear the design pattern cache. Admin only."""
    # In production, add admin check here
    cache = get_cache()
    old_stats = await cache.get_stats()
    cleared = await cache.clear()
    return {
        "message": "Cache cleared",
        "cleared_entries": cleared,
    }


# ============================================================================
# Deployment Feedback Endpoints
# ============================================================================

@app.post("/feedback/deployment")
async def submit_deployment_feedback(
    feedback: DeploymentFeedback,
    current_user: User = Depends(get_current_active_user)
):
    """
    Submit feedback about a deployed design.

    Track deployment outcomes to:
    - Monitor success rates
    - Identify common issues
    - Improve design quality over time
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


@app.get("/feedback/my-feedback")
async def get_my_feedback(
    current_user: User = Depends(get_current_active_user),
    limit: int = 20
):
    """Get deployment feedback submitted by the current user."""
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


@app.get("/feedback/analytics")
async def get_deployment_analytics(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get aggregate deployment analytics.

    Returns:
    - Total designs tracked
    - Deployment rate
    - Success rate
    - Average satisfaction rating
    - Common issues encountered
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
