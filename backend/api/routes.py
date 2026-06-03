import json
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, HTTPException
from models import RefundRequest, RefundDecision
from agent.graph import run_agent

router = APIRouter(tags=["refund"])

LOG_FILE = Path(__file__).parent.parent / "logs" / "decisions.log"
ESCALATION_FILE = Path(__file__).parent.parent / "logs" / "escalations.jsonl"


@router.post("/refund", response_model=RefundDecision)
async def process_refund(request: RefundRequest):
    try:
        result = run_agent({
            "customer_id": request.customer_id,
            "order_id": request.order_id,
            "reason": request.reason,
            "amount_requested": request.amount_requested
        })

        if result["decision"] == "ESCALATED":
            with open(ESCALATION_FILE, "a") as f:
                f.write(json.dumps(result) + "\n")

        return RefundDecision(**result)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    
@router.get("/escalations")
async def get_escalations():
    if not ESCALATION_FILE.exists():
        return {"items": []}

    items = []

    for line in ESCALATION_FILE.read_text().splitlines():
        items.append(json.loads(line))

    return {"items": items}


@router.get("/logs")
async def get_logs():
    try:
        if not LOG_FILE.exists():
            return {"logs": []}
        lines = LOG_FILE.read_text().strip().splitlines()
        logs = [json.loads(line) for line in lines[-50:] if line.strip()]
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health():
    return {"status": "ok"}

