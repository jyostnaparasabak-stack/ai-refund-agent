import json
from pathlib import Path
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from agent.prompts import SYSTEM_PROMPT
from agent.tools import lookup_customer, lookup_order, check_policy
from database.db import get_customer, get_order, get_policy
from config import GOOGLE_API_KEY


LOG_FILE = Path(__file__).parent.parent / "logs" / "decisions.log"


# ---------------------------
# LLM + Agent Setup
# ---------------------------

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=GOOGLE_API_KEY,
    temperature=0
)

agent = create_react_agent(
    llm,
    tools=[
        lookup_customer,
        lookup_order,
        check_policy
    ]
)


# ---------------------------
# Policy Evaluation
# ---------------------------

def evaluate_policy(
    customer,
    order,
    amount_requested,
    reason
):
    policy = get_policy()

    if customer is None:
        return "DENIED", "Customer not found"

    if order is None:
        return "DENIED", "Order not found"

    if order["customer_id"] != customer["id"]:
        return "DENIED", "Order does not belong to customer"

    if order.get("final_sale", False):
        return "DENIED", "Final sale item"

    purchase_date = datetime.fromisoformat(
        order["purchase_date"]
    )

    days_since_order = (
        datetime.now() - purchase_date
    ).days

    allowed_days = policy["return_window_days"]

    if customer.get("vip_status", False):
        allowed_days = policy["vip_benefits"][
            "extended_return_days"
        ]

    if days_since_order > allowed_days:
        return (
            "DENIED",
            f"Outside return window ({allowed_days} days)"
        )

    if amount_requested > policy[
        "require_human_review_above"
    ]:
        return (
            "ESCALATED",
            "Refund exceeds approval threshold"
        )

    return (
        "APPROVED",
        "Refund satisfies policy requirements"
    )


# ---------------------------
# Main Agent Entry
# ---------------------------

def run_agent(request: dict) -> dict:

    customer_id = request["customer_id"]
    order_id = request["order_id"]
    reason = request["reason"]
    amount_requested = request["amount_requested"]

    customer = get_customer(customer_id)
    order = get_order(order_id)

    decision, policy_reason = evaluate_policy(
        customer,
        order,
        amount_requested,
        reason
    )

    # Default reasoning (works even if Gemini fails)
    reasoning_steps = [
        f"Customer lookup completed for {customer_id}",
        f"Order lookup completed for {order_id}",
        "Policy validation completed",
        f"Decision: {decision}",
        f"Reason: {policy_reason}"
    ]

    # Optional Gemini explanation
    try:

        result = agent.invoke(
            {
                "messages": [
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(
                        content=f"""
A refund decision has already been made.

Decision:
{decision}

Policy Reason:
{policy_reason}

Customer ID:
{customer_id}

Order ID:
{order_id}

Refund Reason:
{reason}

Explain the decision clearly and professionally.
"""
                    )
                ]
            }
        )

        llm_messages = []

        for msg in result["messages"]:
            if hasattr(msg, "content"):
                content = str(msg.content).strip()

                if content:
                    llm_messages.append(content)

        if llm_messages:
            reasoning_steps.extend(llm_messages)

    except Exception as e:

        reasoning_steps.append(
            f"LLM explanation unavailable: {str(e)}"
        )

    response = {
        "customer_id": customer_id,
        "order_id": order_id,
        "decision": decision,
        "reason": policy_reason,
        "reasoning_steps": reasoning_steps,
        "timestamp": datetime.now().isoformat()
    }

    LOG_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(
            json.dumps(response)
            + "\n"
        )

    return response