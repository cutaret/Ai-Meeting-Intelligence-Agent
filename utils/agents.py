"""
agents.py (utils) — Wrapper around the main agents pipeline.
Bridges app_v3's group/member-aware interface with the existing
Groq-powered multi-agent pipeline in the root agents.py.
"""

import os
import sys

# Ensure root project dir is importable
_root = os.path.dirname(os.path.dirname(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)

import agents as pipeline  # the root-level agents.py


def _build_member_context(members: list) -> str:
    """Build a team member context block to prepend to the transcript."""
    if not members:
        return ""
    lines = ["[TEAM CONTEXT — use this to correctly attribute tasks and flag role mismatches]"]
    for m in members:
        name = m.get("name", "")
        role = m.get("role", "")
        notes = m.get("notes", "")
        parts = [name]
        if role:
            parts.append(f"Role: {role}")
        if notes:
            parts.append(f"Notes: {notes}")
        lines.append("  - " + " | ".join(parts))
    lines.append("[END TEAM CONTEXT]\n")
    return "\n".join(lines)


def _extract_member_activity(result: dict, members: list) -> list:
    """
    Build member_activity list by cross-referencing team members
    with the analysis results (tasks, attendees).
    """
    if not members:
        return []

    attendees = [a.lower() for a in result.get("attendees", [])]
    tasks = result.get("tasks", [])

    activity = []
    for m in members:
        name = m.get("name", "")
        name_lower = name.lower()

        # Check if they spoke (appeared in attendees list)
        spoke = any(name_lower in a or a in name_lower for a in attendees)

        # Count tasks assigned to them
        task_count = sum(
            1 for t in tasks
            if name_lower in t.get("owner", "").lower()
        )

        activity.append({
            "name": name,
            "role": m.get("role", ""),
            "spoke": spoke,
            "tasks_assigned": task_count,
        })

    return activity


def analyse_meeting(transcript: str, members: list, api_key: str) -> dict:
    """
    Run the full multi-agent pipeline on a transcript.

    Args:
        transcript: The meeting transcript text.
        members: List of team member dicts [{name, role, notes}, ...].
        api_key: Groq API key (set into env for the pipeline).

    Returns:
        Assembled result dict with tasks, risks, summary, quality, member_activity, etc.
    """
    # Set the API key for the pipeline
    os.environ["GROQ_API_KEY"] = api_key

    # Prepend team context so the LLM knows who's who
    member_context = _build_member_context(members)
    enriched_transcript = member_context + transcript

    # Run the existing multi-agent pipeline
    result = pipeline.run_pipeline(enriched_transcript)

    # Add member activity analysis
    result["member_activity"] = _extract_member_activity(result, members)

    return result
