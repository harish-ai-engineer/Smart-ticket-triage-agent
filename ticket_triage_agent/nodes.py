"""Node functions for each step of the ticket triage graph."""

import json

from langchain_core.messages import HumanMessage, SystemMessage

from config import get_classifier_llm, get_langfuse_handler, get_llm
from state import TicketState
from tools import create_jira_ticket, fetch_order_data, notify_slack

ESCALATION_TOTAL_THRESHOLD = 15000

CLASSIFIER_SYSTEM_PROMPT = """You are a customer support ticket classifier for an e-commerce \
jewelry store. Read the ticket and output ONLY a JSON object with these exact keys:
{"intent": "refund|missing_item|damaged|tracking|other", \
"priority": "low|medium|urgent", "order_id": "<order id found in the message, or empty string>"}
Do not include any text outside the JSON object."""

RESPONDER_SYSTEM_PROMPT = """You are a customer support agent for an e-commerce jewelry store. \
Write a friendly, empathetic 3-5 sentence reply to the customer based on the ticket, intent, \
priority, and order data provided. Then output ONLY a JSON object with these exact keys:
{"reply": "<the 3-5 sentence reply text>", "next_action": "loop|escalate|done"}
Do not include any text outside the JSON object."""


def fetch_next_ticket(state: TicketState) -> dict:
    """Pop the next ticket off the queue and bump the iteration counter."""
    pending = state["pending_tickets"]
    current = pending[0]
    remaining = pending[1:]
    iteration = state.get("iteration", 0) + 1
    print(f"[Router] Fetched {current['ticket_id']} (iteration {iteration})")
    return {
        "pending_tickets": remaining,
        "current_ticket": current,
        "iteration": iteration,
    }


def llm_classifier(state: TicketState) -> dict:
    """Call the LLM to classify intent, priority, and extract the order ID."""
    ticket = state["current_ticket"]
    llm = get_classifier_llm()
    handler = get_langfuse_handler()

    messages = [
        SystemMessage(content=CLASSIFIER_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"ticket_id: {ticket['ticket_id']}\n"
                f"customer_name: {ticket['customer_name']}\n"
                f"subject: {ticket['subject']}\n"
                f"message: {ticket['message']}"
            )
        ),
    ]

    response = llm.invoke(messages, config={"callbacks": [handler]})

    try:
        parsed = json.loads(response.content)
        intent = parsed.get("intent", "other")
        priority = parsed.get("priority", "medium")
        order_id = parsed.get("order_id", "")
    except (json.JSONDecodeError, AttributeError, TypeError):
        intent, priority, order_id = "other", "medium", ""

    print(f"[LLM #1] intent={intent} priority={priority} order_id={order_id or '<none>'}")
    return {"intent": intent, "priority": priority, "order_id": order_id}


def tools_node(state: TicketState) -> dict:
    """Run order lookup, Jira ticket creation, and Slack notification in sequence."""
    ticket = state["current_ticket"]
    order_id = state["order_id"]
    intent = state["intent"]
    priority = state["priority"]

    order_data = fetch_order_data.invoke({"order_id": order_id}) if order_id else {}
    print(f"[Tool] fetch_order_data({order_id or '<none>'}) -> {order_data}")

    summary = f"[{priority.upper()}] {intent} - {ticket['subject']}"
    description = (
        f"Ticket: {ticket['ticket_id']}\n"
        f"Customer: {ticket['customer_name']}\n"
        f"Message: {ticket['message']}\n"
        f"Order data: {order_data}"
    )
    jira_result = create_jira_ticket.invoke(
        {
            "summary": summary,
            "description": description,
            "priority": priority,
            "order_id": order_id,
            "intent": intent,
        }
    )
    jira_ticket_id = jira_result["jira_ticket_id"]
    print(f"[Tool] create_jira_ticket -> {jira_ticket_id}")

    channel = "support-urgent" if priority == "urgent" else "support-general"
    slack_message = f"New ticket {jira_ticket_id} ({priority}) for {ticket['ticket_id']}: {summary}"
    slack_result = notify_slack.invoke(
        {
            "channel": channel,
            "message": slack_message,
            "jira_ticket_id": jira_ticket_id,
            "priority": priority,
        }
    )

    return {
        "order_data": order_data,
        "jira_ticket_id": jira_ticket_id,
        "slack_notified": slack_result["sent"],
    }


def llm_responder(state: TicketState) -> dict:
    """Call the LLM to draft a customer reply and decide the routing action."""
    ticket = state["current_ticket"]
    llm = get_llm()
    handler = get_langfuse_handler()

    messages = [
        SystemMessage(content=RESPONDER_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"ticket_id: {ticket['ticket_id']}\n"
                f"customer_name: {ticket['customer_name']}\n"
                f"message: {ticket['message']}\n"
                f"intent: {state['intent']}\n"
                f"priority: {state['priority']}\n"
                f"order_data: {state['order_data']}\n"
                f"jira_ticket_id: {state['jira_ticket_id']}"
            )
        ),
    ]

    response = llm.invoke(messages, config={"callbacks": [handler]})

    try:
        parsed = json.loads(response.content)
        reply = parsed.get("reply", "")
        llm_next_action = parsed.get("next_action", "done")
    except (json.JSONDecodeError, AttributeError, TypeError):
        reply = "Thank you for reaching out, our team will follow up shortly."
        llm_next_action = "done"

    order_total = state["order_data"].get("total", 0)
    high_value_escalation = (
        state["intent"] in ("refund", "damaged") and order_total > ESCALATION_TOTAL_THRESHOLD
    )

    if high_value_escalation:
        next_action = "escalate"
    elif state["pending_tickets"]:
        next_action = "loop"
    else:
        next_action = llm_next_action if llm_next_action == "escalate" else "done"

    print(f"[LLM #2] reply_preview={reply[:60]!r} next_action={next_action}")

    processed_entry = {
        "ticket_id": ticket["ticket_id"],
        "intent": state["intent"],
        "priority": state["priority"],
        "jira_ticket_id": state["jira_ticket_id"],
        "reply": reply,
        "next_action": next_action,
    }

    return {
        "customer_reply": reply,
        "next_action": next_action,
        "processed": state["processed"] + [processed_entry],
    }


def human_escalation(state: TicketState) -> dict:
    """Print escalation details for a human agent to review before resuming the graph."""
    ticket = state["current_ticket"]
    print("[Escalation] ==========================================")
    print(f"[Escalation] Ticket {ticket['ticket_id']} requires human review")
    print(f"[Escalation] Customer: {ticket['customer_name']}")
    print(f"[Escalation] Intent: {state['intent']} | Priority: {state['priority']}")
    print(f"[Escalation] Order total: {state['order_data'].get('total', 0)}")
    print(f"[Escalation] Jira: {state['jira_ticket_id']}")
    print(f"[Escalation] Draft reply: {state['customer_reply']}")
    print("[Escalation] ==========================================")
    return {"next_action": "done"}
