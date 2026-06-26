# Ticket Triage Agent

A LangGraph support triage demo that classifies customer tickets, looks up mock order
data, creates a Jira ticket or local fallback ticket, sends Slack notifications, drafts a
customer reply, and escalates high-value refund or damage cases for human review.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env` with `OPENAI_API_KEY`, Langfuse/AgentGuard keys, and optional Jira/Slack
settings. Slack is currently used for real notifications. Jira failures are traced as
errors and then fall back to local ticket IDs.

## Run CLI Demo

```bash
python agent.py
```

This runs the graph over the sample tickets in `mock_data.py`.

## Run Web UI

```bash
python web_app.py
```

Open `http://localhost:8000`, submit a customer ticket, and the app will run the same
LangGraph triage flow.

## Azure App Service

Use this startup command:

```bash
python web_app.py
```

Set the same environment variables from `.env` in Azure App Service application settings.

## Flow

```text
ticket -> llm_classifier -> tools_node -> llm_responder -> loop/done/escalate
```

`tools_node` looks up order data, tries Jira ticket creation, falls back locally when Jira
auth fails, and sends Slack notifications. Langfuse traces use the name:

```text
ticket triage agent
```
