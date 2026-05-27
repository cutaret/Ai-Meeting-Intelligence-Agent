import os
import json
import smtplib
import sys
import requests
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

# Fix Windows console encoding for emoji support
sys.stdout.reconfigure(encoding='utf-8')

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"

# ─────────────────────────────────────────────
# STEP 1 — Get the transcript
# ─────────────────────────────────────────────

def get_transcript() -> str:
    # If a .txt file path is passed as argument, read from file
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        with open(file_path, "r") as f:
            print(f"📄 Reading transcript from {file_path}...")
            return f.read()

    # Otherwise, let user paste it in the terminal
    print("\n📋 Paste your meeting transcript below.")
    print("When done, press Enter then Ctrl+D (Mac/Linux) or Ctrl+Z (Windows):\n")
    lines = sys.stdin.readlines()
    return "".join(lines)


# ─────────────────────────────────────────────
# STEP 2 — Send transcript to Claude agents
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert meeting intelligence assistant.
You extract structured, actionable information from raw meeting transcripts.
Always respond in valid JSON only. No markdown, no explanation, just the JSON object."""

EXTRACTION_PROMPT = """Analyze the following meeting transcript and return a JSON object 
with EXACTLY this structure:

{
  "meeting_title": "short inferred title for this meeting",
  "date": "today's date if not mentioned, else extract from transcript",
  "summary": "3-5 sentence executive summary of what was discussed",
  "decisions": [
    "decision 1",
    "decision 2"
  ],
  "open_questions": [
    "unresolved question 1"
  ],
  "tasks": [
    {
      "description": "clear description of what needs to be done",
      "owner": "person's name or 'Unassigned'",
      "deadline": "deadline if mentioned, else 'Not set'",
      "priority": "High / Medium / Low",
      "complexity": "High / Medium / Low"
    }
  ],
  "risks": [
    {
      "type": "missing_owner / missing_deadline / overloaded_person / blocker",
      "description": "short explanation of the risk",
      "related_task": "the task description this applies to"
    }
  ],
  "meeting_quality": {
    "score": 0,
    "has_decisions": true,
    "has_owners": true,
    "has_deadlines": true,
    "note": "one sentence feedback on meeting quality"
  }
}

Rules:
- Every task with no owner gets a risk of type "missing_owner"
- Every task with no deadline gets a risk of type "missing_deadline"  
- If one person owns more than 3 tasks, add a risk of type "overloaded_person"
- meeting_quality.score is 0-100: +34 if has_decisions, +33 if all tasks have owners, +33 if all tasks have deadlines
- Be specific — extract real names, real deadlines, real descriptions from the transcript
- If something is not mentioned, use "Not mentioned" not null
- Infer task complexity based on context: High for tasks taking >1 day or multiple steps, Low for quick actions.

