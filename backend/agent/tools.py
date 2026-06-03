import json

from langchain_core.tools import tool

from database.db import (
    get_customer,
    get_order,
    get_policy
)


@tool
def lookup_customer(customer_id: str) -> str:
    """
    Look up a customer by customer ID and return
    the customer record as a JSON string.
    """
    customer = get_customer(customer_id)

    if customer is None:
        return json.dumps(
            {
                "error": f"Customer '{customer_id}' not found"
            }
        )

    return json.dumps(customer)


@tool
def lookup_order(order_id: str) -> str:
    """
    Look up an order by order ID and return
    the order record as a JSON string.
    """
    order = get_order(order_id)

    if order is None:
        return json.dumps(
            {
                "error": f"Order '{order_id}' not found"
            }
        )

    return json.dumps(order)


@tool
def check_policy(
    amount: float,
    is_final_sale: bool,
    days_since_order: int,
    is_vip: bool,
) -> str:
    """
    Evaluate refund eligibility against
    company refund policy rules.
    """

    policy = get_policy()

    allowed_days = policy[
        "return_window_days"
    ]

    review_limit = policy[
        "require_human_review_above"
    ]

    if is_vip:

        allowed_days = policy[
            "vip_benefits"
        ][
            "extended_return_days"
        ]

        review_limit = policy[
            "vip_benefits"
        ].get(
            "higher_limit",
            review_limit
        )

    if days_since_order > allowed_days:
        return json.dumps(
            {
                "eligible": False,
                "action": "DENIED",
                "reason": "Outside return window"
            }
        )

    if (
        is_final_sale
        and not policy.get(
            "final_sale_refundable",
            False
        )
    ):
        return json.dumps(
            {
                "eligible": False,
                "action": "DENIED",
                "reason": "Final sale item"
            }
        )

    if float(amount) > float(review_limit):
        return json.dumps(
            {
                "eligible": False,
                "action": "ESCALATED",
                "reason": "Human review required"
            }
        )

    return json.dumps(
        {
            "eligible": True,
            "action": "APPROVED",
            "reason": "Eligible under policy"
        }
    )