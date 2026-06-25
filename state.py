"""TypedDict definition for the ticket triage agent's shared graph state."""

from typing import TypedDict


class TicketState(TypedDict):
    """Shared state threaded through every node in the triage graph."""

    pending_tickets: list[dict]
    current_ticket: dict
    intent: str
    priority: str
    order_id: str
    order_data: dict
    jira_ticket_id: str
    slack_notified: bool
    customer_reply: str
    next_action: str
    iteration: int
    processed: list[dict]
