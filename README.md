# AI Customer Support Refund Agent

An autonomous AI agent that processes e-commerce refund requests using
LangGraph orchestration, Gemini LLM, FastAPI backend, and Streamlit UI.
Fully containerized — runs with a single command.

## Quick Start

**1. Clone the repository**
git clone [https://github.com/YOUR_USERNAME/ai-refund-agent.git](https://github.com/jyostnaparasabak-stack/ai-refund-agent)
cd ai-refund-agent

**2. Add your API key**
cp .env.example .env

Open `.env` and add your key:

GOOGLE_API_KEY=your-key-here

Get a free key at: https://aistudio.google.com

**3. Run everything**
docker-compose up --build

**4. Open in browser**
- Customer Portal: http://localhost:8501
- Admin Dashboard: http://localhost:8501 → sidebar → Admin
- API Swagger Docs: http://localhost:8000/docs

---

## Architecture
Customer Portal (Streamlit)
↓  POST /refund
FastAPI Backend
↓
Policy Engine (deterministic rules)
├── Final sale?            → DENIED
├── Outside return window? → DENIED
├── Amount > $500?         → ESCALATED
└── All clear?             → APPROVED
↓
LangGraph Agent + Gemini LLM
└── Explains the decision with reasoning steps
↓
Decision logged → Admin Dashboard

┌─────────────────────────────────────────┐
│         FRONTEND (Streamlit :8501)       │
│  Customer chat window + Admin dashboard  │
└──────────────┬──────────────────────────┘
│ HTTP POST /refund
┌──────────────▼──────────────────────────┐
│         BACKEND (FastAPI :8000)          │
│  Request validation + routing + logging  │
└──────────────┬──────────────────────────┘
│
┌──────────────▼──────────────────────────┐
│       AGENT LAYER (LangGraph)            │
│                                          │
│  evaluate_policy()  ← deterministic      │
│  ├── final_sale?      → DENIED           │
│  ├── return window?   → DENIED           │
│  ├── amount > $500?   → ESCALATED        │
│  └── all clear?       → APPROVED         │
│                                          │
│  Gemini LLM ← explains decision only     │
│  Tools: lookup_customer, lookup_order,   │
│          check_policy                    │
└──────────────┬──────────────────────────┘
│
┌──────────────▼──────────────────────────┐
│         DATA LAYER (JSON files)          │
│  customers.json · orders.json ·          │
│  policy.json                             │
└─────────────────────────────────────────┘

## Agent Loop

1. Request arrives with customer_id, order_id, reason, amount
2. `evaluate_policy()` applies hard rules — deterministic, no LLM
3. Gemini LLM explains the decision with step-by-step reasoning
4. Response: APPROVED / DENIED / ESCALATED + reasoning steps
5. Every decision logged to logs/decisions.log

## Edge Cases Handled

- **Prompt injection** — policy engine is deterministic, LLM cannot override it
- **Final sale items** — always DENIED regardless of reason
- **High value refunds > $500** — always ESCALATED for human review
- **VIP customers** — 60-day return window instead of 30 days
- **Missing customer or order** — DENIED with clear error message
- **Backend down** — frontend shows a friendly error message

## API Endpoints

| Method | Endpoint      | Description                 |
|--------|---------------|-----------------------------|
| POST   | /refund       | Submit a refund request     |
| GET    | /logs         | Get last 50 decisions       |
| GET    | /escalations  | Get escalated cases only    |
| GET    | /health       | Health check                |
| GET    | /docs         | Swagger UI                  |

## Example

**Request:**
```json
{
  "customer_id": "C001",
  "order_id": "ORD001",
  "reason": "Product defective",
  "amount_requested": 250.00
}
```

**Response:**
```json
{
  "customer_id": "C001",
  "order_id": "ORD001",
  "decision": "APPROVED",
  "reason": "Refund satisfies policy requirements",
  "reasoning_steps": ["Customer found", "Order verified", "Policy passed"],
  "timestamp": "2026-06-01T10:30:00"
}
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| Backend | FastAPI + Uvicorn |
| Agent | LangGraph 1.0 (ReAct) |
| LLM | Google Gemini 2.0 Flash |
| Deployment | Docker + Docker Compose |
| Data | JSON flat files (mock CRM) |
