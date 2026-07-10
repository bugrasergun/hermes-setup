import sqlite3
import json
import time
import requests
import uuid
import task_queue as q
import timeline as tl
from config import LIBRARIAN_DB, OLLAMA_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT, MAX_RETRIES
from schemas import get_timeline_entry_schema

SYSTEM_PROMPT = """You are the Librarian, an advanced knowledge manager observing an interaction between a user and an AI agent. 
Your goal is to extract ONLY atomic information of lasting value from the conversation history.

WRITE an entry IF and ONLY IF the conversation contains:
- A definitive decision made by the user or agent.
- A new discovery, insight, or piece of knowledge.
- A newly identified bug, problem, or root cause.
- A change in project state or configuration.
- A clear preference or pattern established by the user.
- A concrete next step or open task assigned.

DO NOT WRITE (skip) IF:
- It's just short acknowledgments ("ok", "go ahead", "understood").
- Research or brainstorming is ongoing without a clear conclusion.
- The same topic is being discussed repeatedly without new information.
- It's casual/social conversation.

Your output MUST be strictly in JSON format matching the required schema. If you decide to skip, provide a skip_reason."""

def get_librarian_conn():
    conn = sqlite3.connect(LIBRARIAN_DB, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def move_to_dlq(item, error_msg):
    conn = get_librarian_conn()
    try:
        conn.execute("""
            INSERT INTO dead_letter_queue (original_id, profile, session_id, messages_json, error_msg, failed_at, retry_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (item['id'], item['profile'], item['session_id'], item['messages_json'], error_msg, time.time(), item['retry_count']))
        conn.execute("DELETE FROM processing_queue WHERE id = ?", (item['id'],))
        conn.commit()
    finally:
        conn.close()

def update_status(item_id, status, retry_increment=0):
    conn = get_librarian_conn()
    try:
        conn.execute("UPDATE processing_queue SET status = ?, retry_count = retry_count + ? WHERE id = ?", 
                     (status, retry_increment, item_id))
        conn.commit()
    finally:
        conn.close()

def process_queue():
    conn = get_librarian_conn()
    try:
        item = conn.execute("SELECT * FROM processing_queue WHERE status = 'pending' ORDER BY created_at ASC LIMIT 1").fetchone()
    finally:
        conn.close()

    if not item:
        return False

    item_id = item['id']
    import logging
    logging.info(f"Processing queue item {item_id} (Agent: {item['agent_name']}, Trigger: {item['trigger']})")
    update_status(item_id, 'processing')

    try:
        # Build prompt
        messages = json.loads(item['messages_json'])
        context = {
            "trigger": item['trigger'],
            "session_id": item['session_id'],
            "agent_name": item['agent_name'],
            "source": item['source']
        }
        
        last_entry = json.loads(item['last_entry_json']) if item['last_entry_json'] else tl.get_last_entry(item['agent_name'])

        prompt = f"CONTEXT:\n{json.dumps(context, indent=2)}\n\n"
        if last_entry:
            prompt += f"PREVIOUS TIMELINE ENTRY (For continuity):\n{json.dumps(last_entry, indent=2)}\n\n"
        
        prompt += f"MESSAGES TO ANALYZE:\n{json.dumps(messages, indent=2)}"

        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "format": get_timeline_entry_schema(),
            "options": {
                "temperature": 0.1
            },
            "format": "json",
            "stream": False
        }

        response = requests.post(OLLAMA_URL, json=payload, timeout=OLLAMA_TIMEOUT)
        response.raise_for_status()
        
        result_json = response.json()
        content = result_json.get('message', {}).get('content', '')
        
        # Clean markdown code blocks if the model still wrapped it
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        parsed = json.loads(content)
        decision = parsed.get("decision")
        logging.info(f"Ollama decision for item {item_id}: {decision}")
        
        if decision == "write" and parsed.get("entry"):
            entry = parsed["entry"]
            entry["id"] = str(uuid.uuid4())
            entry["agent_id"] = item['agent_name']
            entry["session_id"] = item['session_id']
            entry["source"] = item['source']
            tl.add_entry(entry)
            logging.info(f"Timeline entry written for item {item_id}")
            
        update_status(item_id, 'done')
        
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Failed processing item {item_id}: {error_msg}", exc_info=True)
        retry_count = item['retry_count'] + 1
        if retry_count >= MAX_RETRIES:
            logging.error(f"Item {item_id} reached max retries. Moving to DLQ.")
            move_to_dlq(item, error_msg)
        else:
            logging.info(f"Item {item_id} failed. Retrying later (retry count: {retry_count}).")
            update_status(item_id, 'pending', retry_increment=1)
            
    return True

if __name__ == "__main__":
    while process_queue():
        pass
