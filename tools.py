"""Tool definitions used by the triage agent: order lookup, issue creation, Slack alerts."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.tools import tool
import requests
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


def _create_local_issue(summary: str, description: str, priority: str, order_id: str, intent: str) -> dict:
    """Persist a support issue locally when GitHub credentials are missing or blocked."""
    issues_path = Path("generated_issues.json")
    if issues_path.exists():
        try:
            issues = json.loads(issues_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            issues = []
    else:
        issues = []

    issue_number = len(issues) + 1
    issue_id = f"LOCAL-{issue_number:04d}"
    issue = {
        "issue_id": issue_id,
        "issue_number": issue_number,
        "summary": summary,
        "description": description,
        "priority": priority,
        "order_id": order_id,
        "intent": intent,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "local_fallback",
    }
    issues.append(issue)
    issues_path.write_text(json.dumps(issues, indent=2), encoding="utf-8")
    return issue


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
def create_support_issue(
    summary: str, description: str, priority: str, order_id: str, intent: str
) -> dict:
    """Create a GitHub support issue and return its generated issue ID."""
    github_enabled = os.getenv("ENABLE_GITHUB_ISSUES", "false").lower() == "true"
    github_token = os.getenv("GITHUB_TOKEN")
    github_repository = os.getenv("GITHUB_REPOSITORY")
    github_api_base = os.getenv("GITHUB_API_BASE", "https://api.github.com").rstrip("/")

    if github_enabled and github_token and github_repository:
        issue_body = (
            f"{description}\n\n"
            f"Priority: {priority}\n"
            f"Intent: {intent}\n"
            f"Order ID: {order_id or 'none'}"
        )
        url = f"{github_api_base}/repos/{github_repository}/issues"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {github_token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        payload = {
            "title": summary,
            "body": issue_body,
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        try:
            error_message = response.json().get("message", response.text)
        except ValueError:
            error_message = response.text
        if response.status_code == 401:
            print(
                "Failed to create GitHub issue: GitHub rejected GITHUB_TOKEN. "
                "Use a fine-grained token with Issues read/write access for GITHUB_REPOSITORY."
            )
            return _create_local_issue(summary, description, priority, order_id, intent)
        if response.status_code == 403:
            print(
                "Failed to create GitHub issue: GITHUB_TOKEN does not have permission "
                f"to create issues in {github_repository}. GitHub says: {error_message}"
            )
            return _create_local_issue(summary, description, priority, order_id, intent)
        if response.status_code == 404:
            print(
                "Failed to create GitHub issue: GITHUB_REPOSITORY="
                f"{github_repository!r} was not found or is not visible to the token. "
                f"GitHub says: {error_message}"
            )
            return _create_local_issue(summary, description, priority, order_id, intent)
        response.raise_for_status()
        issue = response.json()
        return {
            "issue_id": f"GH-{issue['number']}",
            "issue_number": issue["number"],
            "issue_url": issue["html_url"],
            "summary": summary,
            "description": description,
            "priority": priority,
            "order_id": order_id,
            "intent": intent,
        }

    return _create_local_issue(summary, description, priority, order_id, intent)


@tool
def notify_slack(channel: str, message: str, issue_id: str, priority: str) -> dict:
    """Send a Slack notification about a newly created support issue."""
    slack_enabled = os.getenv("ENABLE_SLACK_NOTIFICATIONS", "false").lower() == "true"
    slack_bot_token = os.getenv("SLACK_BOT_TOKEN")

    if slack_enabled and slack_bot_token:
        try:
            client = WebClient(token=slack_bot_token)
            response = client.chat_postMessage(channel=channel, text=message)
        except SlackApiError as exc:
            error = exc.response.get("error", "unknown_error")
            print(f"Failed to send Slack notification: {error}")
            return {"channel": channel, "issue_id": issue_id, "sent": False, "error": error}

        print(f"[Tool] Slack sent -> #{channel} | {issue_id} ({priority})")
        return {
            "channel": channel,
            "issue_id": issue_id,
            "sent": True,
            "slack_ts": response.get("ts"),
        }

    print(f"[Tool] Slack -> #{channel} | {issue_id} ({priority}): {message}")
    return {"channel": channel, "issue_id": issue_id, "sent": True}


TOOLS = [fetch_order_data, create_support_issue, notify_slack]
