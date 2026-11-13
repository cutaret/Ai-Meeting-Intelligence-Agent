"""
database.py — SQLite persistence for Meeting Intelligence Agent
Stores meetings, tasks, risks across sessions for cross-meeting memory.
Includes automatic demo seeding for ephemeral cloud deployments (Streamlit Cloud).
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Optional

DB_PATH = os.getenv("DB_PATH", "meetings.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _seed_demo_data(conn: sqlite3.Connection):
    """Populate initial demo meetings, tasks, and risks if the database is empty."""
    c = conn.cursor()
    count = c.execute("SELECT COUNT(*) FROM meetings").fetchone()[0]
    if count > 0:
        return

    today = datetime.today()
    date_m1 = (today - timedelta(days=3)).strftime("%Y-%m-%d")
    date_m2 = (today - timedelta(days=1)).strftime("%Y-%m-%d")

    demo_meetings = [
        {
            "meeting_title": "Q4 AI Platform Sprint Planning",
            "date": date_m1,
            "attendees": ["Sarah (PM)", "James (Backend)", "Tom (Infra)", "Priya (Frontend)"],
            "summary": (
                "The team aligned on Q4 latency targets for the multi-agent pipeline and decided to migrate "
                "the vector index to HNSW by Friday. Tom took ownership of both the vector migration and Redis "
                "rate-limiting middleware, while James will finalize the OAuth2 refresh flow. Pricing tier rate "
                "limits remain unresolved pending finance sign-off."
            ),
            "key_points": [
                "Target p95 pipeline latency set to under 2.5 seconds.",
                "Vector search migration prioritized over dashboard redesign.",
                "Redis rate-limiting required before public beta traffic spikes."
            ],
            "decisions": [
                "Migrate vector database index to HNSW before Friday feature freeze.",
                "Defer custom webhook retry UI to Sprint 14."
            ],
            "open_questions": [
                "What is the exact burst rate limit for free-tier workspaces?",
                "Do we need a dedicated staging cluster for load testing?"
            ],
            "meeting_quality": {
                "score": 78,
                "has_decisions": True,
                "has_owners": True,
                "has_deadlines": True,
                "feedback": "Clear owners and decisions recorded; two open infrastructure questions remain."
            },
            "tasks": [
                {
                    "id": "task_1",
                    "description": "Migrate vector database index to HNSW for sub-50ms retrieval",
                    "owner": "Tom",
                    "deadline": "Friday",
                    "priority": "High",
                    "complexity": "High",
                    "category": "Engineering",
                    "status": "Open"
                },
                {
                    "id": "task_2",
                    "description": "Configure Redis rate-limiting middleware for public API endpoints",
                    "owner": "Tom",
                    "deadline": "Thursday",
                    "priority": "High",
                    "complexity": "Medium",
                    "category": "Engineering",
                    "status": "Open"
                },
                {
                    "id": "task_3",
                    "description": "Finalize OAuth2 token refresh flow with mobile client team",
                    "owner": "James",
                    "deadline": "Wednesday",
                    "priority": "Medium",
                    "complexity": "Medium",
                    "category": "Engineering",
                    "status": "Done"
                },
                {
                    "id": "task_4",
                    "description": "Update OpenAPI/Swagger documentation for v2 webhook payloads",
                    "owner": "Priya",
                    "deadline": "Next Monday",
                    "priority": "Low",
                    "complexity": "Low",
                    "category": "Documentation",
                    "status": "Open"
                }
            ],
            "risks": [
                {
                    "type": "Resource Bottleneck",
                    "severity": "High",
                    "description": "Tom is assigned two high-priority infrastructure tasks due within 48 hours.",
                    "related_task_id": "task_1",
                    "recommendation": "Reassign Redis rate-limiting configuration to James once OAuth2 is merged."
                },
                {
                    "type": "Unresolved Dependency",
                    "severity": "Medium",
                    "description": "Free-tier burst rate limits are not finalized, which may block Redis middleware thresholds.",
                    "related_task_id": "task_2",
                    "recommendation": "Use a configurable environment variable default (60 req/min) until PM confirms."
                }
            ],
            "sentiment": {
                "overall_tone": "Focused & Constructive",
                "meeting_health": "Healthy (82/100)",
                "speakers": [
                    {"name": "Sarah", "tone": "Decisive", "engagement": "High", "confidence": "High"},
                    {"name": "James", "tone": "Confident", "engagement": "High", "confidence": "High"},
                    {"name": "Tom", "tone": "Stressed", "engagement": "Medium", "confidence": "Medium"},
                    {"name": "Priya", "tone": "Collaborative", "engagement": "Medium", "confidence": "High"}
                ]
            },
            "followups": [
                {
                    "owner": "Tom",
                    "slack_message": "Hey Tom! Following up from Sprint Planning: you're down for the HNSW vector migration (due Friday) and Redis rate-limiting middleware (due Thursday). Let Sarah know if you need to offload Redis."
                },
                {
                    "owner": "James",
                    "slack_message": "Hi James, quick recap: please wrap up the OAuth2 token refresh flow with the mobile team by Wednesday."
                }
            ]
        },
        {
            "meeting_title": "Production Release Readiness & Security Sync",
            "date": date_m2,
            "attendees": ["Sarah (PM)", "Tom (Infra)", "James (Backend)", "Elena (SecOps)"],
            "summary": (
                "Elena reviewed the pre-launch security audit and flagged two mandatory fixes before Monday's "
                "production cutover: rotating AWS IAM keys and patching a legacy reporting endpoint. Tom was "
                "assigned IAM key rotation and Prometheus alerting, pushing his active workload to 4 open tasks."
            ),
            "key_points": [
                "Production launch remains scheduled for Monday at 9:00 AM UTC.",
                "AWS IAM key rotation and KMS encryption enforcement are launch blockers.",
                "Prometheus latency alerts needed to monitor Groq API token throughput."
            ],
            "decisions": [
                "Gate Monday's production deployment on SecOps sign-off for IAM rotation and SQL patch.",
                "Enable automatic model fallback to Llama 3.1 8B on HTTP 429 responses."
            ],
            "open_questions": [
                "Who is on primary PagerDuty rotation for Monday's launch window?"
            ],
            "meeting_quality": {
                "score": 88,
                "has_decisions": True,
                "has_owners": True,
                "has_deadlines": False,
                "feedback": "Strong security action items, though Prometheus alerting lacks a firm deadline."
            },
            "tasks": [
                {
                    "id": "task_1",
                    "description": "Rotate production AWS IAM keys and enforce KMS encryption",
                    "owner": "Tom",
                    "deadline": "Tomorrow 5 PM",
                    "priority": "High",
                    "complexity": "Medium",
                    "category": "Security",
                    "status": "Open"
                },
                {
                    "id": "task_2",
                    "description": "Set up Prometheus alerts for Groq API latency spikes",
                    "owner": "Tom",
                    "deadline": "Not set",
                    "priority": "Medium",
                    "complexity": "Low",
                    "category": "DevOps",
                    "status": "Open"
                },
                {
                    "id": "task_3",
                    "description": "Patch parameterized query validation in legacy reporting endpoint",
                    "owner": "James",
                    "deadline": "Thursday EOD",
                    "priority": "High",
                    "complexity": "Medium",
                    "category": "Security",
                    "status": "In Progress"
                },
                {
                    "id": "task_4",
                    "description": "Draft customer release notes for multi-agent analytics launch",
                    "owner": "Sarah",
                    "deadline": "Friday",
                    "priority": "Medium",
                    "complexity": "Low",
                    "category": "Product",
                    "status": "Open"
                }
            ],
            "risks": [
                {
                    "type": "Overloaded Owner",
                    "severity": "Critical",
                    "description": "Tom now has 4 open tasks across active sprints, including launch-blocking IAM rotation.",
                    "related_task_id": "task_1",
                    "recommendation": "Immediately hand off Prometheus alert configuration to Elena or James."
                },
                {
                    "type": "Missing Deadline",
                    "severity": "High",
                    "description": "No deadline set for Prometheus latency alerts prior to Monday launch.",
                    "related_task_id": "task_2",
                    "recommendation": "Assign a firm Friday 3 PM deadline for observability readiness."
                }
            ],
            "sentiment": {
                "overall_tone": "Urgent & Focused",
                "meeting_health": "Attention Needed (74/100)",
                "speakers": [
                    {"name": "Elena", "tone": "Direct", "engagement": "High", "confidence": "High"},
                    {"name": "Tom", "tone": "Overwhelmed", "engagement": "Low", "confidence": "Medium"},
                    {"name": "James", "tone": "Proactive", "engagement": "High", "confidence": "High"},
                    {"name": "Sarah", "tone": "Organized", "engagement": "High", "confidence": "High"}
                ]
            },
            "followups": [
                {
                    "owner": "Tom",
                    "slack_message": "Hi Tom, from today's Security Sync: rotating production AWS IAM keys is due Tomorrow at 5 PM, plus setting up Prometheus alerts. Flagging that you now have 4 open tasks across meetings."
                },
                {
                    "owner": "James",
                    "slack_message": "Hey James, please have the parameterized query patch on the legacy reporting endpoint ready for Elena's review by Thursday EOD."
                }
            ]
        }
    ]

    for data in demo_meetings:
        attendees_json = json.dumps(data.get("attendees", []))
        score = data.get("meeting_quality", {}).get("score", 0)

        c.execute("""
            INSERT INTO meetings (title, date, attendees, summary, raw_json, quality_score)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data.get("meeting_title", "Untitled Meeting"),
            data.get("date", today.strftime("%Y-%m-%d")),
            attendees_json,
            data.get("summary", ""),
            json.dumps(data),
            score,
        ))
        meeting_id = c.lastrowid

        for t in data.get("tasks", []):
            c.execute("""
                INSERT INTO tasks (meeting_id, task_ref, description, owner, deadline, priority, complexity, category, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                meeting_id,
                t.get("id", ""),
                t.get("description", ""),
                t.get("owner", "Unassigned"),
                t.get("deadline", "Not set"),
                t.get("priority", "Medium"),
                t.get("complexity", "Medium"),
                t.get("category", "Other"),
                t.get("status", "Open"),
            ))

        for r in data.get("risks", []):
            c.execute("""
                INSERT INTO risks (meeting_id, type, severity, description, related_task_id, recommendation)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                meeting_id,
                r.get("type", ""),
                r.get("severity", "Medium"),
                r.get("description", ""),
                r.get("related_task_id", ""),
                r.get("recommendation", ""),
            ))


