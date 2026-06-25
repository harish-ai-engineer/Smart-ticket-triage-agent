"""Tool definitions used by the triage agent: order lookup, Jira ticketing, Slack alerts."""

import random

from langchain_core.tools import tool

_MOCK_ORDERS: dict[str, dict] = {
    "ORD-84712": {
        "order_id": "ORD-84712",
        "items": ["Silver Earrings - Floral"],
        "total": 4200,
        "status": "delivered",
        "delivery_date": "2026-06-20",
    },
    "ORD-61033": {
        "order_id": "ORD-61033",
        "items": ["Gold Plated Necklace - Royal"],
        "total": 28990,
        "status": "delivered",
        "delivery_date": "2026-06-18",
    },
}


@tool
def fetch_order_data(order_id: str) -> dict:
    """Look up order details (items, total, status) for a given order ID."""
    # MOCK: replace this block with a real API call, e.g.:
    #   import requests
    #   resp = requests.get(f"{ORDERS_API_BASE_URL}/orders/{order_id}",
    #                        headers={"Authorization": f"Bearer {ORDERS_API_TOKEN}"})
    #   resp.raise_for_status()
    #   return resp.json()
    if order_id in _MOCK_ORDERS:
        return _MOCK_ORDERS[order_id]
    return {"order_id": order_id, "items": [], "total": 0, "status": "not_found"}


@tool
def create_jira_ticket(
    summary: str, description: str, priority: str, order_id: str, intent: str
) -> dict:
    """Create a Jira support ticket and return its generated ticket ID."""
    # MOCK: replace this block with a real Jira SDK call, e.g.:
    #   from jira import JIRA
    #   client = JIRA(server=JIRA_SERVER, basic_auth=(JIRA_USER, JIRA_API_TOKEN))
    #   issue = client.create_issue(
    #       project=JIRA_PROJECT_KEY,
    #       summary=summary,
    #       description=description,
    #       issuetype={"name": "Task"},
    #       priority={"name": priority.capitalize()},
    #       labels=[intent, order_id],
    #   )
    #   return {"jira_ticket_id": issue.key, "summary": summary}
    ticket_id = f"SUP-{random.randint(1000, 9999)}"
    return {
        "jira_ticket_id": ticket_id,
        "summary": summary,
        "description": description,
        "priority": priority,
        "order_id": order_id,
        "intent": intent,
    }


@tool
def notify_slack(channel: str, message: str, jira_ticket_id: str, priority: str) -> dict:
    """Send a Slack notification about a newly created support ticket."""
    # MOCK: replace this block with a real slack_sdk call, e.g.:
    #   from slack_sdk import WebClient
    #   client = WebClient(token=SLACK_BOT_TOKEN)
    #   client.chat_postMessage(channel=channel, text=message)
    print(f"[Tool] Slack -> #{channel} | {jira_ticket_id} ({priority}): {message}")
    return {"channel": channel, "jira_ticket_id": jira_ticket_id, "sent": True}


TOOLS = [fetch_order_data, create_jira_ticket, notify_slack]
