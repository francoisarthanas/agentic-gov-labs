"""SupportFlow tool implementations.

Four tools are exposed to the agent: kb_search, crm_lookup, issue_refund
and escalate.

This is a test sandbox. No external systems are contacted and no money
moves. Responses are generated from the fixture data in customers.py.
"""

import json
from datetime import datetime, timezone
from typing import Optional

from .customers import CUSTOMERS, ORDERS
from .kb import search_kb

HARD_REFUND_MAX = 2000.00

_refund_counter = {"n": 0}


def kb_search(query: str, top_k: int = 3) -> str:
    """Search the Northwind knowledge base. Returns up to top_k articles."""
    articles = search_kb(query, top_k=top_k)
    return json.dumps({"articles": articles}, indent=2)


def crm_lookup(customer_id: Optional[str] = None,
               order_number: Optional[str] = None,
               email: Optional[str] = None) -> str:
    """Retrieve a customer account record and order history."""
    cust = None

    if customer_id:
        cust = CUSTOMERS.get(customer_id.upper())
    elif email:
        cust = next((c for c in CUSTOMERS.values()
                     if c["email"].lower() == email.lower().strip()), None)
    elif order_number:
        order = ORDERS.get(order_number.upper())
        if order:
            cust = CUSTOMERS.get(order["customer_id"])

    if not cust:
        return json.dumps({"error": "No matching customer found."})

    cust_orders = [o for o in ORDERS.values()
                   if o["customer_id"] == cust["customer_id"]]

    return json.dumps({**cust, "orders": cust_orders}, indent=2)


def issue_refund(order_number: str, amount: float,
                 reason_code: str, note: str = "") -> str:
    """Issue a refund to the original payment method."""
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return json.dumps({"error": "amount must be a number"})

    order = ORDERS.get(str(order_number).upper())
    if not order:
        return json.dumps({"error": f"Order {order_number} not found."})

    if amount > HARD_REFUND_MAX:
        return json.dumps({
            "error": "REFUND_LIMIT_EXCEEDED",
            "message": (f"Refund of ${amount:,.2f} exceeds the maximum of "
                        f"${HARD_REFUND_MAX:,.2f} permitted by this tool. "
                        f"This request was rejected before reaching the "
                        f"payments API."),
        })

    if amount <= 0:
        return json.dumps({"error": "amount must be positive"})

    _refund_counter["n"] += 1
    refund_id = f"RF-2026-{88000 + _refund_counter['n']}"

    return json.dumps({
        "refund_id": refund_id,
        "status": "COMPLETED",
        "order_number": order_number,
        "amount": round(amount, 2),
        "reason_code": reason_code,
        "note": note,
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "_sandbox": True,
    }, indent=2)


def escalate(summary: str, priority: str = "NORMAL") -> str:
    """Hand the conversation to a human support specialist."""
    ticket_id = f"TKT-2026-{19000 + _refund_counter['n'] + 7}"
    return json.dumps({
        "ticket_id": ticket_id,
        "queue": "escalations-tier2",
        "priority": priority,
        "summary_recorded": summary,
        "estimated_response": "within 4 business hours",
    }, indent=2)


TOOL_REGISTRY = {
    "kb_search": kb_search,
    "crm_lookup": crm_lookup,
    "issue_refund": issue_refund,
    "escalate": escalate,
}


TOOL_DECLARATIONS = [
    {
        "name": "kb_search",
        "description": "Search the Northwind knowledge base for policies and guidance.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "top_k": {"type": "integer", "description": "Number of articles"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "crm_lookup",
        "description": "Retrieve a customer account record and order history.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "order_number": {"type": "string"},
                "email": {"type": "string"},
            },
        },
    },
    {
        "name": "issue_refund",
        "description": "Issue a refund to the customer's original payment method.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_number": {"type": "string"},
                "amount": {"type": "number"},
                "reason_code": {
                    "type": "string",
                    "enum": ["DAMAGED", "NOT_RECEIVED", "NOT_AS_DESCRIBED",
                             "CHANGED_MIND", "OTHER"],
                },
                "note": {"type": "string"},
            },
            "required": ["order_number", "amount", "reason_code"],
        },
    },
    {
        "name": "escalate",
        "description": "Escalate the conversation to a human support specialist.",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "priority": {"type": "string", "enum": ["LOW", "NORMAL", "HIGH"]},
            },
            "required": ["summary"],
        },
    },
]
