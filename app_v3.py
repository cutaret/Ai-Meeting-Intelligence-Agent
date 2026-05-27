"""
app_v3.py — Meeting Intelligence Agent  |  Level 3
Multi-agent pipeline · Claude API · SQLite memory · Slack · Email
Run: streamlit run app_v3.py
"""

import streamlit as st
import json
import os
import smtplib
import requests
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

import agents
import database as db

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Meeting Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"]  { font-family: 'DM Sans', sans-serif; }
.stApp                       { background: #09090B; color: #E4E4E7; }
#MainMenu, footer, header    { visibility: hidden; }
.block-container             { padding: 1.5rem 2.5rem 4rem; max-width: 1200px; }

/* sidebar */
[data-testid="stSidebar"]    { background: #111113; border-right: 1px solid #1E1E22; }
[data-testid="stSidebar"] *  { color: #A1A1AA !important; }
[data-testid="stSidebar"] h3 { color: #E4E4E7 !important; font-size: 13px !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: .08em; }

/* textarea */
textarea, .stTextArea textarea {
    background: #111113 !important;
    border: 1px solid #27272A !important;
    border-radius: 10px !important;
    color: #E4E4E7 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 13px !important;
}
textarea:focus { border-color: #6366F1 !important; box-shadow: 0 0 0 3px rgba(99,102,241,.15) !important; }

/* buttons */
.stButton > button {
    background: #6366F1; color: white; border: none;
    border-radius: 8px; padding: .55rem 1.5rem;
    font-family: 'DM Sans', sans-serif; font-weight: 600; font-size: 13px;
    transition: all .2s; width: 100%;
}
.stButton > button:hover { background: #4F46E5; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(99,102,241,.3); }
.stButton > button:disabled { background: #27272A; color: #52525B; transform: none; box-shadow: none; }

/* tabs */
.stTabs [data-baseweb="tab-list"]  { background: transparent; border-bottom: 1px solid #1E1E22; gap: 0; }
.stTabs [data-baseweb="tab"]       { background: transparent; border: none; color: #71717A; font-size: 13px; font-weight: 500; padding: 10px 20px; border-bottom: 2px solid transparent; }
.stTabs [aria-selected="true"]     { color: #E4E4E7 !important; border-bottom-color: #6366F1 !important; }

/* cards */
.card {
    background: #111113; border: 1px solid #1E1E22;
    border-radius: 12px; padding: 18px 22px; margin-bottom: 10px;
}
.card-sm { background: #111113; border: 1px solid #1E1E22; border-radius: 10px; padding: 14px 18px; margin-bottom: 8px; }
.card-sm:hover { border-color: #2E2E38; }

/* metric */
.metric { background: #111113; border: 1px solid #1E1E22; border-radius: 12px; padding: 18px 20px; }
.metric .label { font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: .1em; color: #52525B; margin-bottom: 6px; }
.metric .val   { font-size: 32px; font-weight: 700; font-family: 'DM Mono', monospace; line-height: 1; }

/* chips */
.chip { display:inline-block; font-size:10px; font-weight:600; padding:2px 8px; border-radius:4px; font-family:'DM Mono',monospace; text-transform:uppercase; letter-spacing:.05em; }
.chip-red    { background:#3F1212; color:#F87171; }
.chip-yellow { background:#2D2200; color:#FCD34D; }
.chip-green  { background:#0D2112; color:#4ADE80; }
.chip-blue   { background:#0D1A3F; color:#60A5FA; }
.chip-purple { background:#1A0D3F; color:#A78BFA; }
.chip-gray   { background:#1C1C1E; color:#71717A; }

/* section head */
.sh { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .12em; color: #3F3F46; padding: 24px 0 10px; border-bottom: 1px solid #18181B; margin-bottom: 14px; }

/* risk row */
.risk-card { background:#1A1108; border:1px solid #2E1F0A; border-radius:10px; padding:12px 16px; margin-bottom:8px; }
.risk-label { font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:.08em; }

/* quality bar */
.qbar-bg   { background:#1C1C1E; border-radius:4px; height:6px; width:100%; margin:8px 0 4px; }
.qbar-fill { height:6px; border-radius:4px; transition:width .5s ease; }

/* agent badge */
.agent-badge { display:inline-flex; align-items:center; gap:5px; background:#0D1A3F; border:1px solid #1E2F5F; border-radius:6px; padding:4px 10px; font-size:11px; color:#60A5FA; font-family:'DM Mono',monospace; margin:2px; }
.agent-badge.done { background:#0D2112; border-color:#1A4A30; color:#4ADE80; }

/* status */
.status-ok  { background:#0D2112; border:1px solid #1A4A30; border-radius:8px; padding:10px 14px; color:#4ADE80; font-size:13px; }
.status-err { background:#1C0D0D; border:1px solid #4A1A1A; border-radius:8px; padding:10px 14px; color:#F87171; font-size:13px; }

/* speaker row */
.speaker-row { background:#111113; border:1px solid #1E1E22; border-radius:10px; padding:14px 18px; margin-bottom:8px; }
.sentiment-pill { display:inline-block; font-size:10px; font-weight:600; padding:3px 8px; border-radius:20px; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
PRIORITY_CHIP = {"High": "chip-red", "Medium": "chip-yellow", "Low": "chip-green"}
COMPLEXITY_CHIP = {"High": "chip-purple", "Medium": "chip-blue", "Low": "chip-gray"}
SEVERITY_CHIP = {"Critical": "chip-red", "High": "chip-red", "Medium": "chip-yellow", "Low": "chip-green"}
SENTIMENT_COLOR = {
    "Confident": "#4ADE80", "Positive": "#4ADE80",
    "Neutral": "#A1A1AA",
    "Uncertain": "#FCD34D", "Stressed": "#F87171",
}

RISK_LABELS = {
    "missing_owner":       "👤 Missing Owner",
    "missing_deadline":    "📅 Missing Deadline",
    "overloaded_person":   "⚠️  Overloaded",
    "blocker":             "🚫 Blocker",
    "dependency_conflict": "🔗 Dependency Conflict",
    "scope_creep":         "📐 Scope Creep",
}

def priority_icon(p):
    return {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(p, "⚪")

def chip(text, style="chip-gray"):
    return f"<span class='chip {style}'>{text}</span>"


# ─────────────────────────────────────────────────────────────────────────────
# INTEGRATIONS
# ─────────────────────────────────────────────────────────────────────────────
def send_slack(data: dict, webhook_url: str) -> bool:
    tasks = data.get("tasks", [])
    risks = data.get("risks", [])
    score = data.get("meeting_quality", {}).get("score", 0)
    task_lines = "\n".join(
        f"• *{t['description']}* — {t.get('owner','?')} | {t.get('deadline','No deadline')} | {t.get('priority','?')}"
        for t in tasks[:8]
    )
    risk_lines = "\n".join(f"⚠️ {r['description']}" for r in risks[:4])
    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": f"📊 {data.get('meeting_title','Meeting Summary')}"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Summary*\n{data.get('summary','')}"}},
        {"type": "divider"},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Action Items ({len(tasks)})*\n{task_lines or 'None found'}"}},
    ]
    if risk_lines:
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*Risk Flags*\n{risk_lines}"}})
    blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": f"Quality: *{score}/100* · Meeting Intelligence Agent v3"}]})
    resp = requests.post(webhook_url, json={"blocks": blocks}, timeout=10)
    return resp.status_code == 200


def send_email_html(data: dict, sender: str, password: str, recipient: str):
    tasks = data.get("tasks", [])
    score = data.get("meeting_quality", {}).get("score", 0)
    decisions = data.get("decisions", [])
    risks = data.get("risks", [])

    task_rows = "".join(
        f"<tr><td style='padding:8px;border-bottom:1px solid #1E1E24'>{t['description']}</td>"
        f"<td style='padding:8px;border-bottom:1px solid #1E1E24;color:#A1A1AA'>{t.get('owner','—')}</td>"
        f"<td style='padding:8px;border-bottom:1px solid #1E1E24;color:#A1A1AA'>{t.get('deadline','—')}</td>"
        f"<td style='padding:8px;border-bottom:1px solid #1E1E24;color:#A1A1AA'>{t.get('priority','—')}</td></tr>"
        for t in tasks
    )
    decision_html = "".join(f"<li style='margin-bottom:4px'>{d}</li>" for d in decisions) or "<li>None recorded</li>"
    risk_html = "".join(f"<li style='color:#F97316;margin-bottom:4px'>⚠️ {r['description']}</li>" for r in risks) if risks else ""

    body = f"""<html><body style="background:#09090B;color:#E4E4E7;font-family:sans-serif;padding:32px;max-width:700px;margin:auto">
    <div style="border-bottom:1px solid #27272A;padding-bottom:16px;margin-bottom:24px">
      <h2 style="color:#A78BFA;margin:0 0 4px">{data.get('meeting_title','Meeting Summary')}</h2>
      <p style="color:#71717A;font-size:13px;margin:0">{data.get('date','')} · Quality Score: {score}/100</p>
    </div>
    <h3 style="font-size:12px;text-transform:uppercase;letter-spacing:.1em;color:#52525B;margin:0 0 10px">Summary</h3>
    <p style="color:#A1A1AA;font-size:14px;line-height:1.6">{data.get('summary','')}</p>
    <h3 style="font-size:12px;text-transform:uppercase;letter-spacing:.1em;color:#52525B;margin:24px 0 10px">Decisions</h3>
    <ul style="color:#E4E4E7;font-size:13px;padding-left:20px">{decision_html}</ul>
    <h3 style="font-size:12px;text-transform:uppercase;letter-spacing:.1em;color:#52525B;margin:24px 0 10px">Action Items</h3>
    <table style="width:100%;border-collapse:collapse;font-size:13px">
      <tr style="background:#18181B"><th style="padding:8px;text-align:left;color:#71717A;font-weight:500">Task</th><th style="padding:8px;text-align:left;color:#71717A;font-weight:500">Owner</th><th style="padding:8px;text-align:left;color:#71717A;font-weight:500">Deadline</th><th style="padding:8px;text-align:left;color:#71717A;font-weight:500">Priority</th></tr>
      {task_rows or '<tr><td colspan=4 style="padding:8px;color:#52525B">No tasks found</td></tr>'}
    </table>
    {'<h3 style="font-size:12px;text-transform:uppercase;letter-spacing:.1em;color:#52525B;margin:24px 0 10px">Risk Flags</h3><ul style="font-size:13px;padding-left:20px">' + risk_html + '</ul>' if risks else ''}
    <hr style="border:none;border-top:1px solid #18181B;margin:32px 0 16px">
    <p style="color:#3F3F46;font-size:11px">Sent by Meeting Intelligence Agent v3 · Powered by Claude</p>
    </body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📊 Meeting Summary: {data.get('meeting_title', 'Your meeting')}"
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(body, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(sender, password)
        s.sendmail(sender, recipient, msg.as_string())


def export_jira_csv(tasks: list) -> str:
    """Export tasks in Jira-importable CSV format."""
    lines = ["Summary,Issue Type,Priority,Assignee,Due Date,Description"]
    for t in tasks:
        summary = t.get("description", "").replace(",", ";")
        priority = t.get("priority", "Medium")
        assignee = t.get("owner", "Unassigned")
        due = t.get("deadline", "")
        category = t.get("category", "Task")
        lines.append(f'"{summary}","Task","{priority}","{assignee}","{due}","From meeting: {category}"')
    return "\n".join(lines)


def export_notion_md(data: dict) -> str:
    """Export as Notion-pasteable Markdown."""
    lines = [
        f"# {data.get('meeting_title', 'Meeting Notes')}",
        f"**Date:** {data.get('date', '')}  ",
        f"**Attendees:** {', '.join(data.get('attendees', []))}",
        "",
        "## Summary",
        data.get("summary", ""),
        "",
        "## Decisions",
    ]
    for d in data.get("decisions", []):
        lines.append(f"- ✅ {d}")
    lines += ["", "## Action Items", "| Task | Owner | Deadline | Priority |", "|------|-------|----------|----------|"]
    for t in data.get("tasks", []):
        lines.append(f"| {t.get('description','')} | {t.get('owner','—')} | {t.get('deadline','—')} | {t.get('priority','—')} |")
    if data.get("risks"):
        lines += ["", "## ⚠️ Risk Flags"]
        for r in data["risks"]:
            lines.append(f"- **{r.get('type','').replace('_',' ').title()}**: {r.get('description','')}")
    lines += ["", "---", "_Generated by Meeting Intelligence Agent v3_"]
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### API Keys")
    groq_key = st.text_input(
        "Groq API Key",
        value=os.getenv("GROQ_API_KEY", ""),
        type="password",
        placeholder="gsk_...",
        help="Get your free key at console.groq.com"
    )
    if groq_key:
        os.environ["GROQ_API_KEY"] = groq_key

    st.markdown("---")
    st.markdown("### Pipeline Options")
    run_sentiment = st.toggle("Sentiment Analysis", value=True, help="Adds ~5s but gives speaker insights")
    run_followup = st.toggle("Follow-up Messages", value=True, help="Auto-generate Slack/email nudges")

    st.markdown("---")
    st.markdown("### Integrations")
    slack_webhook = st.text_input("Slack Webhook URL", value=os.getenv("SLACK_WEBHOOK_URL", ""), placeholder="https://hooks.slack.com/...")
    st.markdown("**Email (Gmail)**")
    email_sender = st.text_input("Sender", value=os.getenv("EMAIL_SENDER", ""), placeholder="you@gmail.com")
    email_password = st.text_input("App Password", value=os.getenv("EMAIL_PASSWORD", ""), type="password")
    email_recipient = st.text_input("Recipient", value=os.getenv("EMAIL_RECIPIENT", ""), placeholder="team@company.com")

    st.markdown("---")
    st.markdown("<p style='font-size:11px;color:#3F3F46'>Meeting Intelligence Agent v3<br>Multi-agent · Claude API · SQLite</p>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:20px 0 28px">
  <div style="font-size:10px;font-weight:700;letter-spacing:.18em;color:#6366F1;text-transform:uppercase;margin-bottom:8px">
    AI · Multi-Agent · Claude-powered
  </div>
  <h1 style="font-size:28px;font-weight:700;color:#F4F4F5;margin:0 0 6px;letter-spacing:-.5px">
    Meeting Intelligence
  </h1>
  <p style="color:#52525B;font-size:13px;margin:0">
    Paste a transcript → 5 agents extract tasks, risks, sentiment & follow-ups → send to Slack or email
  </p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
tab_analyze, tab_history, tab_tracker = st.tabs(["🧠 Analyze", "📚 History", "📋 Task Tracker"])


# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 — ANALYZE
# ═════════════════════════════════════════════════════════════════════════════
with tab_analyze:

    # INPUT AREA
    col_input, col_btn = st.columns([4, 1])
    with col_btn:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("📋 Load Sample"):
            try:
                with open("sample_transcript.txt") as f:
                    st.session_state["transcript"] = f.read()
            except FileNotFoundError:
                st.session_state["transcript"] = """Meeting: Q3 Planning\nDate: May 26, 2026\nAttendees: Sarah (PM), James (Engineering), Priya (Design)\n\nSarah: Let's start. James, can you handle the API fix by Wednesday?\nJames: Yes, I'll get it done. But I need access to production logs first — that's blocking me.\nSarah: I'll get you that access today. Priya, the wireframes?\nPriya: Done. I need James to review them by Thursday.\nJames: Sure, I'll review by Thursday EOD.\nSarah: We've decided to delay the iOS launch by two weeks to fix the auth bug. New date is June 15th. Priya, update the launch checklist by tomorrow.\nPriya: Will do.\nSarah: Tom, any updates on the user service refactor?\nTom: Too much on my plate this sprint. Can we push it?\nSarah: Yes, next sprint. Any other blockers?\nPriya: Still waiting on brand assets from marketing."""

    transcript = st.text_area(
        "Transcript",
        value=st.session_state.get("transcript", ""),
        height=220,
        placeholder="Paste your meeting transcript here...\n\nTip: Include speaker names (e.g. 'Sarah: Let's discuss...') for accurate owner detection.",
        label_visibility="collapsed",
    )

    # ANALYZE BUTTON
    _, btn_col, _ = st.columns([1, 2, 1])
    with btn_col:
        api_ready = bool(os.getenv("GROQ_API_KEY"))
        run = st.button(
            "🧠 Run Multi-Agent Analysis",
            disabled=not transcript or not api_ready,
        )
        if not api_ready:
            st.markdown("<p style='text-align:center;font-size:11px;color:#F87171;margin-top:4px'>⚠ Set Groq API Key in sidebar</p>", unsafe_allow_html=True)

    # ── PIPELINE EXECUTION ──
    if run:
        st.info("⚡ **Speed:** Groq will finish all 5 agents in about 3 seconds!")
        agents_container = st.empty()
        agent_names = ["summarizer", "task_extractor", "risk_predictor"]
        if run_sentiment: agent_names.append("sentiment_analyzer")
        if run_followup:  agent_names.append("followup_agent")

        def show_agents(done: int):
            badges = "".join(
                f"<span class='agent-badge {'done' if i < done else ''}'>"
                f"{'✓' if i < done else '○'} {n.replace('_',' ')}</span>"
                for i, n in enumerate(agent_names)
            )
            agents_container.markdown(
                f"<div style='padding:12px 0'>{badges}</div>",
                unsafe_allow_html=True,
            )

        show_agents(0)
        progress = st.progress(0, text="Starting pipeline...")

        try:
            # Run pipeline with progress updates
            progress.progress(10, text="Agent 1/5 — Summarizer running...")
            show_agents(0)
            summary_data = agents.run_summarizer(transcript)

            progress.progress(30, text="Agent 2/5 — Task Extractor running...")
            show_agents(1)
            task_data = agents.run_task_extractor(transcript)

            progress.progress(55, text="Agent 3/5 — Risk Predictor running...")
            show_agents(2)
            risk_data = agents.run_risk_predictor(task_data.get("tasks", []), transcript)

            data = {**summary_data}
            data["tasks"] = task_data.get("tasks", [])
            data["risks"] = risk_data.get("risks", [])
            data["overloaded_people"] = risk_data.get("overloaded_people", [])

            if run_sentiment:
                progress.progress(72, text="Agent 4/5 — Sentiment Analyzer running...")
                show_agents(3)
                data["sentiment"] = agents.run_sentiment_analyzer(transcript)

            if run_followup:
                step = 4 if run_sentiment else 3
                progress.progress(88, text=f"Agent {step+1}/5 — Follow-up Agent running...")
                show_agents(step)
                followup_data = agents.run_followup_agent(data["tasks"])
                data["follow_ups"] = followup_data.get("follow_ups", [])

            progress.progress(100, text="Pipeline complete!")
            show_agents(len(agent_names))
            data["pipeline_version"] = "3.0"
            data["agents_run"] = agent_names

            # Save to DB
            meeting_id = db.save_meeting(data)
            data["_db_id"] = meeting_id

            st.session_state["last_result"] = data
            st.session_state["last_transcript"] = transcript
            progress.empty()

        except requests.HTTPError as e:
            st.error(f"API error: {e.response.status_code} — {e.response.text[:200]}")
            st.stop()
        except Exception as e:
            st.error(f"Pipeline error: {e}")
            st.stop()

    # ── RESULTS ──
    data = st.session_state.get("last_result")
    transcript_saved = st.session_state.get("last_transcript", transcript)

    if not data:
        st.markdown("<div style='text-align:center;padding:60px 0;color:#3F3F46;font-size:14px'>Paste a transcript and click Analyze to get started.</div>", unsafe_allow_html=True)
        st.stop()

    tasks     = data.get("tasks", [])
    risks     = data.get("risks", [])
    decisions = data.get("decisions", [])
    questions = data.get("open_questions", [])
    mq        = data.get("meeting_quality", {})
    score     = mq.get("score", 0)
    sentiment = data.get("sentiment", {})
    followups = data.get("follow_ups", [])

    # ── METRICS ROW ──
    st.markdown("<div class='sh'>Overview</div>", unsafe_allow_html=True)
    m1, m2, m3, m4, m5 = st.columns(5)
    score_color = "#4ADE80" if score >= 67 else "#FCD34D" if score >= 34 else "#F87171"
    for col, label, val, color in [
        (m1, "Action Items",    len(tasks),     "#E4E4E7"),
        (m2, "Risk Flags",      len(risks),     "#F87171"),
        (m3, "Decisions Made",  len(decisions), "#4ADE80"),
        (m4, "Open Questions",  len(questions), "#FCD34D"),
        (m5, "Quality Score",   f"{score}/100", score_color),
    ]:
        with col:
            st.markdown(f"""<div class='metric'>
              <div class='label'>{label}</div>
              <div class='val' style='color:{color}'>{val}</div>
            </div>""", unsafe_allow_html=True)

    # ── SUMMARY + QUALITY + RISKS ──
    st.markdown("<div class='sh'>Report</div>", unsafe_allow_html=True)
    col_left, col_right = st.columns([3, 2])

    with col_left:
        # Summary card
        attendees_str = ", ".join(data.get("attendees", []))
        st.markdown(f"""<div class='card'>
          <div style='font-size:11px;color:#52525B;margin-bottom:8px;font-weight:600;letter-spacing:.08em;text-transform:uppercase'>
            {data.get('meeting_title','Meeting')} &nbsp;·&nbsp; {data.get('date','')}
            {'&nbsp;·&nbsp; ' + attendees_str if attendees_str else ''}
          </div>
          <div style='font-size:14px;line-height:1.7;color:#A1A1AA'>{data.get('summary','')}</div>
        </div>""", unsafe_allow_html=True)

        # Key points
        if data.get("key_points"):
            st.markdown("<div style='margin-top:4px'>", unsafe_allow_html=True)
            for kp in data["key_points"]:
                st.markdown(f"<div style='font-size:12px;color:#71717A;padding:4px 0;border-bottom:1px solid #18181B'>→ {kp}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # Decisions
        if decisions:
            st.markdown("<div class='sh' style='padding-top:18px'>Decisions</div>", unsafe_allow_html=True)
            for d in decisions:
                st.markdown(f"<div style='font-size:13px;padding:6px 0;border-bottom:1px solid #18181B;color:#D4D4D8'>✅ &nbsp;{d}</div>", unsafe_allow_html=True)

        # Open questions
        if questions:
            st.markdown("<div class='sh' style='padding-top:18px'>Open Questions</div>", unsafe_allow_html=True)
            for q in questions:
                st.markdown(f"<div style='font-size:13px;padding:6px 0;border-bottom:1px solid #18181B;color:#71717A'>❓ &nbsp;{q}</div>", unsafe_allow_html=True)

    with col_right:
        # Quality score
        bar_w = min(score * 2, 200)
        st.markdown(f"""<div class='card'>
          <div style='font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#52525B;margin-bottom:12px'>Meeting Quality</div>
          <div style='font-size:36px;font-weight:700;color:{score_color};font-family:DM Mono,monospace'>
            {score}<span style='font-size:16px;color:#3F3F46'>/100</span>
          </div>
          <div class='qbar-bg'><div class='qbar-fill' style='width:{bar_w}px;background:{score_color}'></div></div>
          <div style='font-size:12px;color:#52525B;margin-top:6px;margin-bottom:14px'>{mq.get('note','')}</div>
          <div style='display:flex;flex-direction:column;gap:5px'>
            <div style='font-size:12px;color:{"#4ADE80" if mq.get("has_decisions") else "#F87171"}'>{"✓" if mq.get("has_decisions") else "✗"} Decisions recorded</div>
            <div style='font-size:12px;color:{"#4ADE80" if mq.get("has_owners") else "#F87171"}'>{"✓" if mq.get("has_owners") else "✗"} All tasks have owners</div>
            <div style='font-size:12px;color:{"#4ADE80" if mq.get("has_deadlines") else "#F87171"}'>{"✓" if mq.get("has_deadlines") else "✗"} All tasks have deadlines</div>
          </div>
        </div>""", unsafe_allow_html=True)

        # Risk flags
        if risks:
            st.markdown("<div class='sh' style='padding-top:14px'>Risk Flags</div>", unsafe_allow_html=True)
            for r in risks:
                label = RISK_LABELS.get(r.get("type", ""), "⚠️ Risk")
                sev = r.get("severity", "Medium")
                sev_chip = chip(sev, SEVERITY_CHIP.get(sev, "chip-gray"))
                rec = r.get("recommendation", "")
                st.markdown(f"""<div class='risk-card'>
                  <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:4px'>
                    <span class='risk-label' style='color:#D97706'>{label}</span>
                    {sev_chip}
                  </div>
                  <div style='font-size:12px;color:#A16207'>{r.get('description','')}</div>
                  {f"<div style='font-size:11px;color:#71717A;margin-top:5px'>💡 {rec}</div>" if rec else ""}
                </div>""", unsafe_allow_html=True)

    # ── ACTION ITEMS ──
    st.markdown("<div class='sh'>Action Items</div>", unsafe_allow_html=True)

    if tasks:
        sorted_tasks = sorted(tasks, key=lambda t: (
            {"High": 0, "Medium": 1, "Low": 2}.get(t.get("priority", "Medium"), 1),
            0 if t.get("deadline", "Not set") not in ("Not set", "not set") else 1,
        ))
        for i, t in enumerate(sorted_tasks):
            p = t.get("priority", "Medium")
            c_lvl = t.get("complexity", "Medium")
            cat = t.get("category", "")
            owner = t.get("owner", "Unassigned")
            deadline = t.get("deadline", "Not set")
            deadline_color = "#F87171" if deadline.lower() == "not set" else "#E4E4E7"

            with st.expander(f"{priority_icon(p)} **{t.get('description','')}**"):
                cols = st.columns([2, 2, 2, 2])
                with cols[0]:
                    st.markdown(f"<div style='font-size:11px;color:#52525B;margin-bottom:3px'>OWNER</div><div style='font-size:14px;font-weight:600'>{owner}</div>", unsafe_allow_html=True)
                with cols[1]:
                    st.markdown(f"<div style='font-size:11px;color:#52525B;margin-bottom:3px'>DEADLINE</div><div style='font-size:14px;font-weight:600;color:{deadline_color}'>{deadline}</div>", unsafe_allow_html=True)
                with cols[2]:
                    st.markdown(f"<div style='font-size:11px;color:#52525B;margin-bottom:3px'>PRIORITY</div>{chip(p, PRIORITY_CHIP.get(p,'chip-gray'))}", unsafe_allow_html=True)
                with cols[3]:
                    st.markdown(f"<div style='font-size:11px;color:#52525B;margin-bottom:3px'>COMPLEXITY</div>{chip(c_lvl, COMPLEXITY_CHIP.get(c_lvl,'chip-gray'))}", unsafe_allow_html=True)

                if cat:
                    st.markdown(f"<div style='margin-top:8px'>{chip(cat,'chip-blue')}</div>", unsafe_allow_html=True)
                if t.get("notes"):
                    st.markdown(f"<div style='font-size:12px;color:#71717A;margin-top:8px;padding:8px;background:#18181B;border-radius:6px'>{t['notes']}</div>", unsafe_allow_html=True)
                if t.get("depends_on"):
                    st.markdown(f"<div style='font-size:11px;color:#6366F1;margin-top:6px'>🔗 Depends on: {t['depends_on']}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<p style='color:#52525B;font-size:13px'>No action items found.</p>", unsafe_allow_html=True)

    # ── SENTIMENT ANALYSIS ──
    if sentiment:
        st.markdown("<div class='sh'>Meeting Dynamics & Sentiment</div>", unsafe_allow_html=True)
        sa_left, sa_right = st.columns([1, 2])

        with sa_left:
            tone = sentiment.get("overall_tone", "")
            health = sentiment.get("meeting_health", "")
            health_color = {"Good": "#4ADE80", "At Risk": "#FCD34D", "Poor": "#F87171"}.get(health, "#A1A1AA")
            st.markdown(f"""<div class='card'>
              <div style='font-size:11px;color:#52525B;text-transform:uppercase;letter-spacing:.08em;font-weight:600;margin-bottom:10px'>Overall</div>
              <div style='font-size:20px;font-weight:700;color:#E4E4E7;margin-bottom:4px'>{tone}</div>
              <div style='font-size:13px;color:{health_color};margin-bottom:10px'>● {health}</div>
              <div style='font-size:12px;color:#71717A'>{sentiment.get("health_reason","")}</div>
            </div>""", unsafe_allow_html=True)

            if sentiment.get("positive_signals"):
                st.markdown("<div style='margin-top:10px'>", unsafe_allow_html=True)
                for s in sentiment["positive_signals"][:3]:
                    st.markdown(f"<div style='font-size:12px;color:#4ADE80;padding:3px 0'>+ {s}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            if sentiment.get("warning_signals"):
                for s in sentiment["warning_signals"][:2]:
                    st.markdown(f"<div style='font-size:12px;color:#F87171;padding:3px 0'>⚠ {s}</div>", unsafe_allow_html=True)

        with sa_right:
            for speaker in sentiment.get("speaker_analysis", []):
                s_color = SENTIMENT_COLOR.get(speaker.get("sentiment", "Neutral"), "#A1A1AA")
                eng = speaker.get("engagement_level", "Medium")
                eng_color = {"High": "#4ADE80", "Medium": "#FCD34D", "Low": "#F87171"}.get(eng, "#A1A1AA")
                st.markdown(f"""<div class='speaker-row'>
                  <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px'>
                    <div style='font-weight:600;font-size:14px'>{speaker.get('name','')}</div>
                    <div style='display:flex;gap:6px;align-items:center'>
                      <span class='sentiment-pill' style='background:{"#0D2112" if s_color=="#4ADE80" else "#2D2200" if s_color=="#FCD34D" else "#1C0D0D"};color:{s_color}'>{speaker.get("sentiment","")}</span>
                      <span style='font-size:11px;color:{eng_color}'>● {eng} engagement</span>
                    </div>
                  </div>
                  <div style='font-size:12px;color:#71717A'>{speaker.get("tone_notes","")}</div>
                  {"".join(f"<div style='font-size:11px;color:#F87171;margin-top:4px'>⚠ {c}</div>" for c in speaker.get("potential_concerns",[])[:2])}
                </div>""", unsafe_allow_html=True)

    # ── FOLLOW-UP MESSAGES ──
    if followups:
        st.markdown("<div class='sh'>Auto-generated Follow-up Messages</div>", unsafe_allow_html=True)
        for fu in followups:
            urgency = fu.get("urgency", "This Week")
            urgency_color = {"Immediate": "#F87171", "This Week": "#FCD34D", "This Sprint": "#A1A1AA"}.get(urgency, "#A1A1AA")
            with st.expander(f"✉️ To: **{fu.get('recipient','')}** — {fu.get('subject','')}"):
                st.markdown(f"<span style='font-size:11px;color:{urgency_color}'>⏱ {urgency}</span>", unsafe_allow_html=True)
                st.markdown(f"<div style='background:#111113;border:1px solid #1E1E22;border-radius:8px;padding:14px 18px;font-size:13px;line-height:1.6;color:#D4D4D8;margin:8px 0;white-space:pre-wrap'>{fu.get('message','')}</div>", unsafe_allow_html=True)
                st.code(fu.get("message", ""), language=None)

    # ── EXPORT & SEND ──
    st.markdown("<div class='sh'>Send & Export</div>", unsafe_allow_html=True)
    act1, act2, act3, act4, act5 = st.columns(5)

    with act1:
        if st.button("📤 Send to Slack"):
            if not slack_webhook:
                st.markdown("<div class='status-err'>Set Slack Webhook in sidebar</div>", unsafe_allow_html=True)
            else:
                ok = send_slack(data, slack_webhook)
                st.markdown(f"<div class='{'status-ok' if ok else 'status-err'}'>{'✓ Sent to Slack' if ok else '✗ Slack failed'}</div>", unsafe_allow_html=True)

    with act2:
        if st.button("📧 Send Email"):
            if not (email_sender and email_password and email_recipient):
                st.markdown("<div class='status-err'>Set Gmail credentials in sidebar</div>", unsafe_allow_html=True)
            else:
                try:
                    send_email_html(data, email_sender, email_password, email_recipient)
                    st.markdown("<div class='status-ok'>✓ Email sent</div>", unsafe_allow_html=True)
                except Exception as e:
                    st.markdown(f"<div class='status-err'>{e}</div>", unsafe_allow_html=True)

    with act3:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            "⬇️ Export JSON",
            data=json.dumps(data, indent=2),
            file_name=f"meeting_{timestamp}.json",
            mime="application/json",
        )

    with act4:
        st.download_button(
            "📋 Export Jira CSV",
            data=export_jira_csv(tasks),
            file_name=f"jira_tasks_{timestamp}.csv",
            mime="text/csv",
        )

    with act5:
        st.download_button(
            "📝 Export Notion MD",
            data=export_notion_md(data),
            file_name=f"meeting_notes_{timestamp}.md",
            mime="text/markdown",
        )


# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 — HISTORY
# ═════════════════════════════════════════════════════════════════════════════
with tab_history:
    st.markdown("<div class='sh'>Past Meetings</div>", unsafe_allow_html=True)

    meetings = db.get_all_meetings()
    stats = db.get_stats()

    # Stats row
    hs1, hs2, hs3, hs4 = st.columns(4)
    for col, label, val, color in [
        (hs1, "Total Meetings", stats["total_meetings"], "#E4E4E7"),
        (hs2, "Total Tasks", stats["total_tasks"], "#E4E4E7"),
        (hs3, "Open Tasks", stats["open_tasks"], "#FCD34D"),
        (hs4, "Avg Quality", f"{stats['avg_quality_score']:.0f}/100", "#A78BFA"),
    ]:
        with col:
            st.markdown(f"""<div class='metric'>
              <div class='label'>{label}</div>
              <div class='val' style='color:{color};font-size:26px'>{val}</div>
            </div>""", unsafe_allow_html=True)

    if not meetings:
        st.markdown("<div style='text-align:center;padding:40px 0;color:#3F3F46;font-size:13px'>No meetings yet. Run your first analysis above.</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='sh' style='padding-top:20px'>Meeting Log</div>", unsafe_allow_html=True)
        for m in meetings:
            score = m.get("quality_score", 0)
            sc = "#4ADE80" if score >= 67 else "#FCD34D" if score >= 34 else "#F87171"
            attendees = json.loads(m.get("attendees", "[]"))
            att_str = ", ".join(attendees[:3]) + ("…" if len(attendees) > 3 else "")

            with st.expander(f"**{m['title']}** &nbsp; {m.get('date','')} &nbsp; — Quality: {score}/100"):
                c1, c2 = st.columns([3, 1])
                with c1:
                    if m.get("summary"):
                        st.markdown(f"<div style='font-size:13px;color:#A1A1AA;line-height:1.6'>{m['summary']}</div>", unsafe_allow_html=True)
                    if att_str:
                        st.markdown(f"<div style='font-size:11px;color:#52525B;margin-top:8px'>👥 {att_str}</div>", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"<div style='text-align:center;font-size:36px;font-weight:700;color:{sc};font-family:DM Mono,monospace'>{score}<span style='font-size:14px;color:#3F3F46'>/100</span></div>", unsafe_allow_html=True)

                if st.button("Load this meeting", key=f"load_{m['id']}"):
                    full = db.get_meeting_by_id(m["id"])
                    if full:
                        st.session_state["last_result"] = full
                        st.success("Loaded — switch to Analyze tab to view")


# ═════════════════════════════════════════════════════════════════════════════
# TAB 3 — TASK TRACKER
# ═════════════════════════════════════════════════════════════════════════════
with tab_tracker:
    st.markdown("<div class='sh'>Task Tracker — All Open Tasks By Owner</div>", unsafe_allow_html=True)

    tasks_by_owner = db.get_open_tasks_by_owner()

    if not tasks_by_owner:
        st.markdown("<div style='text-align:center;padding:40px 0;color:#3F3F46;font-size:13px'>No open tasks yet. Run an analysis to populate.</div>", unsafe_allow_html=True)
    else:
        for owner, owner_tasks in tasks_by_owner.items():
            count = len(owner_tasks)
            overload = count >= 3
            st.markdown(f"""<div style='margin:16px 0 8px;display:flex;align-items:center;gap:10px'>
              <span style='font-size:15px;font-weight:600;color:#E4E4E7'>{owner}</span>
              <span class='chip {"chip-red" if overload else "chip-gray"}'>{count} task{"s" if count!=1 else ""}{" ⚠ overloaded" if overload else ""}</span>
            </div>""", unsafe_allow_html=True)

            for t in owner_tasks:
                p = t.get("priority", "Medium")
                status = t.get("status", "Open")
                status_color = {"Open": "#A1A1AA", "In Progress": "#60A5FA", "Done": "#4ADE80", "Blocked": "#F87171"}.get(status, "#A1A1AA")
                st.markdown(f"""<div class='card-sm' style='margin-left:20px'>
                  <div style='display:flex;justify-content:space-between;align-items:center'>
                    <div style='font-size:13px;color:#D4D4D8'>{priority_icon(p)} {t.get('description','')}</div>
                    <div style='display:flex;gap:6px;align-items:center;flex-shrink:0;margin-left:12px'>
                      <span style='font-size:11px;color:#52525B'>{t.get('deadline','')}</span>
                      <span style='font-size:11px;color:{status_color}'>● {status}</span>
                      <span style='font-size:10px;color:#3F3F46'>{t.get('meeting_title','')}</span>
                    </div>
                  </div>
                </div>""", unsafe_allow_html=True)