def init_db():
    """Create tables if they don't exist and seed demo data when empty."""
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS meetings (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            title         TEXT NOT NULL,
            date          TEXT,
            attendees     TEXT,  -- JSON array
            summary       TEXT,
            raw_json      TEXT,  -- full pipeline output
            quality_score INTEGER DEFAULT 0,
            created_at    TEXT DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id  INTEGER REFERENCES meetings(id),
            task_ref    TEXT,   -- original task_id from pipeline (task_1, etc.)
            description TEXT NOT NULL,
            owner       TEXT DEFAULT 'Unassigned',
            deadline    TEXT DEFAULT 'Not set',
            priority    TEXT DEFAULT 'Medium',
            complexity  TEXT DEFAULT 'Medium',
            category    TEXT DEFAULT 'Other',
            status      TEXT DEFAULT 'Open',  -- Open / In Progress / Done / Blocked
            created_at  TEXT DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS risks (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id      INTEGER REFERENCES meetings(id),
            type            TEXT,
            severity        TEXT,
            description     TEXT,
            related_task_id TEXT,
            recommendation  TEXT,
            created_at      TEXT DEFAULT (datetime('now'))
        )
    """)

    _seed_demo_data(conn)

    conn.commit()
    conn.close()


def save_meeting(data: dict) -> int:
    """Save full pipeline result; returns new meeting ID."""
    init_db()
    conn = get_conn()
    c = conn.cursor()

    attendees_json = json.dumps(data.get("attendees", []))
    score = data.get("meeting_quality", {}).get("score", 0)

    c.execute("""
        INSERT INTO meetings (title, date, attendees, summary, raw_json, quality_score)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data.get("meeting_title", "Untitled Meeting"),
        data.get("date", datetime.today().strftime("%Y-%m-%d")),
        attendees_json,
        data.get("summary", ""),
        json.dumps(data),
        score,
    ))
    meeting_id = c.lastrowid

    # Save tasks
    for t in data.get("tasks", []):
        c.execute("""
            INSERT INTO tasks (meeting_id, task_ref, description, owner, deadline, priority, complexity, category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            meeting_id,
            t.get("id", ""),
            t.get("description", ""),
            t.get("owner", "Unassigned"),
            t.get("deadline", "Not set"),
            t.get("priority", "Medium"),
            t.get("complexity", "Medium"),
            t.get("category", "Other"),
        ))

    # Save risks
    for r in data.get("risks", []):
        c.execute("""
            INSERT INTO risks (meeting_id, type, severity, description, related_task_id, recommendation)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            meeting_id,
            r.get("type", ""),
            r.get("severity", "Medium"),
            r.get("description", ""),
            r.get("related_task_id", ""),
            r.get("recommendation", ""),
        ))

    conn.commit()
    conn.close()
    return meeting_id


