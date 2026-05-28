"""
storage.py — JSON-file-based storage for groups and meetings.
Groups and their members persist in data/groups.json.
Meeting results are saved as individual JSON files under data/meetings/.
"""

import json
import os
import uuid
from datetime import datetime
from typing import Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
GROUPS_FILE = os.path.join(DATA_DIR, "groups.json")
MEETINGS_DIR = os.path.join(DATA_DIR, "meetings")


def _ensure_dirs():
    """Create data directories if they don't exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(MEETINGS_DIR, exist_ok=True)


# ─────────────────────────────────────────────
# GROUPS
# ─────────────────────────────────────────────

def load_groups() -> dict:
    """Return dict of {group_id: group_data}."""
    _ensure_dirs()
    if not os.path.exists(GROUPS_FILE):
        return {}
    try:
        with open(GROUPS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_groups(groups: dict):
    """Persist the full groups dict to disk."""
    _ensure_dirs()
    with open(GROUPS_FILE, "w", encoding="utf-8") as f:
        json.dump(groups, f, indent=2, ensure_ascii=False)


def create_group(name: str, description: str = "") -> str:
    """Create a new group. Returns the new group ID."""
    groups = load_groups()
    gid = str(uuid.uuid4())[:8]
    groups[gid] = {
        "id": gid,
        "name": name,
        "description": description,
        "members": [],
        "created_at": datetime.now().isoformat(),
    }
    save_groups(groups)
    return gid


def update_group_members(group_id: str, members: list):
    """Replace the member list for a group."""
    groups = load_groups()
    if group_id in groups:
        groups[group_id]["members"] = members
        save_groups(groups)


def delete_group(group_id: str):
    """Delete a group and all its meetings."""
    groups = load_groups()
    groups.pop(group_id, None)
    save_groups(groups)
    # Also remove meeting files belonging to this group
    for fname in os.listdir(MEETINGS_DIR):
        fpath = os.path.join(MEETINGS_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                m = json.load(f)
            if m.get("group_id") == group_id:
                os.remove(fpath)
        except Exception:
            pass


# ─────────────────────────────────────────────
# MEETINGS
# ─────────────────────────────────────────────

def save_meeting_result(
    group_id: str,
    group_name: str,
    transcript: str,
    result: dict,
    source: str = "paste",
) -> str:
    """Save a meeting analysis result. Returns the meeting ID."""
    _ensure_dirs()
    meeting_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + str(uuid.uuid4())[:6]
    meeting = {
        "id": meeting_id,
        "group_id": group_id,
        "group_name": group_name,
        "transcript": transcript,
        "result": result,
        "source": source,
        "analyzed_at": datetime.now().isoformat(),
    }
    fpath = os.path.join(MEETINGS_DIR, f"{meeting_id}.json")
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(meeting, f, indent=2, ensure_ascii=False)
    return meeting_id


def get_meetings_for_group(group_id: str) -> list:
    """Return all meetings for a group, newest first."""
    _ensure_dirs()
    meetings = []
    for fname in os.listdir(MEETINGS_DIR):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(MEETINGS_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                m = json.load(f)
            if m.get("group_id") == group_id:
                meetings.append(m)
        except Exception:
            pass
    # Sort newest first
    meetings.sort(key=lambda m: m.get("analyzed_at", ""), reverse=True)
    return meetings


def get_meeting_by_id(meeting_id: str) -> Optional[dict]:
    """Return a single meeting dict by ID, or None."""
    _ensure_dirs()
    fpath = os.path.join(MEETINGS_DIR, f"{meeting_id}.json")
    if os.path.exists(fpath):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    # Fallback: scan all files (in case ID doesn't match filename)
    for fname in os.listdir(MEETINGS_DIR):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(MEETINGS_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                m = json.load(f)
            if m.get("id") == meeting_id:
                return m
        except Exception:
            pass
    return None
