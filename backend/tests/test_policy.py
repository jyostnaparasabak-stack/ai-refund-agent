from agent.graph import evaluate_policy


def test_large_refund_escalated():
    customer = {"id": "C001", "vip_status": False}
    order = {
        "id": "ORD001",
        "customer_id": "C001",
        "final_sale": False,
        "purchase_date": "2026-05-01"
    }
    decision, _ = evaluate_policy(customer, order, 1000, "Defective")
    assert decision == "ESCALATED"


def test_final_sale_denied():
    customer = {"id": "C002", "vip_status": False}
    order = {
        "id": "ORD002",
        "customer_id": "C002",
        "final_sale": True,
        "purchase_date": "2026-05-20"
    }
    decision, _ = evaluate_policy(customer, order, 100, "Changed mind")
    assert decision == "DENIED"


def test_normal_refund_approved():
    customer = {"id": "C003", "vip_status": False}
    order = {
        "id": "ORD003",
        "customer_id": "C003",
        "final_sale": False,
        "purchase_date": "2026-05-25"
    }
    decision, _ = evaluate_policy(customer, order, 200, "Defective product")
    assert decision == "APPROVED"