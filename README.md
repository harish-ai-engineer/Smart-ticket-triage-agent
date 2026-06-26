# Ticket Triage Agent

A LangGraph agent that processes a queue of e-commerce support tickets, classifying each
one's intent and priority, looking up the related order, filing a Jira ticket, alerting
the right Slack channel, and drafting a customer reply — escalating high-value refund or
damage claims to a human before closing them out. Every LLM call and tool invocation is
traced through Langfuse-compatible callbacks (AgentGuard), giving full visibility into
cost, latency, and decisions per ticket.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env` with your `OPENAI_API_KEY` and Langfuse/AgentGuard keys
(`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`). Jira and Slack keys are
only required once you swap the mock tools for the real APIs (see below).

## Run

```bash
python agent.py
```

This runs the graph over the three sample tickets defined in `mock_data.py` and prints a
summary at the end.

## Graph flow

```
                ┌──────────────────────────────────────────────┐
                │                                                │
                ▼                                                │
START ──▶ fetch_next_ticket ──▶ llm_classifier ──▶ tools_node ──▶ llm_responder
                                                                       │
                                                          ┌────────────┼────────────┐
                                                          │            │            │
                                                        "loop"     "escalate"     "done"
                                                          │            │            │
                                                          ▼            ▼            ▼
                                                   (back to top) human_escalation   END
                                                                       │
                                                                       ▼
                                                                      END
```

- **fetch_next_ticket** — pops the next ticket off the queue.
- **llm_classifier** (LLM call #1) — classifies `intent`, `priority`, and extracts `order_id`.
- **tools_node** — looks up the order, files a Jira ticket, and notifies Slack.
- **llm_responder** (LLM call #2) — drafts a customer reply and decides `next_action`.
- **human_escalation** — pauses (`interrupt_before`) for refund/damaged tickets over
  ₹15,000 before closing.

## Swapping mock tools for real APIs

**Jira** (`tools.py::create_jira_ticket`):

```python
from jira import JIRA
client = JIRA(server=JIRA_SERVER, basic_auth=(JIRA_USER, JIRA_API_TOKEN))
issue = client.create_issue(
    project=JIRA_PROJECT_KEY,
    summary=summary,
    description=description,
    issuetype={"name": "Task"},
    priority={"name": priority.capitalize()},
    labels=[intent, order_id],
)
return {"jira_ticket_id": issue.key, "summary": summary}
```

**Slack** (`tools.py::notify_slack`):

```python
from slack_sdk import WebClient
client = WebClient(token=SLACK_BOT_TOKEN)
client.chat_postMessage(channel=channel, text=message)
```

**Order data** (`tools.py::fetch_order_data`):

```python
import requests
resp = requests.get(f"{ORDERS_API_BASE_URL}/orders/{order_id}",
                     headers={"Authorization": f"Bearer {ORDERS_API_TOKEN}"})
resp.raise_for_status()
return resp.json()
```

## Human-in-the-loop resume

The graph is compiled with `interrupt_before=["human_escalation"]`, so it pauses right
before that node whenever a ticket needs human review. `agent.py` resumes automatically
for the demo, but in a real deployment a human agent's approval action would trigger the
resume instead:

```python
app = build_graph()
config = {"configurable": {"thread_id": thread_id}}

app.invoke(initial_state, config=config)

# ... a human reviews the paused state, optionally edits it ...
app.update_state(config, {"customer_reply": "<edited reply>"})

# resume execution from where it paused
app.invoke(None, config=config)
```

`app.get_state(config).next` tells you whether the graph is paused and which node it's
about to run, so a UI can poll this to know when a ticket needs attention.

## AgentGuard / Langfuse observability

Every LLM call passes a `CallbackHandler` from `langfuse.callback` in its `callbacks`
config, so each classification and response generation shows up in the AgentGuard/Langfuse
UI as a traced generation with prompt, completion, token usage, latency, and cost — grouped
by `thread_id` so you can see the full multi-ticket session for a single run.
