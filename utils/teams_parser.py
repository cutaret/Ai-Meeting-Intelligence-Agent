"""
teams_parser.py — Parse Microsoft Teams transcript exports.
Supports .vtt (WebVTT) and .txt (copy-pasted) formats.
Returns a clean transcript string and metadata about speakers.
"""

import re
from typing import Tuple


def _parse_vtt(content: str) -> Tuple[str, dict]:
    """
    Parse a WebVTT file from Microsoft Teams.

    Teams VTT format (two common variants):

    Variant A (voice tags):
        00:00:01.920 --> 00:00:04.560
        <v Speaker Name>Hello everyone, let's start.

    Variant B (speaker on separate line):
        00:00:01.920 --> 00:00:04.560
        Speaker Name
        Hello everyone, let's start.
    """
    lines = content.splitlines()
    utterances = []
    speakers_seen = set()
    current_speaker = None
    current_text = []
    timestamp_re = re.compile(r"\d{2}:\d{2}:\d{2}\.\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}")
    voice_tag_re = re.compile(r"<v\s+([^>]+)>(.+)")

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip WEBVTT header, NOTE lines, empty lines, and numeric cue IDs
        if (
            not line
            or line.upper().startswith("WEBVTT")
            or line.upper().startswith("NOTE")
            or line.isdigit()
        ):
            i += 1
            continue

        # Timestamp line — start of a new cue
        if timestamp_re.match(line):
            i += 1
            if i >= len(lines):
                break

            next_line = lines[i].strip()

            # Check for voice tag variant: <v Speaker>text
            voice_match = voice_tag_re.match(next_line)
            if voice_match:
                speaker = voice_match.group(1).strip()
                text = voice_match.group(2).strip()
                # Remove closing </v> if present
                text = re.sub(r"</v>$", "", text).strip()
                speakers_seen.add(speaker)
                utterances.append(f"{speaker}: {text}")
                i += 1
                continue

            # Check for speaker-on-separate-line variant
            # If the next line after this one exists and isn't a timestamp or empty,
            # then this line is likely the speaker name
            if i + 1 < len(lines):
                following = lines[i + 1].strip()
                if (
                    following
                    and not timestamp_re.match(following)
                    and not following.isdigit()
                    and not following.upper().startswith("WEBVTT")
                ):
                    # Heuristic: if next_line has no spaces or is a short name-like string
                    # and the following line looks like dialogue, treat next_line as speaker
                    if len(next_line.split()) <= 5 and not next_line.endswith((".","!","?",",")):
                        speaker = next_line
                        text = following
                        speakers_seen.add(speaker)
                        utterances.append(f"{speaker}: {text}")
                        i += 2
                        continue

            # Fallback: treat as continuation text
            if next_line:
                if current_speaker:
                    utterances.append(f"{current_speaker}: {next_line}")
                else:
                    utterances.append(next_line)
            i += 1
            continue

        i += 1

    transcript = "\n".join(utterances)
    meta = {
        "format": "vtt",
        "utterances": len(utterances),
        "speakers_detected": sorted(speakers_seen) if speakers_seen else [],
    }
    return transcript, meta


def _parse_txt(content: str) -> Tuple[str, dict]:
    """
    Parse a plain text transcript (copy-pasted from Teams or manual).

    Expected format:
        Speaker Name: what they said
        Another Speaker: their response

    Or freeform text (returned as-is with basic cleanup).
    """
    lines = content.strip().splitlines()
    speakers_seen = set()
    utterances = 0

    # Detect speaker lines (Name: text pattern)
    speaker_re = re.compile(r"^([A-Za-z][A-Za-z\s.'-]{0,40}):\s+(.+)")

    for line in lines:
        match = speaker_re.match(line.strip())
        if match:
            speaker = match.group(1).strip()
            # Filter out things that look like timestamps or metadata, not names
            if not re.match(r"^\d", speaker) and len(speaker) < 40:
                speakers_seen.add(speaker)
                utterances += 1

    # Clean up the text — remove excessive blank lines
    cleaned = re.sub(r"\n{3,}", "\n\n", content.strip())

    meta = {
        "format": "txt",
        "utterances": utterances if utterances else len([l for l in lines if l.strip()]),
        "speakers_detected": sorted(speakers_seen) if speakers_seen else [],
    }
    return cleaned, meta


def detect_and_parse(filename: str, content: str) -> Tuple[str, dict]:
    """
    Auto-detect format and parse transcript.

    Args:
        filename: Original filename (used to detect format).
        content: Raw file content as string.

    Returns:
        (transcript_text, metadata_dict)
        metadata keys: format, utterances, speakers_detected
    """
    if filename.lower().endswith(".vtt") or "WEBVTT" in content[:50]:
        return _parse_vtt(content)
    else:
        return _parse_txt(content)
