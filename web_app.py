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
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%230f766e'/%3E%3Cpath d='M18 18h28v6H18zM18 30h28v6H18zM18 42h18v6H18z' fill='white'/%3E%3Ccircle cx='47' cy='45' r='7' fill='%23f59e0b'/%3E%3C/svg%3E" />
  <style>
    :root {
      color-scheme: light;
      --bg: #f5f7fb;
      --panel: #ffffff;
      --text: #111827;
      --muted: #667085;
      --line: #d7deea;
      --soft-line: #edf1f7;
      --brand: #0a84ff;
      --brand-dark: #0067d8;
      --accent: #2563eb;
      --ok: #0f7b4f;
      --warn: #9a5a00;
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      overflow: hidden;
      background: var(--bg);
      color: var(--text);
    }
    body::before {
      content: "";
      position: fixed;
      inset: 0 0 auto;
      height: 280px;
      background:
        radial-gradient(circle at 16% 0%, rgba(10, 132, 255, .20), transparent 34%),
        linear-gradient(180deg, #ffffff 0%, #f4f8ff 100%);
      border-bottom: 1px solid #e6edf7;
      z-index: -1;
    }
    .shell {
      max-width: 1180px;
      margin: 0 auto;
      height: 100vh;
      padding: 14px 20px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    header {
      display: flex;
      justify-content: space-between;
      gap: 20px;
      align-items: center;
      color: var(--text);
      flex: 0 0 auto;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 0;
    }
    .brand-mark {
      display: grid;
      place-items: center;
      width: 48px;
      height: 48px;
      border-radius: 14px;
      background: #0f766e;
      border: 1px solid rgba(15, 118, 110, .18);
      box-shadow: 0 16px 34px rgba(15, 118, 110, .20);
    }
    .brand-mark svg {
      width: 28px;
      height: 28px;
      display: block;
    }
    h1 {
      margin: 0 0 3px;
      font-size: 28px;
      line-height: 1.2;
      letter-spacing: 0;
      font-weight: 760;
    }
    .subtitle {
      margin: 0;
      color: var(--muted);
      font-size: 13px;
      font-weight: 400;
      line-height: 1.45;
    }
    .status {
      border: 1px solid rgba(10, 132, 255, .18);
      background: rgba(255, 255, 255, .78);
      color: #0758b8;
      border-radius: 999px;
      padding: 11px 14px;
      min-width: 220px;
      font-size: 13px;
      font-weight: 650;
      text-align: center;
      box-shadow: 0 18px 36px rgba(15, 23, 42, .07);
      backdrop-filter: blur(16px);
    }
    .summary {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
      flex: 0 0 auto;
    }
    .metric {
      background: rgba(255, 255, 255, .82);
      border: 1px solid rgba(215, 222, 234, .8);
      border-radius: 13px;
      padding: 9px 14px;
      box-shadow: 0 18px 40px rgba(15, 23, 42, .06);
      backdrop-filter: blur(18px);
    }
    .metric .label {
      color: var(--muted);
      font-size: 12px;
      font-weight: 680;
      text-transform: uppercase;
      letter-spacing: .04em;
    }
    .metric .value {
      margin-top: 5px;
      font-size: 16px;
      font-weight: 720;
    }
    .grid {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(340px, 430px);
      gap: 16px;
      align-items: stretch;
      min-height: 0;
      flex: 1 1 auto;
    }
    form, .result {
      background: var(--panel);
      border: 1px solid var(--line);
      padding: 16px;
      border-radius: 18px;
      box-shadow: 0 24px 60px rgba(15, 23, 42, .08);
      min-height: 0;
      height: 100%;
      display: flex;
      flex-direction: column;
    }
    .panel-title {
      margin: 0 0 14px;
      font-size: 18px;
      letter-spacing: 0;
      font-weight: 720;
    }
    label {
      display: block;
      font-size: 12px;
      font-weight: 620;
      margin: 0 0 5px;
    }
    input, textarea {
      width: 100%;
      border: 1px solid #c9d1dc;
      border-radius: 12px;
      padding: 8px 12px;
      font: inherit;
      font-size: 15px;
      font-weight: 400;
      background: #fbfcff;
      color: var(--text);
    }
    input:focus, textarea:focus {
      border-color: var(--brand);
      box-shadow: 0 0 0 4px rgba(10, 132, 255, .14);
      outline: 0;
    }
    textarea {
      min-height: 0;
      height: 100%;
      resize: none;
    }
    .field {
      margin-bottom: 8px;
    }
    .message-field {
      display: flex;
      flex: 1 1 auto;
      min-height: 0;
      flex-direction: column;
    }
    .message-field textarea {
      flex: 1 1 auto;
    }
    .actions {
      display: flex;
      justify-content: flex-end;
      gap: 10px;
      padding-top: 0;
      margin-top: 10px;
      flex: 0 0 auto;
    }
    button {
      border: 0;
      border-radius: 12px;
      background: var(--brand);
      color: #fff;
      font-weight: 650;
      padding: 9px 18px;
      cursor: pointer;
      min-height: 38px;
      box-shadow: 0 16px 26px rgba(10, 132, 255, .24);
    }
    button:hover { background: var(--brand-dark); }
    button:disabled {
      opacity: .55;
      cursor: not-allowed;
    }
    .result h2 {
      margin: 0;
      font-size: 18px;
      font-weight: 720;
      letter-spacing: 0;
    }
    .result-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 10px;
      flex: 0 0 auto;
    }
    .result-chip {
      border: 1px solid var(--soft-line);
      border-radius: 999px;
      padding: 4px 10px;
      color: #0758b8;
      font-size: 12px;
      font-weight: 650;
      background: #eef6ff;
    }
    .empty {
      color: var(--muted);
      font-size: 14px;
      line-height: 1.5;
      margin: 0;
    }
    #result {
      flex: 1 1 auto;
      min-height: 0;
      overflow: hidden;
    }
    .kv {
      display: grid;
      grid-template-columns: 116px minmax(0, 1fr);
      gap: 8px 10px;
      font-size: 14px;
      padding: 9px 0;
      border-top: 1px solid var(--soft-line);
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
      color: #334155;
      display: -webkit-box;
      -webkit-line-clamp: 5;
      -webkit-box-orient: vertical;
      overflow: hidden;
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
      body { overflow: auto; }
      .shell { height: auto; min-height: 100vh; }
      header { display: block; }
      .status { margin-top: 14px; }
      .summary { grid-template-columns: 1fr; }
      .grid { grid-template-columns: 1fr; }
      .shell { padding: 22px 14px; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <header>
      <div class="brand">
        <div class="brand-mark" aria-hidden="true">
          <svg viewBox="0 0 64 64" role="img">
            <path d="M18 18h28v6H18zM18 30h28v6H18zM18 42h18v6H18z" fill="#fff"/>
            <circle cx="47" cy="45" r="7" fill="#f59e0b"/>
          </svg>
        </div>
        <div>
          <h1>Ticket Triage Agent</h1>
          <p class="subtitle">Submit a customer message and route it through classification, ticketing, Slack, and escalation.</p>
        </div>
      </div>
      <div class="status" id="status">Ready</div>
    </header>
    <section class="summary" aria-label="Agent workflow">
      <div class="metric">
        <div class="label">Classify</div>
        <div class="value">Intent and priority</div>
      </div>
      <div class="metric">
        <div class="label">Create case</div>
        <div class="value">Jira or local fallback</div>
      </div>
      <div class="metric">
        <div class="label">Notify</div>
        <div class="value">Slack escalation</div>
      </div>
    </section>
    <div class="grid">
      <form id="ticketForm">
        <h2 class="panel-title">New Support Ticket</h2>
        <div class="field">
          <label for="customerName">Customer name</label>
          <input id="customerName" name="customerName" value="Nisha Rao" required />
        </div>
        <div class="field">
          <label for="subject">Subject</label>
          <input id="subject" name="subject" value="Missing item in my order" required />
        </div>
        <div class="field message-field">
          <label for="message">Message</label>
          <textarea id="message" name="message" required>Hi, I received my package today but one item is missing from the box. Order is ORD-84712. Please help urgently, this was a gift.</textarea>
        </div>
        <div class="actions">
          <button id="submitBtn" type="submit">Submit Ticket</button>
        </div>
      </form>
      <section class="result">
        <div class="result-head">
          <h2>Result</h2>
          <span class="result-chip">Live run</span>
        </div>
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
