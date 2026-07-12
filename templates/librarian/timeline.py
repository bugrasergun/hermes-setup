import json
import os
import datetime
from collections import Counter
from config import TIMELINE_PATH

def get_timeline():
    if not os.path.exists(TIMELINE_PATH):
        # Create base timeline
        return {
            "schema_version": "v1",
            "date": "",
            "entries": [],
            "agent_snapshots": {}
        }
    with open(TIMELINE_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_timeline(timeline):
    os.makedirs(os.path.dirname(TIMELINE_PATH), exist_ok=True)
    tmp_path = TIMELINE_PATH + ".tmp"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(timeline, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, TIMELINE_PATH)

def get_last_entry(agent_name):
    tl = get_timeline()
    for entry in reversed(tl.get("entries", [])):
        if entry.get("agent_id") == agent_name:
            return entry
    return None

def add_entry(entry):
    tl = get_timeline()
    tl.setdefault("entries", []).append(entry)
    save_timeline(tl)

def update_agent_snapshot(agent_name, entry, session_id, source):
    """Update agent_snapshot fields every time a new entry is written.

    Updates:
    - last_seen: current UTC timestamp
    - last_session_id: the session that produced this entry
    - source: where the session came from (telegram, antigravity-ide, etc.)
    - active_topics: top tags from all current entries (max 8)
    - pending_items: summaries of entries still open/pending
    """
    tl = get_timeline()
    snapshots = tl.setdefault("agent_snapshots", {})
    snap = snapshots.setdefault(agent_name, {})

    # last_seen & session info
    snap["last_seen"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    snap["last_session_id"] = session_id
    snap["source"] = source

    # active_topics — aggregate tags from all current entries for this agent
    all_entries = tl.get("entries", [])
    tag_counts = Counter()
    pending = []
    for e in all_entries:
        if e.get("agent_id") != agent_name:
            continue
        for tag in e.get("tags", []):
            tag_counts[tag] += 1
        if e.get("status") in ("open", "pending"):
            pending.append(e.get("summary", ""))

    snap["active_topics"] = [tag for tag, _ in tag_counts.most_common(8)]
    snap["pending_items"] = pending

    tl["agent_snapshots"] = snapshots
    save_timeline(tl)

