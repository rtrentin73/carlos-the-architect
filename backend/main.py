from dotenv import load_dotenv
import os

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from graph import carlos_graph
import json

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
        print(
            f"Design generated, length={len(design_doc)}, ronei_length={len(ronei_design)}, "
            f"audit_status={audit_status}, audit_report_len={len(audit_report)}, "
            f"security_len={len(security_report)}, cost_len={len(cost_report)}, "
            f"reliability_len={len(reliability_report)}, convo_len={len(conversation)}"
        )
        return {
            "design": design_doc,
            "ronei_design": ronei_design,
            "audit_status": audit_status,
            "audit_report": audit_report,
            "agent_chat": conversation,
            "security_report": security_report,
            "cost_report": cost_report,
            "reliability_report": reliability_report,
        }
    except Exception as e:
        print(f"Error in design endpoint: {e}")
        return {"error": str(e)}
