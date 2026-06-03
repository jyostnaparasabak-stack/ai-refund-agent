from pathlib import Path
import json


BASE_DIR = Path(__file__).parent


def get_customer(customer_id: str) -> dict | None:
    file_path = BASE_DIR / "customers.json"

    with open(file_path, "r", encoding="utf-8") as f:
        customers = json.load(f)

    return next((customer for customer in customers if customer.get("id") == customer_id), None)


def get_order(order_id: str) -> dict | None:
    file_path = BASE_DIR / "orders.json"

    with open(file_path, "r", encoding="utf-8") as f:
        orders = json.load(f)

    return next((order for order in orders if order.get("id") == order_id), None)


def get_policy() -> dict:
    file_path = BASE_DIR / "policy.json"

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_orders_by_customer(customer_id: str) -> list:
    file_path = BASE_DIR / "orders.json"

    with open(file_path, "r", encoding="utf-8") as f:
        orders = json.load(f)

    return [order for order in orders if order.get("customer_id") == customer_id]