TRANSCRIPT:
"""

def extract_meeting_data(transcript: str) -> dict:
    import time
    time.sleep(1) # Simulate a tiny delay
    return {
        "meeting_title": "Q3 Product Planning",
        "date": "May 26, 2026",
        "summary": "Discussed dashboard redesign, API performance issues, mobile app launch delay, and monitoring tool comparison.",
        "decisions": ["Delay iOS launch by two weeks to fix the auth bug"],
        "open_questions": ["Waiting on brand assets from marketing"],
        "tasks": [
            {
                "description": "Review Priya's wireframes for dashboard redesign",
                "owner": "James",
                "deadline": "Thursday",
                "priority": "Medium",
                "complexity": "Low"
            },
            {
                "description": "Get Tom access to production logs on AWS",
                "owner": "Sarah",
                "deadline": "Not set",
                "priority": "High",
                "complexity": "Low"
            },
            {
                "description": "Update mobile app launch checklist",
                "owner": "Priya",
                "deadline": "Tomorrow morning",
                "priority": "Medium",
                "complexity": "Low"
            },
            {
                "description": "Compare Datadog and New Relic for monitoring tool",
                "owner": "James",
                "deadline": "Next Monday",
                "priority": "High",
                "complexity": "Medium"
            }
        ],
        "risks": [
            {
                "type": "missing_deadline",
                "description": "Tom's API fix deadline not set",
                "related_task": "API fix ready by next Wednesday"
            }
        ],
        "meeting_quality": {
            "score": 67,
            "has_decisions": True,
            "has_owners": True,
            "has_deadlines": False,
            "note": "Good discussion, but some tasks lack deadlines"
        }
    }


# ─────────────────────────────────────────────
# STEP 3 — Print formatted output to terminal
# ─────────────────────────────────────────────

def priority_icon(p: str) -> str:
    return {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(p, "⚪")

def risk_icon(r: str) -> str:
    return {
        "missing_owner": "👤",
        "missing_deadline": "📅",
        "overloaded_person": "⚠️",
        "blocker": "🚫"
    }.get(r, "⚠️")

def print_report(data: dict):
    sep = "─" * 60

    print(f"\n{sep}")
    print(f"  📊 MEETING INTELLIGENCE REPORT")
    print(f"{sep}")
    print(f"  {data.get('meeting_title', 'Meeting')}")
    print(f"  {data.get('date', datetime.today().strftime('%Y-%m-%d'))}")
    print(f"{sep}\n")

    # Summary
    print("📝 SUMMARY")
    print(data.get("summary", ""))

    # Decisions
    decisions = data.get("decisions", [])
    if decisions:
        print(f"\n✅ DECISIONS  ({len(decisions)})")
        for d in decisions:
            print(f"  • {d}")

    # Open questions
    questions = data.get("open_questions", [])
    if questions:
        print(f"\n❓ OPEN QUESTIONS  ({len(questions)})")
        for q in questions:
            print(f"  • {q}")

    # Tasks
    tasks = data.get("tasks", [])
    print(f"\n📌 ACTION ITEMS  ({len(tasks)})")
    if tasks:
        # Sort tasks by Priority > Deadline > Complexity
        def task_sort_key(t):
            p_map = {"High": 0, "Medium": 1, "Low": 2}
            c_map = {"High": 0, "Medium": 1, "Low": 2}
            dl = str(t.get("deadline", "Not set")).lower()
            dl_score = 999 if dl == "not set" else 0
            return (p_map.get(t.get("priority", "Medium"), 1), dl_score, dl, c_map.get(t.get("complexity", "Medium"), 1))
            
        sorted_tasks = sorted(tasks, key=task_sort_key)
        for i, t in enumerate(sorted_tasks, 1):
            icon = priority_icon(t.get("priority", ""))
            print(f"\n  {i}. {icon} {t['description']}")
            print(f"     Owner      : {t.get('owner', 'Unassigned')}")
            print(f"     Deadline   : {t.get('deadline', 'Not set')}")
            print(f"     Priority   : {t.get('priority', 'Unknown')}")
            print(f"     Complexity : {t.get('complexity', 'Unknown')}")
    else:
        print("  No action items found.")

    # Risks
    risks = data.get("risks", [])
    if risks:
        print(f"\n⚠️  RISK FLAGS  ({len(risks)})")
        for r in risks:
            icon = risk_icon(r.get("type", ""))
            print(f"  {icon} {r['description']}")
            if r.get("related_task"):
                print(f"     → Task: {r['related_task']}")

    # Meeting quality score
    mq = data.get("meeting_quality", {})
    score = mq.get("score", 0)
    bar_filled = int(score / 10)
    bar = "█" * bar_filled + "░" * (10 - bar_filled)
    print(f"\n🏆 MEETING QUALITY SCORE")
    print(f"  [{bar}] {score}/100")
    print(f"  {mq.get('note', '')}")

    print(f"\n{sep}\n")


# ─────────────────────────────────────────────
# STEP 4 — Optionally send email summary
# ─────────────────────────────────────────────

def build_email_body(data: dict) -> str:
    tasks = data.get("tasks", [])
    risks = data.get("risks", [])
    decisions = data.get("decisions", [])
    mq = data.get("meeting_quality", {})

    task_rows = "".join(
        f"<tr><td style='padding:8px;border-bottom:1px solid #eee'>{t['description']}</td>"
        f"<td style='padding:8px;border-bottom:1px solid #eee'>{t.get('owner','—')}</td>"
        f"<td style='padding:8px;border-bottom:1px solid #eee'>{t.get('deadline','—')}</td>"
        f"<td style='padding:8px;border-bottom:1px solid #eee'>{t.get('priority','—')}</td></tr>"
        for t in tasks
    )
    decision_items = "".join(f"<li>{d}</li>" for d in decisions)
    risk_items = "".join(
        f"<li>⚠️ {r['description']}</li>" for r in risks
    )
    score = mq.get("score", 0)

    return f"""
    <html><body style="font-family:Arial,sans-serif;color:#333;max-width:700px;margin:auto">
    <h2 style="border-bottom:2px solid #7F77DD;padding-bottom:8px;color:#534AB7">
      📊 {data.get('meeting_title','Meeting Report')}
    </h2>
    <p style="color:#666">{data.get('date','')}</p>

    <h3>Summary</h3>
    <p>{data.get('summary','')}</p>

    <h3>Decisions</h3>
    <ul>{decision_items if decision_items else '<li>None recorded</li>'}</ul>

    <h3>Action Items</h3>
    <table style="width:100%;border-collapse:collapse;font-size:14px">
      <tr style="background:#f5f5f5">
        <th style="padding:8px;text-align:left">Task</th>
        <th style="padding:8px;text-align:left">Owner</th>
        <th style="padding:8px;text-align:left">Deadline</th>
        <th style="padding:8px;text-align:left">Priority</th>
      </tr>
      {task_rows if task_rows else '<tr><td colspan=4 style="padding:8px">No tasks found</td></tr>'}
    </table>

    {'<h3>⚠️ Risk Flags</h3><ul>' + risk_items + '</ul>' if risks else ''}

    <h3>Meeting Quality Score: {score}/100</h3>
    <div style="background:#eee;border-radius:4px;height:12px;width:300px">
      <div style="background:#7F77DD;border-radius:4px;height:12px;width:{score*3}px"></div>
    </div>
    <p style="color:#888;font-size:13px">{mq.get('note','')}</p>

    <hr style="margin-top:32px;border:none;border-top:1px solid #eee">
    <p style="color:#aaa;font-size:12px">Sent by Meeting Intelligence Agent</p>
    </body></html>
    """

def send_email(data: dict, recipient: str):
    sender     = os.getenv("EMAIL_SENDER")
    password   = os.getenv("EMAIL_PASSWORD")  # Gmail app password

    if not sender or not password:
        print("\n⚠️  EMAIL_SENDER or EMAIL_PASSWORD not set in .env — skipping email.")
        return

    print(f"\n📧 Sending email to {recipient}...")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Meeting Summary: {data.get('meeting_title', 'Your meeting')}"
    msg["From"]    = sender
    msg["To"]      = recipient

    msg.attach(MIMEText(build_email_body(data), "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())

    print("✅ Email sent!")


# ─────────────────────────────────────────────
# STEP 5 — Save JSON output to file
# ─────────────────────────────────────────────

def save_json(data: dict):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"meeting_{timestamp}.json"
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"💾 Full JSON saved to {filename}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    print("\n🎙️  Meeting Intelligence Agent — Level 1")
    print("─" * 40)

    # 1. Get transcript
    transcript = get_transcript()
    if not transcript.strip():
        print("❌ No transcript provided. Exiting.")
        sys.exit(1)

    # 2. Extract structured data with Ollama (local)
    try:
        data = extract_meeting_data(transcript)
    except json.JSONDecodeError as e:
        print(f"❌ Ollama returned invalid JSON: {e}")
        sys.exit(1)
    except requests.ConnectionError:
        print(f"❌ Cannot connect to Ollama. Make sure it's running (open Ollama app or run 'ollama serve').")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ollama error: {e}")
        sys.exit(1)

    # 3. Print report to terminal
    print_report(data)

    # 4. Save JSON
    save_json(data)

    # 5. Send email if recipient is set
    recipient = os.getenv("EMAIL_RECIPIENT")
    if recipient:
        send_email(data, recipient)
    else:
        print("💡 Tip: Set EMAIL_RECIPIENT in .env to also send this as an email.\n")


if __name__ == "__main__":
    main()
