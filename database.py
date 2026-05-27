"""
database.py — SQLite persistence for Meeting Intelligence Agent
Stores meetings, tasks, risks across sessions for cross-meeting memory.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional

DB_PATH = os.getenv("DB_PATH", "meetings.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS meetings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            date        TEXT,
            attendees   TEXT,  -- JSON array
            summary     TEXT,
            raw_json    TEXT,  -- full pipeline output
            quality_score INTEGER DEFAULT 0,
            created_at  TEXT DEFAULT (datetime('now'))
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
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id  INTEGER REFERENCES meetings(id),
            type        TEXT,
            severity    TEXT,
            description TEXT,
            related_task_id TEXT,
            recommendation TEXT,
            created_at  TEXT DEFAULT (datetime('now'))
        )
    """)

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
        SELECT t.owner, t.description, t.deadline, t.priority, t.status, m.title as meeting_title
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
