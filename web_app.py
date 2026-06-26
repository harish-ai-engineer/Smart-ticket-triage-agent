"""Web UI for submitting customer support tickets to the triage agent."""

import json
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from agent import run_agent


def _ticket_id() -> str:
    return f"WEB-{datetime.now().strftime('%Y%m%d%H%M%S')}"


def _html() -> str:
    return """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Ticket Triage Agent</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --text: #1f2933;
      --muted: #637083;
      --line: #d9dee7;
      --brand: #1769e0;
      --brand-dark: #0f55b8;
      --ok: #0f7b4f;
      --warn: #9a5a00;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
    }
    .shell {
      max-width: 1120px;
      margin: 0 auto;
      padding: 32px 20px;
    }
    header {
      display: flex;
      justify-content: space-between;
      gap: 20px;
      align-items: flex-end;
      margin-bottom: 24px;
    }
    h1 {
      margin: 0 0 6px;
      font-size: 28px;
      line-height: 1.2;
      letter-spacing: 0;
    }
    .subtitle {
      margin: 0;
      color: var(--muted);
      font-size: 14px;
    }
    .status {
      border: 1px solid var(--line);
      background: var(--panel);
      padding: 10px 12px;
      min-width: 220px;
      font-size: 13px;
    }
    .grid {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(320px, 420px);
      gap: 20px;
      align-items: start;
    }
    form, .result {
      background: var(--panel);
      border: 1px solid var(--line);
      padding: 18px;
      border-radius: 6px;
    }
    label {
      display: block;
      font-size: 13px;
      font-weight: 650;
      margin: 0 0 6px;
    }
    input, textarea {
      width: 100%;
      border: 1px solid #c9d1dc;
      border-radius: 4px;
      padding: 10px 11px;
      font: inherit;
      font-size: 15px;
      background: #fff;
      color: var(--text);
    }
    textarea {
      min-height: 190px;
      resize: vertical;
    }
    .field {
      margin-bottom: 14px;
    }
    .actions {
      display: flex;
      justify-content: flex-end;
      gap: 10px;
      padding-top: 4px;
    }
    button {
      border: 0;
      border-radius: 4px;
      background: var(--brand);
      color: #fff;
      font-weight: 700;
      padding: 10px 16px;
      cursor: pointer;
      min-height: 40px;
    }
    button:hover { background: var(--brand-dark); }
    button:disabled {
      opacity: .55;
      cursor: not-allowed;
    }
    .result h2 {
      margin: 0 0 14px;
      font-size: 18px;
      letter-spacing: 0;
    }
    .empty {
      color: var(--muted);
      font-size: 14px;
      line-height: 1.5;
      margin: 0;
    }
    .kv {
      display: grid;
      grid-template-columns: 116px minmax(0, 1fr);
      gap: 8px 10px;
      font-size: 14px;
      padding: 12px 0;
      border-top: 1px solid var(--line);
    }
    .kv:first-of-type { border-top: 0; padding-top: 0; }
    .k { color: var(--muted); }
    .badge {
      display: inline-block;
      border-radius: 999px;
      padding: 2px 8px;
      font-size: 12px;
      font-weight: 750;
      background: #eef4ff;
      color: #174f9c;
    }
    .badge.warn {
      background: #fff4db;
      color: var(--warn);
    }
    .reply {
      white-space: pre-wrap;
      line-height: 1.45;
    }
    .error {
      color: #b42318;
      background: #fff1f0;
      border: 1px solid #ffd0cc;
      padding: 10px;
      border-radius: 4px;
      font-size: 14px;
      margin-top: 12px;
    }
    @media (max-width: 820px) {
      header { display: block; }
      .status { margin-top: 14px; }
      .grid { grid-template-columns: 1fr; }
      .shell { padding: 22px 14px; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <header>
      <div>
        <h1>Ticket Triage Agent</h1>
        <p class="subtitle">Submit a customer message and route it through classification, ticketing, Slack, and escalation.</p>
      </div>
      <div class="status" id="status">Ready</div>
    </header>
    <div class="grid">
      <form id="ticketForm">
        <div class="field">
          <label for="customerName">Customer name</label>
          <input id="customerName" name="customerName" value="Nisha Rao" required />
        </div>
        <div class="field">
          <label for="subject">Subject</label>
          <input id="subject" name="subject" value="Missing item in my order" required />
        </div>
        <div class="field">
          <label for="message">Message</label>
          <textarea id="message" name="message" required>Hi, I received my package today but one item is missing from the box. Order is ORD-84712. Please help urgently, this was a gift.</textarea>
        </div>
        <div class="actions">
          <button id="submitBtn" type="submit">Submit Ticket</button>
        </div>
      </form>
      <section class="result">
        <h2>Result</h2>
        <div id="result"><p class="empty">No ticket submitted yet.</p></div>
      </section>
    </div>
  </main>
  <script>
    const form = document.getElementById("ticketForm");
    const statusBox = document.getElementById("status");
    const resultBox = document.getElementById("result");
    const submitBtn = document.getElementById("submitBtn");

    function escapeHtml(value) {
      return String(value ?? "").replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
      })[char]);
    }

    function renderResult(data) {
      const item = data.processed?.[0] || {};
      const isEscalated = item.next_action === "escalate";
      resultBox.innerHTML = `
        <div class="kv"><div class="k">Ticket</div><div>${escapeHtml(item.ticket_id || data.ticket_id)}</div></div>
        <div class="kv"><div class="k">Case ID</div><div>${escapeHtml(item.jira_ticket_id || "Pending")}</div></div>
        <div class="kv"><div class="k">Intent</div><div><span class="badge">${escapeHtml(item.intent || "unknown")}</span></div></div>
        <div class="kv"><div class="k">Priority</div><div><span class="badge ${isEscalated ? "warn" : ""}">${escapeHtml(item.priority || "unknown")}</span></div></div>
        <div class="kv"><div class="k">Action</div><div>${escapeHtml(item.next_action || "done")}</div></div>
        <div class="kv"><div class="k">Reply</div><div class="reply">${escapeHtml(item.reply || "")}</div></div>
      `;
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      submitBtn.disabled = true;
      statusBox.textContent = "Processing ticket...";
      resultBox.innerHTML = '<p class="empty">Running triage graph.</p>';

      const payload = {
        customer_name: form.customerName.value.trim(),
        subject: form.subject.value.trim(),
        message: form.message.value.trim()
      };

      try {
        const response = await fetch("/api/tickets", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || "Ticket processing failed.");
        }
        statusBox.textContent = "Ticket processed";
        renderResult(data);
      } catch (error) {
        statusBox.textContent = "Error";
        resultBox.innerHTML = `<div class="error">${escapeHtml(error.message)}</div>`;
      } finally {
        submitBtn.disabled = false;
      }
    });
  </script>
</body>
</html>
"""


def _process_ticket(payload: dict) -> dict:
    ticket = {
        "ticket_id": _ticket_id(),
        "customer_name": str(payload.get("customer_name", "")).strip() or "Customer",
        "subject": str(payload.get("subject", "")).strip() or "Support request",
        "message": str(payload.get("message", "")).strip(),
    }
    if not ticket["message"]:
        raise ValueError("Message is required.")

    processed = run_agent([ticket])
    return {"ticket_id": ticket["ticket_id"], "processed": processed}


class TicketHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path != "/":
            self.send_error(404)
            return
        body = _html().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if self.path != "/api/tickets":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            self._send_json(_process_ticket(payload))
        except ValueError as exc:
            self._send_json({"detail": str(exc)}, status=400)
        except Exception as exc:
            self._send_json({"detail": str(exc)}, status=500)

    def log_message(self, format: str, *args) -> None:
        print(f"[Web] {self.address_string()} - {format % args}")


def main() -> None:
    port = int(os.getenv("PORT", "8000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), TicketHandler)
    print(f"[Web] Ticket Triage Agent running on http://0.0.0.0:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
