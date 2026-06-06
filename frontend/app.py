import os
import json
import requests
import streamlit as st
from pathlib import Path

API_URL = os.getenv("API_URL", "http://localhost:8000")

def load_orders():
    try:
        orders_path = Path(__file__).parent.parent / "backend" / "database" / "orders.json"
        if orders_path.exists():
            return {o["id"]: o for o in json.load(open(orders_path))}
    except:
        pass
    return {}

st.set_page_config(
    page_title="AI Refund Agent",
    page_icon="🤖",
    layout="wide"
)

page = st.sidebar.radio("Navigation", ["🛒 Customer Portal", "📊 Admin Dashboard"])

if page == "🛒 Customer Portal":
    st.title("🛒 Refund Request Portal")
    st.caption("Submit your refund request below. Our AI agent will process it instantly.")

    st.info("📋 **Policy:** Refunds over $500 require human escalation · Final sale items cannot be refunded · 30-day return window (VIP: 60 days)")

    with st.form("refund_form"):
        col1, col2 = st.columns(2)
        with col1:
            customer_id = st.text_input("Customer ID", placeholder="e.g. C001")
            order_id = st.text_input("Order ID", placeholder="e.g. ORD001")
        with col2:
            amount = st.number_input(
                "Refund Amount ($)",
                min_value=0.01,
                max_value=10000.00,
                value=50.00,
                help="Enter amount > $500 to trigger human escalation"
            )
            reason = st.text_area(
                "Reason for Refund",
                placeholder="e.g. Product was defective"
            )
        submitted = st.form_submit_button(
            "Submit Refund Request",
            use_container_width=True
        )

    if submitted:
        if not customer_id or not order_id or not reason:
            st.error("Please fill in all fields.")
        else:
            with st.spinner("AI Agent is processing your request..."):
                try:
                    response = requests.post(
                        f"{API_URL}/refund",
                        json={
                            "customer_id": customer_id,
                            "order_id": order_id,
                            "reason": reason,
                            "amount_requested": amount
                        },
                        timeout=60
                    )
                    if response.status_code == 200:
                        data = response.json()
                        decision = data.get("decision", "UNKNOWN")

                        if decision == "APPROVED":
                            st.success(f"✅ Decision: **{decision}**")
                            if data.get("amount_approved"):
                                st.info(f"💰 Amount Approved: **${data['amount_approved']:.2f}**")
                        elif decision == "DENIED":
                            st.error(f"❌ Decision: **{decision}**")
                            st.write(f"**Reason:** {data.get('reason', '')}")
                        else:
                            st.warning(f"⏳ Decision: **{decision}** — Sent for human review")
                            st.write("Amount exceeds auto-approval limit. A human agent will review this request.")

                        st.subheader("🧠 Agent Reasoning")
                        steps = data.get("reasoning_steps", [])
                        for i, step in enumerate(steps, 1):
                            with st.expander(f"Step {i}"):
                                st.write(step)

                        if "history" not in st.session_state:
                            st.session_state.history = []
                        st.session_state.history.append(data)

                    else:
                        st.error(f"Error {response.status_code}: {response.text}")

                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to backend. Make sure it is running on port 8000.")
                except Exception as e:
                    st.error(f"Unexpected error: {str(e)}")

    if "history" in st.session_state and st.session_state.history:
        st.divider()
        st.subheader("📋 This Session's Requests")
        for item in reversed(st.session_state.history):
            icon = "🟢" if item["decision"] == "APPROVED" else "🔴" if item["decision"] == "DENIED" else "🟡"
            st.write(f"{icon} **{item['order_id']}** — {item['decision']} — {item['timestamp'][:19]}")

elif page == "📊 Admin Dashboard":
    st.title("📊 Admin Dashboard")
    st.caption("All agent decisions and reasoning logs.")

    col1, col2 = st.columns([1, 5])
    with col1:
        refresh = st.button("🔄 Refresh")

    if refresh or "logs_loaded" not in st.session_state:
        try:
            response = requests.get(f"{API_URL}/logs", timeout=10)
            if response.status_code == 200:
                st.session_state.logs = response.json().get("logs", [])
                st.session_state.logs_loaded = True
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to backend.")
            st.session_state.logs = []

    logs = st.session_state.get("logs", [])

    if not logs:
        st.info("No decisions logged yet. Submit a refund request first.")
    else:
        approved = sum(1 for l in logs if l.get("decision") == "APPROVED")
        denied = sum(1 for l in logs if l.get("decision") == "DENIED")
        escalated = sum(1 for l in logs if l.get("decision") == "ESCALATED")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total", len(logs))
        c2.metric("✅ Approved", approved)
        c3.metric("❌ Denied", denied)
        c4.metric("⏳ Escalated", escalated)

        st.divider()

        for log in reversed(logs):
            decision = log.get("decision", "UNKNOWN")
            icon = "✅" if decision == "APPROVED" else "❌" if decision == "DENIED" else "⏳"
            label = f"{icon} {log.get('order_id')} | {log.get('customer_id')} | **{decision}** | {log.get('timestamp', '')[:19]}"

            with st.expander(label):
                st.write(f"**Reason:** {log.get('reason', 'N/A')}")
                st.write("**Reasoning Steps:**")
                for i, step in enumerate(log.get("reasoning_steps", []), 1):
                    st.write(f"{i}. {step}")
                if log.get("amount_approved"):
                    st.write(f"**Amount Approved:** ${log['amount_approved']:.2f}")
                if log.get("escalation_reason"):
                    st.write(f"**Escalation Reason:** {log['escalation_reason']}")