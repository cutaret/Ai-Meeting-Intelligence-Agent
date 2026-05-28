import streamlit as st
import json
import os
import sys
import requests
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Make utils importable
sys.path.insert(0, os.path.dirname(__file__))
from utils.storage import (
    load_groups, save_groups, create_group, update_group_members,
    delete_group, save_meeting_result, get_meetings_for_group, get_meeting_by_id
)
from utils.teams_parser import detect_and_parse
from utils.agents import analyse_meeting

load_dotenv()

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Meeting Intelligence — Manager Console",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
.stApp { background: #0A0A0C; color: #DEDBD5; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 2.5rem 4rem; max-width: 1200px; }

/* sidebar */
[data-testid="stSidebar"] { background: #0F0F13; border-right: 1px solid #1A1A22; }
[data-testid="stSidebar"] .block-container { padding: 1.5rem 1rem; }

/* inputs */
textarea, .stTextArea textarea, input[type="text"], .stTextInput input {
    background: #13131A !important;
    border: 1px solid #252530 !important;
    border-radius: 8px !important;
    color: #DEDBD5 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 13px !important;
}
textarea:focus, input:focus { border-color: #6C63FF !important; box-shadow: 0 0 0 2px rgba(108,99,255,0.15) !important; }

/* primary button */
.stButton > button {
    background: #6C63FF; color: white; border: none; border-radius: 8px;
    padding: 0.55rem 1.6rem; font-family: 'IBM Plex Sans', sans-serif;
    font-weight: 500; font-size: 13px; transition: all .15s; width: 100%;
}
.stButton > button:hover { background: #5A52DD; }
.stButton > button:disabled { background: #252530; color: #444; }

/* file uploader */
[data-testid="stFileUploader"] {
    background: #13131A; border: 1px dashed #2A2A38;
    border-radius: 10px; padding: 16px;
}

/* selectbox */
.stSelectbox select, [data-baseweb="select"] { background: #13131A !important; color: #DEDBD5 !important; border-color: #252530 !important; }

/* number input */
.stNumberInput input { background: #13131A !important; color: #DEDBD5 !important; }

/* tabs */
.stTabs [data-baseweb="tab-list"] { background: transparent; border-bottom: 1px solid #1A1A22; gap: 0; }
.stTabs [data-baseweb="tab"] { background: transparent; color: #666; font-family: 'IBM Plex Sans'; font-size: 13px; font-weight: 500; padding: 10px 20px; border: none; border-bottom: 2px solid transparent; }
.stTabs [aria-selected="true"] { color: #DEDBD5; border-bottom: 2px solid #6C63FF; background: transparent; }

/* cards */
.g-card {
    background: #13131A; border: 1px solid #1E1E28;
    border-radius: 12px; padding: 18px 20px; margin-bottom: 10px;
    cursor: pointer; transition: border-color .15s, background .15s;
}
.g-card:hover { border-color: #6C63FF; background: #16161F; }
.g-card.active { border-color: #6C63FF; background: #14141E; }
.g-card-title { font-size: 14px; font-weight: 600; color: #DEDBD5; margin-bottom: 4px; }
.g-card-meta { font-size: 12px; color: #555; font-family: 'IBM Plex Mono'; }

/* metric mini */
.m-pill {
    background: #1A1A24; border: 1px solid #252530;
    border-radius: 8px; padding: 12px 16px; text-align: center;
}
.m-pill-val { font-size: 24px; font-weight: 600; font-family: 'IBM Plex Mono'; }
.m-pill-lbl { font-size: 11px; color: #555; text-transform: uppercase; letter-spacing: .06em; margin-top: 3px; }

/* task row */
.t-row {
    background: #13131A; border: 1px solid #1E1E28;
    border-radius: 8px; padding: 12px 16px; margin-bottom: 6px;
}
.t-row-title { font-size: 13px; font-weight: 500; color: #DEDBD5; margin-bottom: 5px; }
.t-chips { display: flex; gap: 8px; flex-wrap: wrap; }
.t-chip { font-size: 11px; padding: 2px 8px; border-radius: 4px; font-family: 'IBM Plex Mono'; }

/* member badge */
.mbadge {
    background: #1A1A24; border: 1px solid #252530; border-radius: 8px;
    padding: 10px 14px; margin-bottom: 6px; display: flex; align-items: center; gap: 12px;
}
.mbadge-av {
    width: 34px; height: 34px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; font-weight: 600; flex-shrink: 0;
}
.mbadge-name { font-size: 13px; font-weight: 500; color: #DEDBD5; }
.mbadge-role { font-size: 11px; color: #666; font-family: 'IBM Plex Mono'; }

/* risk */
.risk-item { background: #180F08; border: 1px solid #3A2510; border-radius: 8px; padding: 10px 14px; margin-bottom: 6px; font-size: 12px; color: #C87A3A; }

/* section header */
.s-head { font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: .12em; color: #444; padding: 20px 0 10px; border-bottom: 1px solid #181820; margin-bottom: 14px; }

/* meeting history item */
.hist-row { background: #13131A; border: 1px solid #1E1E28; border-radius: 8px; padding: 12px 16px; margin-bottom: 6px; cursor: pointer; }
.hist-row:hover { border-color: #6C63FF; }
.hist-title { font-size: 13px; font-weight: 500; color: #DEDBD5; }
.hist-meta { font-size: 11px; color: #555; font-family: 'IBM Plex Mono'; margin-top: 3px; }

/* status */
.ok-badge { background: #0A1F12; border: 1px solid #1A4A28; border-radius: 6px; padding: 8px 12px; color: #4ADE80; font-size: 12px; }
.err-badge { background: #180A0A; border: 1px solid #4A1A1A; border-radius: 6px; padding: 8px 12px; color: #F87171; font-size: 12px; }

/* quality bar */
.qbar-bg { background: #1A1A24; border-radius: 3px; height: 6px; width: 100%; margin: 6px 0; }
.qbar-fill { height: 6px; border-radius: 3px; }

/* avatar colors */
.av0{background:#2D1F6E;color:#A78BFA}
.av1{background:#0F2A1A;color:#4ADE80}
.av2{background:#2A1010;color:#F87171}
.av3{background:#1A2A0F;color:#86EFAC}
.av4{background:#2A1F0F;color:#FCD34D}
.av5{background:#0F1A2A;color:#60A5FA}
.av6{background:#2A0F1A;color:#F472B6}
.av7{background:#1A1A0F;color:#D9F99D}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
PRIORITY_COLORS = {"High": "#F87171", "Medium": "#FBBF24", "Low": "#4ADE80"}
RISK_ICONS = {
    "missing_owner":    "👤 No owner",
    "missing_deadline": "📅 No deadline",
    "overloaded_person":"⚠️ Overloaded",
    "blocker":          "🚫 Blocker",
    "role_mismatch":    "🔀 Role mismatch",
}
AV_COLORS = ["av0","av1","av2","av3","av4","av5","av6","av7"]

SAMPLE_TRANSCRIPT = """Meeting: AI Team Sprint Planning
Date: May 26, 2026
Attendees: Neha (SDE), Raghav (Data Scientist), Amar (HR), Priya (Product Manager)

Priya: Alright everyone, let's get started on the sprint planning. Neha, what's the status on the model API integration?

Neha: I finished the initial integration last week. I just need to write unit tests and then it should be ready for QA. I can have tests done by Wednesday.

Priya: Great. Raghav, what about the data pipeline for the new recommendation engine?

Raghav: The pipeline is about 70% done. There's one blocker — I need the cleaned dataset from the data engineering team. Without that I can't finish before Friday.

Priya: Got it. I'll follow up with data engineering today and get that unblocked. Amar, on the onboarding side, are the new joiners ready for the AI team orientation?

Amar: Yes, I have the orientation scheduled for Thursday. I still need everyone's availability confirmed for the team lunch on Friday though.

Priya: Can you send a calendar invite today for the lunch? We should also decide on the sprint goal. I think we should commit to having the recommendation engine MVP live by end of next week. Does everyone agree?

Neha: That's tight for me with the testing work, but doable if the API review gets done by Thursday.

Raghav: I'm fine with that as long as the dataset arrives by Tuesday.

Priya: Okay, so our sprint goal is the recommendation engine MVP by May 31st. Neha, can you also review Raghav's pipeline code once your tests are done?

Neha: Sure, I can do that Thursday or Friday.

Amar: I also wanted to flag that two interns are joining next week. Should I set up their development environments?

Priya: Yes please, can you coordinate with Neha on what they'll need? Get that done by Monday.

Neha: I'll send Amar the setup guide today so he has it before the weekend.

Priya: Perfect. Any blockers I haven't captured?

Raghav: Just the dataset — that's my main blocker.

Priya: Noted. I'll handle it. Let's wrap up."""

def avatar_html(name: str, idx: int) -> str:
    initials = "".join(p[0].upper() for p in name.split()[:2]) if name else "?"
    cls = AV_COLORS[idx % len(AV_COLORS)]
    return f"<div class='mbadge-av {cls}'>{initials}</div>"

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div style='font-size:11px;font-weight:600;letter-spacing:.12em;color:#6C63FF;text-transform:uppercase;margin-bottom:4px'>Manager Console</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:20px;font-weight:600;color:#DEDBD5;margin-bottom:20px'>Meeting Intelligence</div>", unsafe_allow_html=True)

    api_key = st.text_input("Anthropic API Key", value=os.getenv("ANTHROPIC_API_KEY", ""), type="password", placeholder="sk-ant-...")
    slack_webhook = st.text_input("Slack Webhook", value=os.getenv("SLACK_WEBHOOK_URL", ""), placeholder="https://hooks.slack.com/...")

    st.markdown("---")

    # Group selector
    st.markdown("<div style='font-size:11px;color:#555;text-transform:uppercase;letter-spacing:.1em;margin-bottom:10px'>Your Groups</div>", unsafe_allow_html=True)

    groups = load_groups()

    if "active_group_id" not in st.session_state:
        st.session_state.active_group_id = None

    for gid, g in groups.items():
        meetings = get_meetings_for_group(gid)
        is_active = st.session_state.active_group_id == gid
        card_cls = "g-card active" if is_active else "g-card"
        member_count = len(g.get("members", []))
        if st.button(f"{'▶ ' if is_active else ''}{g['name']}", key=f"grp_{gid}"):
            st.session_state.active_group_id = gid
            st.session_state.pop("show_new_group", None)
            st.rerun()
        st.markdown(f"<div style='font-size:11px;color:#444;margin:-10px 0 6px 4px;font-family:IBM Plex Mono'>{member_count} members · {len(meetings)} meetings</div>", unsafe_allow_html=True)

    st.markdown("")
    if st.button("＋ New Group"):
        st.session_state.show_new_group = True
        st.session_state.active_group_id = None

    st.markdown("---")
    st.markdown("<p style='font-size:11px;color:#333'>Meeting Intelligence v3<br>Manager Console</p>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# MAIN AREA
# ─────────────────────────────────────────────

# ── Create New Group ──
if st.session_state.get("show_new_group"):
    st.markdown("<div class='s-head'>Create New Group</div>", unsafe_allow_html=True)
    c1, c2 = st.columns([2, 3])
    with c1:
        new_name = st.text_input("Group name", placeholder="e.g. Intern Batch 2026")
    with c2:
        new_desc = st.text_input("Description (optional)", placeholder="e.g. Summer interns on AI team")

    col_a, col_b, _ = st.columns([1, 1, 3])
    with col_a:
        if st.button("Create Group", disabled=not new_name.strip()):
            gid = create_group(new_name.strip(), new_desc.strip())
            st.session_state.active_group_id = gid
            st.session_state.pop("show_new_group", None)
            st.success(f"Group '{new_name}' created!")
            st.rerun()
    with col_b:
        if st.button("Cancel"):
            st.session_state.pop("show_new_group", None)
            st.rerun()
    st.stop()


# ── No group selected ──
if not st.session_state.active_group_id:
    st.markdown("""
    <div style='text-align:center;padding:80px 0'>
      <div style='font-size:48px;margin-bottom:16px'>🧠</div>
      <div style='font-size:22px;font-weight:600;color:#DEDBD5;margin-bottom:8px'>Manager Console</div>
      <div style='font-size:14px;color:#444;max-width:400px;margin:auto'>
        Create a group in the sidebar, add your team members once,<br>
        then analyse any meeting transcript with full team context.
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ── Load active group ──
groups = load_groups()
group = groups.get(st.session_state.active_group_id)
if not group:
    st.session_state.active_group_id = None
    st.rerun()

gid = group["id"]
members = group.get("members", [])
meetings = get_meetings_for_group(gid)

# ─────────────────────────────────────────────
# GROUP HEADER
# ─────────────────────────────────────────────
h1, h2 = st.columns([5, 1])
with h1:
    st.markdown(f"""
    <div style='padding:0 0 20px'>
      <div style='font-size:11px;color:#6C63FF;font-weight:600;letter-spacing:.1em;text-transform:uppercase;margin-bottom:6px'>
        Active Group
      </div>
      <div style='font-size:26px;font-weight:600;color:#DEDBD5;margin-bottom:4px'>{group['name']}</div>
      <div style='font-size:13px;color:#444'>{group.get('description','')}</div>
    </div>
    """, unsafe_allow_html=True)
with h2:
    if st.button("🗑 Delete Group"):
        delete_group(gid)
        st.session_state.active_group_id = None
        st.rerun()


# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab_analyse, tab_members, tab_history = st.tabs(["🔍 Analyse Meeting", "👥 Team Members", "📋 Meeting History"])


# ══════════════════════════════════════════════
# TAB 1 — ANALYSE
# ══════════════════════════════════════════════
with tab_analyse:

    if not members:
        st.markdown("""
        <div style='background:#13131A;border:1px solid #2A2A38;border-radius:10px;padding:20px 24px;margin-bottom:20px'>
          <div style='font-size:14px;font-weight:500;color:#FBBF24;margin-bottom:6px'>⚠️ No team members added yet</div>
          <div style='font-size:13px;color:#666'>Go to the <strong style='color:#DEDBD5'>Team Members</strong> tab to add members with their roles.
          The analysis will be much more accurate when it knows who's on the team.</div>
        </div>
        """, unsafe_allow_html=True)

    # Input method selector
    st.markdown("<div class='s-head'>Transcript Input</div>", unsafe_allow_html=True)
    input_method = st.radio(
        "Source",
        ["✏️ Paste text", "📁 Upload Teams file (.vtt / .txt)"],
        horizontal=True,
        label_visibility="collapsed"
    )

    transcript = ""
    parse_meta = {}
    source_label = "paste"

    if "✏️" in input_method:
        col_ta, col_sample = st.columns([6, 1])
        with col_sample:
            if st.button("Load\nsample"):
                st.session_state["pasted_transcript"] = SAMPLE_TRANSCRIPT
        transcript = st.text_area(
            "Transcript",
            value=st.session_state.get("pasted_transcript", ""),
            height=260,
            placeholder="Paste your meeting transcript here...\n\nTip: Include speaker names (e.g. 'Neha: I'll handle the tests') for accurate owner attribution.",
            label_visibility="collapsed"
        )
        if transcript:
            st.session_state["pasted_transcript"] = transcript
        source_label = "paste"

    else:
        st.markdown("""
        <div style='font-size:12px;color:#555;margin-bottom:8px'>
          <strong style='color:#888'>Microsoft Teams export:</strong>
          Teams → Meeting recording → Download transcript (.vtt) &nbsp;|&nbsp;
          Or copy-paste the transcript text as a .txt file.
        </div>
        """, unsafe_allow_html=True)

        uploaded = st.file_uploader(
            "Upload Teams transcript",
            type=["vtt", "txt"],
            label_visibility="collapsed"
        )
        if uploaded:
            raw_content = uploaded.read().decode("utf-8", errors="replace")
            transcript, parse_meta = detect_and_parse(uploaded.name, raw_content)
            source_label = "teams_vtt" if uploaded.name.endswith(".vtt") else "teams_txt"

            if parse_meta.get("speakers_detected"):
                st.markdown(f"""
                <div style='background:#0A1320;border:1px solid #1A3A50;border-radius:8px;padding:10px 14px;margin-bottom:8px'>
                  <span style='color:#60A5FA;font-size:12px'>✓ Parsed Teams transcript · {parse_meta.get('utterances',0)} utterances · Speakers: {', '.join(parse_meta['speakers_detected'])}</span>
                </div>
                """, unsafe_allow_html=True)

            with st.expander("Preview parsed transcript"):
                st.text(transcript[:1200] + ("..." if len(transcript) > 1200 else ""))

    # Analyse button
    st.markdown("")
    _, btn_col, _ = st.columns([1, 2, 1])
    with btn_col:
        can_run = bool(transcript.strip() and api_key)
        run = st.button("🧠 Run Analysis", disabled=not can_run)

    if not can_run and not transcript:
        st.markdown("<div style='text-align:center;font-size:12px;color:#333;margin-top:8px'>Add a transcript above to analyse</div>", unsafe_allow_html=True)
    if not api_key:
        st.markdown("<div style='text-align:center;font-size:12px;color:#F87171;margin-top:8px'>Add your Anthropic API key in the sidebar</div>", unsafe_allow_html=True)

    # Run analysis
    if run:
        with st.spinner("Analysing with Claude..."):
            try:
                result = analyse_meeting(transcript, members, api_key)
                meeting_id = save_meeting_result(gid, group["name"], transcript, result, source_label)
                st.session_state[f"result_{gid}"] = result
                st.session_state[f"transcript_{gid}"] = transcript
                st.success("Analysis complete — scroll down to see results")
            except Exception as e:
                st.error(f"Analysis failed: {e}")

    # Show result
    result = st.session_state.get(f"result_{gid}")
    if not result and meetings:
        result = meetings[0]["result"]

    if result:
        tasks = result.get("tasks", [])
        risks = result.get("risks", [])
        decisions = result.get("decisions", [])
        questions = result.get("open_questions", [])
        mq = result.get("meeting_quality", {})
        score = mq.get("score", 0)
        member_activity = result.get("member_activity", [])

        # metrics
        st.markdown("<div class='s-head'>Results — " + result.get("meeting_title", "Meeting") + "</div>", unsafe_allow_html=True)
        mc1, mc2, mc3, mc4, mc5 = st.columns(5)
        for col, val, label, color in [
            (mc1, len(tasks), "Tasks", "#DEDBD5"),
            (mc2, len(risks), "Risks", "#F87171"),
            (mc3, len(decisions), "Decisions", "#4ADE80"),
            (mc4, len(questions), "Open Qs", "#FBBF24"),
            (mc5, score, "Quality", "#A78BFA"),
        ]:
            col.markdown(f"<div class='m-pill'><div class='m-pill-val' style='color:{color}'>{val}</div><div class='m-pill-lbl'>{label}</div></div>", unsafe_allow_html=True)

        # summary + quality
        r1, r2 = st.columns([3, 2])

        with r1:
            st.markdown("<div class='s-head'>Summary</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:13px;line-height:1.75;color:#AAA;background:#13131A;border:1px solid #1E1E28;border-radius:8px;padding:14px 18px'>{result.get('summary','')}</div>", unsafe_allow_html=True)

            if decisions:
                st.markdown("<div class='s-head' style='padding-top:14px'>Decisions</div>", unsafe_allow_html=True)
                for d in decisions:
                    st.markdown(f"<div style='font-size:13px;padding:5px 0;border-bottom:1px solid #141420;color:#CCC'>✅ &nbsp;{d}</div>", unsafe_allow_html=True)

            if questions:
                st.markdown("<div class='s-head' style='padding-top:14px'>Open Questions</div>", unsafe_allow_html=True)
                for q in questions:
                    st.markdown(f"<div style='font-size:13px;padding:5px 0;border-bottom:1px solid #141420;color:#777'>❓ &nbsp;{q}</div>", unsafe_allow_html=True)

        with r2:
            # quality panel
            bar_w = min(score * 1.9, 190)
            qcolor = "#4ADE80" if score >= 67 else "#FBBF24" if score >= 34 else "#F87171"
            st.markdown(f"""
            <div style='background:#13131A;border:1px solid #1E1E28;border-radius:10px;padding:18px 20px'>
              <div style='font-size:11px;color:#444;text-transform:uppercase;letter-spacing:.1em;margin-bottom:10px'>Meeting Quality</div>
              <div style='font-size:36px;font-weight:600;color:{qcolor};font-family:IBM Plex Mono'>{score}<span style='font-size:16px;color:#333'>/100</span></div>
              <div class='qbar-bg'><div class='qbar-fill' style='width:{bar_w}px;background:{qcolor}'></div></div>
              <div style='font-size:12px;color:#555;margin-top:8px'>{mq.get("note","")}</div>
              <div style='margin-top:12px;display:flex;flex-direction:column;gap:5px'>
                <div style='font-size:12px;color:{"#4ADE80" if mq.get("has_decisions") else "#F87171"}'>{"✓" if mq.get("has_decisions") else "✗"} Decisions recorded</div>
                <div style='font-size:12px;color:{"#4ADE80" if mq.get("has_owners") else "#F87171"}'>{"✓" if mq.get("has_owners") else "✗"} All tasks have owners</div>
                <div style='font-size:12px;color:{"#4ADE80" if mq.get("has_deadlines") else "#F87171"}'>{"✓" if mq.get("has_deadlines") else "✗"} All tasks have deadlines</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            if risks:
                st.markdown("<div class='s-head' style='padding-top:14px'>Risk Flags</div>", unsafe_allow_html=True)
                for r in risks:
                    label = RISK_ICONS.get(r.get("type", ""), "⚠️ Risk")
                    sev = r.get("severity", "")
                    sev_color = "#F87171" if sev == "High" else "#FBBF24" if sev == "Medium" else "#AAA"
                    st.markdown(f"""
                    <div class='risk-item'>
                      <strong style='font-size:11px'>{label}</strong>
                      <span style='font-size:11px;float:right;color:{sev_color}'>{sev}</span><br>
                      {r.get('description','')}
                    </div>""", unsafe_allow_html=True)

        # Action items
        st.markdown("<div class='s-head'>Action Items</div>", unsafe_allow_html=True)
        if tasks:
            for t in tasks:
                p = t.get("priority", "Medium")
                pc = PRIORITY_COLORS.get(p, "#999")
                role = t.get("role", "")
                st.markdown(f"""
                <div class='t-row'>
                  <div class='t-row-title'>{t['description']}</div>
                  <div class='t-chips'>
                    <span class='t-chip' style='background:#1A1A28;color:#888'>👤 {t.get('owner','Unassigned')}</span>
                    {"<span class='t-chip' style='background:#1A1A28;color:#555'>" + role + "</span>" if role and role != "Unknown" else ""}
                    <span class='t-chip' style='background:#1A1A28;color:#777'>📅 {t.get('deadline','Not set')}</span>
                    <span class='t-chip' style='background:#1A1A28;color:{pc}'>● {p}</span>
                  </div>
                </div>""", unsafe_allow_html=True)

        # Member activity
        if member_activity:
            st.markdown("<div class='s-head'>Member Activity This Meeting</div>", unsafe_allow_html=True)
            act_cols = st.columns(min(len(member_activity), 4))
            for i, m in enumerate(member_activity):
                col = act_cols[i % len(act_cols)]
                spoke = m.get("spoke", False)
                n_tasks = m.get("tasks_assigned", 0)
                av_cls = AV_COLORS[i % len(AV_COLORS)]
                initials = "".join(p[0].upper() for p in m.get("name","?").split()[:2])
                col.markdown(f"""
                <div style='background:#13131A;border:1px solid #1E1E28;border-radius:10px;padding:14px;text-align:center;margin-bottom:8px'>
                  <div class='mbadge-av {av_cls}' style='margin:0 auto 8px;width:38px;height:38px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:600'>{initials}</div>
                  <div style='font-size:13px;font-weight:500;color:#DEDBD5'>{m.get("name","")}</div>
                  <div style='font-size:11px;color:#555;font-family:IBM Plex Mono;margin-top:2px'>{m.get("role","")}</div>
                  <div style='margin-top:10px;display:flex;justify-content:center;gap:10px'>
                    <div style='text-align:center'>
                      <div style='font-size:18px;font-weight:600;font-family:IBM Plex Mono;color:{"#FBBF24" if n_tasks > 2 else "#DEDBD5"}'>{n_tasks}</div>
                      <div style='font-size:10px;color:#444'>tasks</div>
                    </div>
                    <div style='text-align:center'>
                      <div style='font-size:14px;margin-top:2px'>{"🎙️" if spoke else "🔇"}</div>
                      <div style='font-size:10px;color:#444'>{"spoke" if spoke else "absent"}</div>
                    </div>
                  </div>
                </div>""", unsafe_allow_html=True)

        # Send actions
        st.markdown("<div class='s-head'>Send & Export</div>", unsafe_allow_html=True)
        a1, a2 = st.columns(2)
        with a1:
            if st.button("📤 Send to Slack"):
                if not slack_webhook:
                    st.markdown("<div class='err-badge'>Set Slack Webhook in sidebar first</div>", unsafe_allow_html=True)
                else:
                    try:
                        tasks_text = "\n".join(f"• *{t['description']}* — {t.get('owner','?')} | {t.get('deadline','No deadline')}" for t in tasks[:8])
                        payload = {
                            "blocks": [
                                {"type": "header", "text": {"type": "plain_text", "text": f"📊 {result.get('meeting_title','Meeting')} — {group['name']}"}},
                                {"type": "section", "text": {"type": "mrkdwn", "text": result.get('summary','')}},
                                {"type": "divider"},
                                {"type": "section", "text": {"type": "mrkdwn", "text": f"*Action Items ({len(tasks)})*\n{tasks_text}"}},
                                {"type": "context", "elements": [{"type": "mrkdwn", "text": f"Quality: *{score}/100* | Group: {group['name']} | Meeting Intelligence"}]}
                            ]
                        }
                        resp = requests.post(slack_webhook, json=payload, timeout=10)
                        if resp.status_code == 200:
                            st.markdown("<div class='ok-badge'>✓ Posted to Slack</div>", unsafe_allow_html=True)
                        else:
                            st.markdown("<div class='err-badge'>Slack error — check webhook URL</div>", unsafe_allow_html=True)
                    except Exception as e:
                        st.markdown(f"<div class='err-badge'>Error: {e}</div>", unsafe_allow_html=True)
        with a2:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            fname = f"{group['name'].replace(' ','_')}_{ts}.json"
            st.download_button("⬇️ Export JSON", data=json.dumps(result, indent=2), file_name=fname, mime="application/json")


# ══════════════════════════════════════════════
# TAB 2 — TEAM MEMBERS
# ══════════════════════════════════════════════
with tab_members:
    st.markdown("<div class='s-head'>Team Members — saved permanently for this group</div>", unsafe_allow_html=True)

    st.markdown("""
    <div style='font-size:13px;color:#555;margin-bottom:16px'>
    Add each team member once. This information is saved and automatically included in every future meeting analysis for this group.
    Claude will use names, roles, and notes to correctly attribute tasks and flag role mismatches.
    </div>
    """, unsafe_allow_html=True)

    # Edit members form
    if "editing_members" not in st.session_state:
        st.session_state.editing_members = members.copy() if members else [{"name": "", "role": "", "notes": ""}]

    # Sync if switching groups
    if st.session_state.get("_last_member_group") != gid:
        st.session_state.editing_members = members.copy() if members else [{"name": "", "role": "", "notes": ""}]
        st.session_state._last_member_group = gid

    current = st.session_state.editing_members

    st.markdown("<div style='font-size:11px;color:#444;margin-bottom:8px'>NAME &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ROLE &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; NOTES (optional)</div>", unsafe_allow_html=True)

    updated = []
    to_remove = []

    for i, m in enumerate(current):
        mc1, mc2, mc3, mc4 = st.columns([3, 3, 4, 0.5])
        with mc1:
            name = st.text_input("Name", value=m.get("name", ""), key=f"mname_{gid}_{i}", label_visibility="collapsed", placeholder=f"Member {i+1} name")
        with mc2:
            role = st.text_input("Role", value=m.get("role", ""), key=f"mrole_{gid}_{i}", label_visibility="collapsed", placeholder="e.g. SDE, Data Scientist")
        with mc3:
            notes = st.text_input("Notes", value=m.get("notes", ""), key=f"mnotes_{gid}_{i}", label_visibility="collapsed", placeholder="e.g. backend focus, joined Jan 2026")
        with mc4:
            if st.button("✕", key=f"mdel_{gid}_{i}"):
                to_remove.append(i)
        updated.append({"name": name.strip(), "role": role.strip(), "notes": notes.strip()})

    for idx in sorted(to_remove, reverse=True):
        updated.pop(idx)

    st.session_state.editing_members = updated

    col_add, col_save, _ = st.columns([1, 1, 3])
    with col_add:
        if st.button("＋ Add Member"):
            st.session_state.editing_members.append({"name": "", "role": "", "notes": ""})
            st.rerun()
    with col_save:
        if st.button("💾 Save Members"):
            clean = [m for m in updated if m["name"].strip()]
            update_group_members(gid, clean)
            st.success(f"Saved {len(clean)} members to {group['name']}")
            st.rerun()

    # Display saved members
    saved = [m for m in members if m.get("name")]
    if saved:
        st.markdown("<div class='s-head' style='padding-top:20px'>Saved Members</div>", unsafe_allow_html=True)
        for i, m in enumerate(saved):
            av_cls = AV_COLORS[i % len(AV_COLORS)]
            initials = "".join(p[0].upper() for p in m["name"].split()[:2])
            notes_txt = f" · {m['notes']}" if m.get("notes") else ""
            st.markdown(f"""
            <div class='mbadge'>
              <div class='mbadge-av {av_cls}'>{initials}</div>
              <div>
                <div class='mbadge-name'>{m['name']}</div>
                <div class='mbadge-role'>{m.get('role','—')}{notes_txt}</div>
              </div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("<div style='color:#333;font-size:13px;padding:20px 0'>No members saved yet. Add members above and click Save.</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# TAB 3 — MEETING HISTORY
# ══════════════════════════════════════════════
with tab_history:
    st.markdown("<div class='s-head'>Meeting History — " + group['name'] + "</div>", unsafe_allow_html=True)

    if not meetings:
        st.markdown("<div style='color:#333;font-size:13px;padding:20px 0'>No meetings analysed yet for this group. Use the Analyse tab to process your first meeting.</div>", unsafe_allow_html=True)
    else:
        # Selected meeting detail view
        selected_id = st.session_state.get(f"selected_meeting_{gid}")

        if selected_id:
            mtg = get_meeting_by_id(selected_id)
            if mtg:
                r = mtg["result"]
                dt = mtg.get("analyzed_at","")[:16].replace("T", " at ")
                src_icons = {"paste": "✏️", "teams_vtt": "🎥 Teams", "teams_txt": "📄 Teams"}
                src = src_icons.get(mtg.get("source","paste"), "✏️")

                back_col, _ = st.columns([1, 5])
                with back_col:
                    if st.button("← Back to list"):
                        st.session_state.pop(f"selected_meeting_{gid}", None)
                        st.rerun()

                st.markdown(f"<div style='font-size:20px;font-weight:600;color:#DEDBD5;margin:10px 0 4px'>{r.get('meeting_title','Meeting')}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:12px;color:#444;font-family:IBM Plex Mono'>{src} · {dt}</div>", unsafe_allow_html=True)

                htasks = r.get("tasks", [])
                hrisks = r.get("risks", [])
                hq = r.get("meeting_quality", {})
                hs = hq.get("score", 0)

                hm1, hm2, hm3, hm4 = st.columns(4)
                for col, val, label, color in [
                    (hm1, len(htasks), "Tasks", "#DEDBD5"),
                    (hm2, len(hrisks), "Risks", "#F87171"),
                    (hm3, len(r.get("decisions",[])), "Decisions", "#4ADE80"),
                    (hm4, hs, "Quality", "#A78BFA"),
                ]:
                    col.markdown(f"<div class='m-pill'><div class='m-pill-val' style='color:{color}'>{val}</div><div class='m-pill-lbl'>{label}</div></div>", unsafe_allow_html=True)

                st.markdown("<div class='s-head' style='padding-top:16px'>Summary</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:13px;line-height:1.75;color:#AAA;background:#13131A;border:1px solid #1E1E28;border-radius:8px;padding:14px 18px'>{r.get('summary','')}</div>", unsafe_allow_html=True)

                if r.get("decisions"):
                    st.markdown("<div class='s-head'>Decisions</div>", unsafe_allow_html=True)
                    for d in r["decisions"]:
                        st.markdown(f"<div style='font-size:13px;padding:5px 0;border-bottom:1px solid #141420;color:#CCC'>✅ &nbsp;{d}</div>", unsafe_allow_html=True)

                st.markdown("<div class='s-head'>Action Items</div>", unsafe_allow_html=True)
                for t in htasks:
                    p = t.get("priority","Medium")
                    pc = PRIORITY_COLORS.get(p,"#999")
                    st.markdown(f"""
                    <div class='t-row'>
                      <div class='t-row-title'>{t['description']}</div>
                      <div class='t-chips'>
                        <span class='t-chip' style='background:#1A1A28;color:#888'>👤 {t.get('owner','Unassigned')}</span>
                        <span class='t-chip' style='background:#1A1A28;color:#777'>📅 {t.get('deadline','Not set')}</span>
                        <span class='t-chip' style='background:#1A1A28;color:{pc}'>● {p}</span>
                      </div>
                    </div>""", unsafe_allow_html=True)

                st.download_button("⬇️ Export this meeting JSON", data=json.dumps(r, indent=2), file_name=f"{selected_id}.json", mime="application/json")

        else:
            # Meeting list
            for mtg in meetings:
                r = mtg["result"]
                dt = mtg.get("analyzed_at","")[:16].replace("T"," ")
                src_icons = {"paste":"✏️","teams_vtt":"🎥","teams_txt":"📄"}
                src = src_icons.get(mtg.get("source","paste"),"✏️")
                score = r.get("meeting_quality",{}).get("score",0)
                qc = "#4ADE80" if score >= 67 else "#FBBF24" if score >= 34 else "#F87171"
                ntasks = len(r.get("tasks",[]))
                nrisks = len(r.get("risks",[]))

                col_main, col_btn = st.columns([6,1])
                with col_main:
                    st.markdown(f"""
                    <div class='hist-row'>
                      <div class='hist-title'>{src} &nbsp; {r.get('meeting_title','Meeting')}</div>
                      <div class='hist-meta'>{dt} &nbsp;·&nbsp; {ntasks} tasks &nbsp;·&nbsp; {nrisks} risks &nbsp;·&nbsp; <span style='color:{qc}'>{score}/100</span></div>
                    </div>""", unsafe_allow_html=True)
                with col_btn:
                    if st.button("View", key=f"view_{mtg['id']}"):
                        st.session_state[f"selected_meeting_{gid}"] = mtg["id"]
                        st.rerun()