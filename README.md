# Ticket Triage Agent

A LangGraph agent that processes a queue of e-commerce support tickets, classifying each
one's intent and priority, looking up the related order, filing a GitHub issue, alerting
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
(`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`). Set `GITHUB_TOKEN`
and `GITHUB_REPOSITORY` when you want the agent to create real GitHub issues. Slack
keys are only required when you want real Slack alerts.

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
- **tools_node** — looks up the order, files a GitHub issue, and notifies Slack.
- **llm_responder** (LLM call #2) — drafts a customer reply and decides `next_action`.
- **human_escalation** — pauses (`interrupt_before`) for refund/damaged tickets over
  ₹15,000 before closing.

## GitHub Issues

`tools.py::create_support_issue` creates a GitHub issue when these variables are set:

```env
GITHUB_TOKEN=github_pat_or_personal_access_token
GITHUB_REPOSITORY=owner/repo
GITHUB_API_BASE=https://api.github.com
```

Use a fine-grained GitHub token with Issues read/write access for the target repository.

## Swapping mock tools for real APIs

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

The graph passes one `CallbackHandler` from `langfuse.callback`, with trace name
`ticket triage agent`, so a run is grouped into one AgentGuard/Langfuse trace.
