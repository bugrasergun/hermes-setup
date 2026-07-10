import json

TIMELINE_ENTRY_SCHEMA = {
    "type": "object",
    "properties": {
        "$schema": {"type": "string"},
        "decision": {"type": "string", "enum": ["write", "skip"]},
        "skip_reason": {"type": ["string", "null"]},
        "entry": {
            "type": ["object", "null"],
            "properties": {
                "id": {"type": "string"},
                "timestamp": {"type": "string"},
                "agent_id": {"type": "string"},
                "session_id": {"type": "string"},
                "source": {"type": "string"},
                "project": {"type": ["string", "null"]},
                "type": {"type": "string", "enum": ["decision", "discovery", "problem", "pattern", "next_step", "milestone"]},
                "summary": {"type": "string"},
                "detail": {"type": ["string", "null"]},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "status": {"type": "string", "enum": ["open", "resolved", "pending"]}
            },
            "required": ["id", "timestamp", "agent_id", "session_id", "source", "type", "summary", "tags", "status"]
        }
    },
    "required": ["$schema", "decision", "skip_reason", "entry"]
}

def get_timeline_entry_schema():
    return TIMELINE_ENTRY_SCHEMA
