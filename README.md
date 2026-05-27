# 🧠 AI Meeting Intelligence Agent

A highly specialized, multi-agent AI pipeline designed to instantly extract actionable intelligence from meeting transcripts. 

Instead of relying on a single AI prompt (which often leads to dropped tasks and hallucinations), this application uses a **Sequential Multi-Agent Architecture** powered by Llama 3 (via Groq) to independently extract summaries, action items, project risks, and meeting sentiment.

## ✨ Features

- **5-Agent Sequential Pipeline**:
  1. **Summarizer Agent**: Extracts executive summaries and firm decisions.
  2. **Task Extractor Agent**: Identifies action items, assignees, deadlines, and priorities.
  3. **Risk Predictor Agent**: Analyzes tasks for missing owners, missing deadlines, or overloaded team members.
  4. **Sentiment Analyzer Agent**: Evaluates meeting health and speaker engagement.
  5. **Follow-up Agent**: Auto-generates personalized Slack and Email nudges for assigned tasks.
- **Cross-Meeting Memory**: Uses SQLite to persist data, allowing the agent to track team workload and task status across multiple different meetings.
- **Ultra-Fast Inference**: Powered by the Groq API (Llama 3 70B) for near-instantaneous pipeline execution (~3 seconds).
- **One-Click Exports**: Export data directly to Slack, Gmail, Jira (CSV), or Notion (Markdown).

---

## 🚀 Quick Start (Local)

### 1. Clone the repository
```bash
git clone https://github.com/cutaret/Ai-Meeting-Intelligence-Agent.git
cd Ai-Meeting-Intelligence-Agent
```

### 2. Set up your environment
Create a virtual environment and install the dependencies:
```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Add your API Key
Create a `.env` file in the root of the project and add your free [Groq API Key](https://console.groq.com/):
```env
GROQ_API_KEY=gsk_your_api_key_here
```

### 4. Run the app
```bash
streamlit run app_v3.py
```
Open `http://localhost:8501` in your browser.

---

## ☁️ Deployment (Streamlit Community Cloud)

This app is fully compatible with **Streamlit Community Cloud** for free hosting.

1. Push this code to a public GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io/) and connect your repository.
3. Set the Main file path to `app_v3.py`.
4. Click **Deploy**.
5. Once deployed, go to the Streamlit App Settings (bottom right corner) -> **Secrets** and add your Groq API key:
   ```toml
   GROQ_API_KEY = "gsk_your_api_key_here"
   ```

*Note: Streamlit Community Cloud uses ephemeral storage. If the server goes to sleep due to inactivity, your local SQLite `meetings.db` file will be reset.*

---

## 🛠️ Tech Stack
- **Frontend**: Streamlit + Custom Vanilla CSS
- **AI/LLM**: Groq API (`llama-3.3-70b-versatile`)
- **Database**: SQLite
- **Language**: Python 3
