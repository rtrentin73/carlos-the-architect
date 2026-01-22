from dotenv import load_dotenv
import os

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from graph import carlos_graph
import json
from datetime import datetime, timezone

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],  # Allow both common Vite ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/design")
async def design(req: dict):
    """Return a full design document and its security audit."""
    print(f"Received request: {req}")
    try:
        result = await carlos_graph.ainvoke(
            {
                "requirements": req["text"],
                "conversation": "",
                "scenario": req.get("scenario"),
                "priorities": req.get("priorities", {}),
            },
            version="v2",
        )
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
        }
    except Exception as e:
        print(f"Error in design endpoint: {e}")
        return {"error": str(e)}


@app.post("/design-stream")
async def design_stream(req: dict):
    """Stream design generation with real-time agent and token events."""
    print(f"Received streaming request: {req}")

    async def event_generator():
        final_state = {}
        try:
            # Stream events from LangGraph
            async for event in carlos_graph.astream(
                {
                    "requirements": req["text"],
                    "conversation": "",
                    "scenario": req.get("scenario"),
                    "priorities": req.get("priorities", {}),
                },
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

                    # For Carlos: emit token events
                    if "design_tokens" in node_output and node_output["design_tokens"]:
                        for token in node_output["design_tokens"]:
                            token_event = {
                                "type": "token",
                                "agent": "carlos",
                                "content": token,
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            }
                            yield f"data: {json.dumps(token_event)}\n\n"

                    # For Ronei: emit token events
                    if "ronei_tokens" in node_output and node_output["ronei_tokens"]:
                        for token in node_output["ronei_tokens"]:
                            token_event = {
                                "type": "token",
                                "agent": "ronei_design",
                                "content": token,
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            }
                            yield f"data: {json.dumps(token_event)}\n\n"

                    # For other agents: emit field_update events
                    field_mappings = {
                        "security": "security_report",
                        "cost": "cost_report",
                        "reliability": "reliability_report",
                        "audit": "audit_report",
                        "recommender": "recommendation"
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
            complete_summary = {
                "type": "complete",
                "summary": {
                    "design": final_state.get("design_doc", ""),
                    "ronei_design": final_state.get("ronei_design", ""),
                    "audit_status": final_state.get("audit_status", ""),
                    "audit_report": final_state.get("audit_report", ""),
                    "recommendation": final_state.get("recommendation", ""),
                    "agent_chat": final_state.get("conversation", ""),
                    "security_report": final_state.get("security_report", ""),
                    "cost_report": final_state.get("cost_report", ""),
                    "reliability_report": final_state.get("reliability_report", ""),
                },
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
        }
    )
