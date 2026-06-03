from pydantic import BaseModel
from typing import Optional

class RefundRequest(BaseModel):
    customer_id: str
    order_id: str
    reason: str
    amount_requested: float

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "customer_id": "C001",
                    "order_id": "ORD001",
                    "reason": "Product defective",
                    "amount_requested": 250.00
                }
            ]
        }
    }


class RefundDecision(BaseModel):
    customer_id: str
    order_id: str
    decision: str  # APPROVED, DENIED, or ESCALATED
    reason: str
    reasoning_steps: list[str]
    amount_approved: Optional[float] = None
    escalation_reason: Optional[str] = None
    timestamp: str


class LogEntry(RefundDecision):
    request_id: str