"""Tool definitions used by the triage agent: order lookup, Jira ticketing, Slack alerts."""

import os
import random

from jira.exceptions import JIRAError
from langchain_core.tools import tool
from jira import JIRA
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

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
    jira_server = os.getenv("JIRA_SERVER")
    jira_user = os.getenv("JIRA_USER")
    jira_api_token = os.getenv("JIRA_API_TOKEN")
    jira_project_key = os.getenv("JIRA_PROJECT_KEY", "SUP")

    if jira_server and jira_user and jira_api_token and jira_project_key:
        priority_name = {
            "urgent": "High",
            "medium": "Medium",
            "low": "Low",
        }.get(priority, "Medium")

        labels = [label for label in (intent, order_id) if label]

        try:
            client = JIRA(server=jira_server, basic_auth=(jira_user, jira_api_token))
            client.myself()
            issue = client.create_issue(
                project=jira_project_key,
                summary=summary,
                description=description,
                issuetype={"name": "Task"},
                priority={"name": priority_name},
                labels=labels,
            )
        except JIRAError as exc:
            if exc.status_code == 401:
                raise RuntimeError(
                    "Failed to create Jira ticket: Jira rejected JIRA_USER/JIRA_API_TOKEN. "
                    "Use your Atlassian account email as JIRA_USER and a Jira API token "
                    "as JIRA_API_TOKEN."
                ) from exc
            if exc.status_code == 404 and "No project could be found" in str(exc):
                raise RuntimeError(
                    "Failed to create Jira ticket: JIRA_PROJECT_KEY="
                    f"{jira_project_key!r} is not visible to this Jira account. "
                    "Set JIRA_PROJECT_KEY to an existing project key and make sure "
                    "JIRA_USER has Browse Projects and Create Issues permission."
                ) from exc
            raise RuntimeError(f"Failed to create Jira ticket: {exc}") from exc
        except Exception as exc:
            raise RuntimeError(f"Failed to create Jira ticket: {exc}") from exc

        return {
            "jira_ticket_id": issue.key,
            "summary": summary,
            "description": description,
            "priority": priority,
            "order_id": order_id,
            "intent": intent,
            "jira_url": f"{jira_server.rstrip('/')}/browse/{issue.key}",
        }

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
    slack_bot_token = os.getenv("SLACK_BOT_TOKEN")

    if slack_bot_token:
        try:
            client = WebClient(token=slack_bot_token)
            response = client.chat_postMessage(channel=channel, text=message)
        except SlackApiError as exc:
            error = exc.response.get("error", "unknown_error")
            raise RuntimeError(f"Failed to send Slack notification: {error}") from exc

        print(f"[Tool] Slack sent -> #{channel} | {jira_ticket_id} ({priority})")
        return {
            "channel": channel,
            "jira_ticket_id": jira_ticket_id,
            "sent": True,
            "slack_ts": response.get("ts"),
        }

    print(f"[Tool] Slack -> #{channel} | {jira_ticket_id} ({priority}): {message}")
    return {"channel": channel, "jira_ticket_id": jira_ticket_id, "sent": True}


TOOLS = [fetch_order_data, create_jira_ticket, notify_slack]
