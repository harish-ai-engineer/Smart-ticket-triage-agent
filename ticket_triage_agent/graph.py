"""Builds and compiles the LangGraph StateGraph for ticket triage."""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from nodes import fetch_next_ticket, human_escalation, llm_classifier, llm_responder, tools_node
from state import TicketState


def route_after_responder(state: TicketState) -> str:
    """Pick the next node based on the next_action decided by llm_responder."""
    next_action = state["next_action"]
    if next_action == "loop":
        return "loop"
    if next_action == "escalate":
        return "escalate"
    return END


def build_graph():
    """Construct, wire, and compile the ticket triage StateGraph."""
    graph = StateGraph(TicketState)

    graph.add_node("fetch_next_ticket", fetch_next_ticket)
    graph.add_node("llm_classifier", llm_classifier)
    graph.add_node("tools_node", tools_node)
    graph.add_node("llm_responder", llm_responder)
    graph.add_node("human_escalation", human_escalation)

    graph.set_entry_point("fetch_next_ticket")

    graph.add_edge("fetch_next_ticket", "llm_classifier")
    graph.add_edge("llm_classifier", "tools_node")
    graph.add_edge("tools_node", "llm_responder")

    graph.add_conditional_edges(
        "llm_responder",
        route_after_responder,
        {
            "loop": "fetch_next_ticket",
            "escalate": "human_escalation",
            END: END,
        },
    )

    graph.add_edge("human_escalation", END)

    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer, interrupt_before=["human_escalation"])