def get_all_meetings() -> list:
    """Return all meetings ordered by most recent."""
    init_db()
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, title, date, attendees, summary, quality_score, created_at FROM meetings ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_meeting_by_id(meeting_id: int) -> Optional[dict]:
    """Return full pipeline JSON for a meeting."""
    init_db()
    conn = get_conn()
    row = conn.execute("SELECT raw_json FROM meetings WHERE id = ?", (meeting_id,)).fetchone()
    conn.close()
    if row:
        return json.loads(row["raw_json"])
    return None


def get_open_tasks_by_owner() -> dict:
    """Return dict of owner → [tasks] for all open tasks across all meetings."""
    init_db()
    conn = get_conn()
    rows = conn.execute("""
        SELECT t.id, t.owner, t.description, t.deadline, t.priority, t.status, m.title as meeting_title
        FROM tasks t
        JOIN meetings m ON t.meeting_id = m.id
        WHERE t.status != 'Done'
        ORDER BY t.owner, t.priority DESC
    """).fetchall()
    conn.close()

    result = {}
    for row in rows:
        owner = row["owner"]
        if owner not in result:
            result[owner] = []
        result[owner].append(dict(row))
    return result


def update_task_status(task_id: int, status: str):
    """Update task status: Open / In Progress / Done / Blocked."""
    init_db()
    conn = get_conn()
    conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
    conn.commit()
    conn.close()


def get_stats() -> dict:
    """High-level stats for dashboard."""
    init_db()
    conn = get_conn()
    total_meetings = conn.execute("SELECT COUNT(*) FROM meetings").fetchone()[0]
    total_tasks = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    open_tasks = conn.execute("SELECT COUNT(*) FROM tasks WHERE status = 'Open'").fetchone()[0]
    done_tasks = conn.execute("SELECT COUNT(*) FROM tasks WHERE status = 'Done'").fetchone()[0]
    high_risks = conn.execute("SELECT COUNT(*) FROM risks WHERE severity IN ('Critical','High')").fetchone()[0]
    avg_score = conn.execute("SELECT AVG(quality_score) FROM meetings").fetchone()[0]
    conn.close()

    return {
        "total_meetings": total_meetings,
        "total_tasks": total_tasks,
        "open_tasks": open_tasks,
        "done_tasks": done_tasks,
        "high_risks": high_risks,
        "avg_quality_score": round(avg_score or 0, 1),
    }