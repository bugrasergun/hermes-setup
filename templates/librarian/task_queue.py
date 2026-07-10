import sqlite3
import json
import time
from config import LIBRARIAN_DB

def get_librarian_conn():
    conn = sqlite3.connect(LIBRARIAN_DB, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def enqueue_messages(profile, agent_name, session_id, source, trigger, messages, last_entry=None):
    if not messages:
        return

    messages_json = json.dumps([dict(m) for m in messages])
    last_entry_json = json.dumps(last_entry) if last_entry else None
    
    conn = get_librarian_conn()
    try:
        conn.execute("""
            INSERT INTO processing_queue 
            (profile, agent_name, session_id, source, trigger, messages_json, last_entry_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (profile, agent_name, session_id, source, trigger, messages_json, last_entry_json, time.time()))
        conn.commit()
    finally:
        conn.close()

def mark_watermark(profile, session_id, last_msg_id, trigger_type):
    conn = get_librarian_conn()
    try:
        conn.execute("""
            INSERT INTO librarian_watermarks (profile, session_id, last_msg_id, last_processed_at, trigger_type)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(profile, session_id) DO UPDATE SET 
                last_msg_id = excluded.last_msg_id,
                last_processed_at = excluded.last_processed_at,
                trigger_type = excluded.trigger_type
        """, (profile, session_id, last_msg_id, time.time(), trigger_type))
        conn.commit()
    finally:
        conn.close()

def get_watermark(profile, session_id):
    conn = get_librarian_conn()
    try:
        row = conn.execute("SELECT last_msg_id FROM librarian_watermarks WHERE profile = ? AND session_id = ?", (profile, session_id)).fetchone()
        return row['last_msg_id'] if row else 0
    finally:
        conn.close()
