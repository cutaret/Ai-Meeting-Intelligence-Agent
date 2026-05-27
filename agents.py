"""
agents.py — Meeting Intelligence Multi-Agent Pipeline
Each agent calls Claude API independently with a focused prompt.
Pipeline: Transcript → Summarizer → TaskExtractor → RiskPredictor → SentimentAnalyzer → FollowUpAgent
"""

import json
import re
import requests
import os
from datetime import datetime

import time

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"
MAX_TOKENS = 2000
RETRY_WAIT = 15  # seconds to wait on rate limit


def _call_llm(system: str, user: str, max_tokens: int = MAX_TOKENS) -> str:
    """Core API caller — connects to Groq for ultra-fast Llama 3 inference.
    Includes automatic retry with backoff for free-tier rate limits."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set")
        
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ]
    }
    
    for attempt in range(3):
        resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
        if resp.status_code == 429:
            # Rate limited — wait and retry
            time.sleep(RETRY_WAIT)
            continue
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    
    # If all retries exhausted, raise the last error
    resp.raise_for_status()
    return ""


def _parse_json(raw: str) -> dict:
    """Strip markdown fences and parse JSON safely."""
    raw = re.sub(r"^```(?:json)?", "", raw.strip(), flags=re.MULTILINE)
    raw = re.sub(r"```$", "", raw.strip(), flags=re.MULTILINE)
    try:
        return json.loads(raw.strip(), strict=False)
    except json.JSONDecodeError:
        return {}


# ──────────────────────────────────────────────────────────────────────────────
# AGENT 1 — SUMMARIZER
# Job: compress the transcript into summary, decisions, open questions
# ──────────────────────────────────────────────────────────────────────────────
SUMMARIZER_SYSTEM = """You are a meeting summarizer agent. Your ONLY job is to extract:
- A 3-5 sentence executive summary
- A list of firm decisions made
- A list of unresolved open questions
Respond ONLY in valid JSON. No markdown, no explanation."""

SUMMARIZER_PROMPT = """Analyze this transcript and return:
{
  "meeting_title": "short inferred title (5-8 words)",
  "date": "extract from transcript or use today: """ + datetime.today().strftime('%Y-%m-%d') + """",
  "attendees": ["name1", "name2"],
  "summary": "3-5 sentence executive summary",
  "key_points": ["bullet 1", "bullet 2", "bullet 3"],
  "decisions": ["firm decision 1", "firm decision 2"],
  "open_questions": ["unresolved question 1"],
  "meeting_quality": {
    "score": 0,
    "has_decisions": true,
    "has_owners": true,
    "has_deadlines": true,
    "note": "one sentence feedback on meeting quality"
  }
}
Rules:
- Only include things explicitly stated in the transcript
- Decisions are things definitively agreed/announced (not discussed, not maybe)
- score: +34 if decisions exist, +33 if all mentioned tasks have owners, +33 if all tasks have deadlines
TRANSCRIPT:
"""


def run_summarizer(transcript: str) -> dict:
    raw = _call_llm(SUMMARIZER_SYSTEM, SUMMARIZER_PROMPT + transcript)
    return _parse_json(raw)


# ──────────────────────────────────────────────────────────────────────────────
# AGENT 2 — TASK EXTRACTOR
# Job: find every "I'll do X by Y" buried in the transcript
# ──────────────────────────────────────────────────────────────────────────────
TASK_SYSTEM = """You are a task extraction agent. Your ONLY job is to find every action item,
commitment, or to-do in a meeting transcript — explicit AND implied.
Respond ONLY in valid JSON. No markdown, no explanation."""

TASK_PROMPT = """Extract all tasks from this transcript and return:
{
  "tasks": [
    {
      "id": "task_1",
      "description": "clear, actionable description of what must be done",
      "owner": "person's first name or 'Unassigned'",
      "deadline": "specific deadline if mentioned, else 'Not set'",
      "priority": "High / Medium / Low",
      "complexity": "High / Medium / Low",
      "category": "Engineering / Design / Management / DevOps / Other",
      "depends_on": "task_id of blocking task, or null",
      "notes": "any extra context from transcript"
    }
  ]
}
Priority rules:
- High = blocks others, has urgent deadline, or explicitly flagged
- Medium = normal sprint work
- Low = nice-to-have, future sprint
Complexity rules:
- High = multi-step, multi-day, involves multiple people
- Low = quick action (send email, update doc, make intro)
TRANSCRIPT:
"""


def run_task_extractor(transcript: str) -> dict:
    raw = _call_llm(TASK_SYSTEM, TASK_PROMPT + transcript, max_tokens=2500)
    return _parse_json(raw)


# ──────────────────────────────────────────────────────────────────────────────
# AGENT 3 — RISK PREDICTOR
# Job: flag what's going to go wrong before it does
# ──────────────────────────────────────────────────────────────────────────────
RISK_SYSTEM = """You are a project risk prediction agent. Given tasks from a meeting,
you identify risks: missing owners, missing deadlines, overloaded people, blockers,
and dependency conflicts.
Respond ONLY in valid JSON. No markdown, no explanation."""

RISK_PROMPT = """Given these tasks and transcript, identify all risks:
{
  "risks": [
    {
      "type": "missing_owner | missing_deadline | overloaded_person | blocker | dependency_conflict | scope_creep",
      "severity": "Critical / High / Medium / Low",
      "description": "specific explanation of the risk",
      "related_task_id": "task_id or null",
      "affected_person": "name or null",
      "recommendation": "one-line suggested action to mitigate"
    }
  ],
  "overloaded_people": [
    {
      "name": "person name",
      "task_count": 0,
      "tasks": ["task description 1", "task description 2"]
    }
  ]
}
Rules:
- Every task with no owner → missing_owner risk (severity: High)
- Every task with no deadline → missing_deadline risk (severity: Medium)
- Person with 3+ tasks → overloaded_person risk (severity: High)
- Task that another task depends on but has no clear completion → dependency_conflict
- Any task where scope seems unclear or expanding → scope_creep
TASKS:
"""


def run_risk_predictor(tasks: list, transcript: str) -> dict:
    task_json = json.dumps(tasks, indent=2)
    prompt = RISK_PROMPT + task_json + "\n\nORIGINAL TRANSCRIPT FOR CONTEXT:\n" + transcript
    raw = _call_llm(RISK_SYSTEM, prompt)
    return _parse_json(raw)


# ──────────────────────────────────────────────────────────────────────────────
# AGENT 4 — SENTIMENT ANALYZER (NEW FEATURE)
# Job: analyze tone, engagement, and speaking patterns per attendee
# ──────────────────────────────────────────────────────────────────────────────
SENTIMENT_SYSTEM = """You are a meeting dynamics and sentiment analysis agent.
You analyze how people communicate in meetings: their tone, participation, confidence,
and potential concerns. Be analytical but fair.
Respond ONLY in valid JSON. No markdown, no explanation."""

SENTIMENT_PROMPT = """Analyze the meeting dynamics and sentiment from this transcript:
{
  "overall_tone": "Productive / Tense / Uncertain / Collaborative / Rushed",
  "meeting_health": "Good / At Risk / Poor",
  "health_reason": "one sentence explanation",
  "speaker_analysis": [
    {
      "name": "speaker name",
      "sentiment": "Confident / Uncertain / Stressed / Neutral / Positive",
      "engagement_level": "High / Medium / Low",
      "speaking_lines": 0,
      "key_contributions": ["contribution 1"],
      "potential_concerns": ["any concern or empty list"],
      "tone_notes": "brief observation about how they communicate"
    }
  ],
  "positive_signals": ["good thing noticed 1", "good thing noticed 2"],
  "warning_signals": ["concern 1", "concern 2"],
  "follow_up_suggestions": ["suggestion for next meeting 1"]
}
Be specific and evidence-based — cite what was actually said.
TRANSCRIPT:
"""


def run_sentiment_analyzer(transcript: str) -> dict:
    raw = _call_llm(SENTIMENT_SYSTEM, SENTIMENT_PROMPT + transcript)
    return _parse_json(raw)


# ──────────────────────────────────────────────────────────────────────────────
# AGENT 5 — FOLLOW-UP AGENT (NEW FEATURE)
# Job: generate personalized follow-up messages for each task owner
# ──────────────────────────────────────────────────────────────────────────────
FOLLOWUP_SYSTEM = """You are a professional follow-up message writer for workplace settings.
You write concise, friendly, actionable Slack/email messages.
Respond ONLY in valid JSON. No markdown, no explanation."""

FOLLOWUP_PROMPT = """Given these tasks, generate follow-up messages for each unique owner:
{
  "follow_ups": [
    {
      "recipient": "person's name",
      "channel": "slack",
      "subject": "brief subject line",
      "message": "the actual message — friendly, professional, 2-4 sentences max",
      "tasks_referenced": ["task description 1"],
      "urgency": "Immediate / This Week / This Sprint"
    }
  ]
}
Rules:
- One message per person (consolidate all their tasks)
- Slack messages: short, use bullet points for tasks
- Reference specific task descriptions and deadlines
- Tone: collegial and direct, not pushy
- Include a clear call-to-action
TASKS (JSON):
"""


def run_followup_agent(tasks: list) -> dict:
    task_json = json.dumps(tasks, indent=2)
    raw = _call_llm(FOLLOWUP_SYSTEM, FOLLOWUP_PROMPT + task_json)
    return _parse_json(raw)


# ──────────────────────────────────────────────────────────────────────────────
# ORCHESTRATOR — runs all agents in sequence and assembles final result
# ──────────────────────────────────────────────────────────────────────────────
def run_pipeline(transcript: str, run_sentiment: bool = True, run_followup: bool = True) -> dict:
    """
    Full multi-agent pipeline. Returns assembled result dict.
    Agents run sequentially; each passes output to next.
    """
    results = {"pipeline_version": "3.0", "agents_run": []}

    # Agent 1: Summarizer
    summary_data = run_summarizer(transcript)
    results.update(summary_data)
    results["agents_run"].append("summarizer")

    # Agent 2: Task Extractor
    task_data = run_task_extractor(transcript)
    results["tasks"] = task_data.get("tasks", [])
    results["agents_run"].append("task_extractor")

    # Agent 3: Risk Predictor (uses task output)
    risk_data = run_risk_predictor(results["tasks"], transcript)
    results["risks"] = risk_data.get("risks", [])
    results["overloaded_people"] = risk_data.get("overloaded_people", [])
    results["agents_run"].append("risk_predictor")

    # Agent 4: Sentiment Analyzer (optional, adds latency)
    if run_sentiment:
        sentiment_data = run_sentiment_analyzer(transcript)
        results["sentiment"] = sentiment_data
        results["agents_run"].append("sentiment_analyzer")

    # Agent 5: Follow-up Agent (optional)
    if run_followup and results["tasks"]:
        followup_data = run_followup_agent(results["tasks"])
        results["follow_ups"] = followup_data.get("follow_ups", [])
        results["agents_run"].append("followup_agent")

    return results