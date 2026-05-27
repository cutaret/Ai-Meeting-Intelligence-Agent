# 🧠 AI Meeting Intelligence Agent

[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-Streamlit_Cloud-FF4B4B?style=for-the-badge&logo=streamlit)](https://ai-meeting-intelligence-agent.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Groq](https://img.shields.io/badge/Powered_by-Groq_LPU-F55036?style=for-the-badge)](https://groq.com)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)

> **Transform raw meeting transcripts into structured, actionable intelligence in under 3 seconds.**

Most meeting tools give you a single AI summary and call it a day. This project takes a fundamentally different approach — it deploys **5 specialized AI agents** in sequence, each with a laser-focused job, producing results that are dramatically more accurate and actionable than any single-prompt solution.

---

## 🎯 The Problem

After every meeting, teams face the same questions:
- *"What did we actually decide?"*
- *"Who's doing what, and by when?"*
- *"Are we overloading someone without realizing it?"*
- *"Did we leave anything unresolved?"*

Traditional note-taking tools either miss critical details or dump everything into an unstructured wall of text. Single-prompt AI summarizers hallucinate tasks that were never assigned and miss the ones that were.

## 💡 The Solution: Multi-Agent Architecture

Instead of asking one AI to do everything (and do it poorly), this system uses a **Sequential Pipeline** of 5 independent agents — each one a specialist:

```
📝 Transcript
    │
    ▼
┌─────────────────┐
│  1. Summarizer   │ → Executive summary, decisions, open questions
└────────┬────────┘
         ▼
┌─────────────────┐
│ 2. Task Extractor│ → Action items with owners, deadlines, priority, complexity
└────────┬────────┘
         ▼
┌─────────────────┐
│ 3. Risk Predictor│ → Missing owners, overloaded people, blockers, scope creep
└────────┬────────┘
         ▼
┌─────────────────┐
│ 4. Sentiment     │ → Speaker engagement, meeting health, warning signals
└────────┬────────┘
         ▼
┌─────────────────┐
│ 5. Follow-up     │ → Auto-generated Slack/email messages per person
└─────────────────┘
```

**Why this works better:** Each agent receives a tailored system prompt and only focuses on its specific job. The Risk Predictor, for example, doesn't even look at the raw transcript first — it analyzes the *output* of the Task Extractor, allowing it to reason at a higher level about project risks.

---

## ✨ Features

### 🔍 Deep Analysis
| Feature | Description |
|---------|-------------|
| **Executive Summary** | 3-5 sentence summary with key points, firm decisions, and open questions |
| **Task Extraction** | Every action item with owner, deadline, priority, complexity, and category |
| **Risk Prediction** | Flags missing owners, missing deadlines, overloaded team members, and blockers |
| **Sentiment Analysis** | Per-speaker engagement levels, tone, confidence, and warning signals |
| **Follow-up Messages** | Ready-to-send Slack/email messages personalized for each task owner |
| **Meeting Quality Score** | 0-100 score based on whether decisions, owners, and deadlines were recorded |

### 🧠 Cross-Meeting Memory
- **SQLite-powered persistence** — tracks tasks across multiple meetings
- **Task Tracker tab** — see all open tasks grouped by owner across every meeting
- **History tab** — browse past meetings with quality scores and summaries
- **Overload detection** — flags when someone has 3+ open tasks across meetings

### 📤 One-Click Exports
- **Slack** — Rich formatted message via webhook
- **Gmail** — Beautiful HTML email with task table
- **Jira CSV** — Import directly into Jira as issues
- **Notion Markdown** — Copy-paste into Notion pages
- **Raw JSON** — Full pipeline output for custom integrations

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- A free [Groq API Key](https://console.groq.com/) (takes 30 seconds to create)

### 1. Clone & Install

```bash
git clone https://github.com/cutaret/Ai-Meeting-Intelligence-Agent.git
cd Ai-Meeting-Intelligence-Agent

python -m venv venv

# Windows
.\venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure

Create a `.env` file in the project root:

```env
GROQ_API_KEY=gsk_your_api_key_here
```

### 3. Run

```bash
streamlit run app_v3.py
```

Open **http://localhost:8501** in your browser → paste a transcript → click **"Run Multi-Agent Analysis"** → done in ~3 seconds! ⚡

---

## ☁️ Deploy to Streamlit Cloud (Free)

This app is production-ready for **Streamlit Community Cloud**:

1. Fork or push this repo to your GitHub account
2. Go to [share.streamlit.io](https://share.streamlit.io/) → **New App**
3. Select your repo → set Main file path to `app_v3.py`
4. Click **Deploy**
5. Go to **Settings → Secrets** and add:
   ```toml
   GROQ_API_KEY = "gsk_your_api_key_here"
   ```

Your app will be live at `https://your-app-name.streamlit.app` 🎉

> **Note:** Streamlit Cloud uses ephemeral storage. The SQLite database resets when the server sleeps due to inactivity.

---

## 🏗️ Architecture

```
├── app_v3.py          # Streamlit UI — tabs, cards, charts, export logic
├── agents.py          # 5-agent pipeline — each agent has its own system prompt
├── database.py        # SQLite layer — meetings, tasks, risks persistence
├── requirements.txt   # Python dependencies
├── .env               # API keys (not committed to git)
└── .gitignore         # Keeps secrets and local files out of version control
```

### How the Pipeline Works

```python
# Each agent is a focused function that calls Groq independently
transcript = "Sarah: James, can you fix the API by Wednesday?..."

# Agent 1: What happened?
summary = run_summarizer(transcript)

# Agent 2: What needs to be done?
tasks = run_task_extractor(transcript)

# Agent 3: What could go wrong? (uses task output, not raw transcript)
risks = run_risk_predictor(tasks, transcript)

# Agent 4: How did people feel?
sentiment = run_sentiment_analyzer(transcript)

# Agent 5: What messages should we send?
followups = run_followup_agent(tasks)
```

---

## 🛠️ Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Frontend** | Streamlit + Custom CSS | Rapid prototyping with premium dark-mode UI |
| **AI/LLM** | Groq API (`llama-3.3-70b-versatile`) | 800 tokens/sec — makes 5-agent pipelines feel instant |
| **Database** | SQLite | Zero-config persistence for cross-meeting memory |
| **Language** | Python 3 | Clean, readable agent orchestration |

---

## 📊 Sample Output

When you paste a meeting transcript, the agent produces:

- **5 action items** with owners, deadlines, priority (High/Medium/Low), and complexity
- **3 risk flags** like "Tom has 4 open tasks — overloaded" or "No deadline set for API fix"
- **Per-speaker sentiment** like "James: Confident, High engagement" or "Tom: Stressed, Low engagement"
- **Ready-to-send follow-ups** like a Slack message to James listing his 2 tasks with deadlines
- **Meeting Quality Score** of 67/100 with breakdown (decisions ✓, owners ✓, deadlines ✗)

---

## 🤝 Contributing

Contributions are welcome! Some ideas for future enhancements:

- **Contradiction Agent** — detect when today's decisions conflict with past meetings
- **Auto-Status Updates** — if someone says "I finished the wireframes", mark past tasks as Done
- **Cross-Meeting Workload Dashboard** — visualize team workload trends over time
- **Voice Input** — integrate Whisper for direct audio-to-analysis

---

## 📄 License

This project is open source under the [MIT License](LICENSE).

---

<p align="center">
  <b>Built with ❤️ by <a href="https://github.com/cutaret">cutaret</a></b>
  <br>
  <sub>Powered by Groq LPU · Llama 3.3 70B · Streamlit</sub>
</p>
