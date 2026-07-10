import json
import os
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
