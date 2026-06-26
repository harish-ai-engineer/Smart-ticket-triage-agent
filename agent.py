"""Entry point: builds the graph, runs it over a ticket queue, and prints a summary."""

import uuid

from config import get_langfuse_handler
from graph import build_graph
from state import TicketState


def run_agent(tickets: list[dict]) -> list[dict]:
    """Run the triage graph over a queue of tickets."""
    app = build_graph()
    handler = get_langfuse_handler()

    thread_id = str(uuid.uuid4())
    invoke_config = {"configurable": {"thread_id": thread_id}, "callbacks": [handler]}

    initial_state: TicketState = {
        "pending_tickets": tickets,
        "current_ticket": {},
        "intent": "",
        "priority": "",
        "order_id": "",
        "order_data": {},
        "jira_ticket_id": "",
        "slack_notified": False,
        "customer_reply": "",
        "next_action": "",
        "iteration": 0,
        "processed": [],
    }

    app.invoke(initial_state, config=invoke_config)

    final_state = app.get_state(invoke_config).values
    processed = final_state.get("processed", [])

    print("\n[Router] ===== Triage Summary =====")
    for entry in processed:
        print(
            f"[Router] {entry['ticket_id']} | intent={entry['intent']} "
            f"priority={entry['priority']} jira={entry['jira_ticket_id']} "
            f"action={entry['next_action']}"
        )
    print(f"[Router] Total tickets processed: {len(processed)}")

    return processed


if __name__ == "__main__":
    from mock_data import sample_tickets

    run_agent(sample_tickets)
