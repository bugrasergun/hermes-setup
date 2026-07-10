import sqlite3
import time
import os
import task_queue as q
from config import PROFILES, MSG_THRESHOLD, UNGRACEFUL_THRESHOLD

def get_hermes_conn(db_path):
    if not os.path.exists(db_path):
        return None
    uri = f"file:{db_path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def get_unread_messages(conn, profile, session_id):
    last_msg_id = q.get_watermark(profile, session_id)
    return conn.execute("""
        SELECT id, role, content, tool_name, timestamp 
        FROM messages 
        WHERE session_id = ? AND role IN ('user', 'assistant') AND id > ?
        ORDER BY timestamp ASC
    """, (session_id, last_msg_id)).fetchall()

def poll_databases():
    for profile, p_config in PROFILES.items():
        db_path = p_config["db_path"]
        agent_name = p_config["agent_name"]
        
        conn = get_hermes_conn(db_path)
        if not conn:
            continue
            
        try:
            # Tetikleyici 2: Oturum kapandı (ended_at IS NOT NULL)
            closed_sessions = conn.execute("""
                SELECT id, source, end_reason, ended_at 
                FROM sessions 
                WHERE ended_at IS NOT NULL
            """).fetchall()
            
            for session in closed_sessions:
                s_id = session['id']
                source = session['source']
                unread = get_unread_messages(conn, profile, s_id)
                if unread:
                    q.enqueue_messages(profile, agent_name, s_id, source, "session_close", unread)
                    q.mark_watermark(profile, s_id, unread[-1]['id'], "session_close")

            # Aktif oturumları bul
            active_sessions = conn.execute("""
                SELECT s.id, s.source, MAX(m.timestamp) as last_msg_ts
                FROM sessions s 
                JOIN messages m ON s.id = m.session_id
                WHERE s.ended_at IS NULL
                GROUP BY s.id
            """).fetchall()

            now_ts = time.time()

            for session in active_sessions:
                s_id = session['id']
                source = session['source']
                last_msg_ts = session['last_msg_ts']
                
                unread = get_unread_messages(conn, profile, s_id)
                if not unread:
                    continue
                
                # Tetikleyici 1: Mesaj sayısı
                if len(unread) >= MSG_THRESHOLD:
                    q.enqueue_messages(profile, agent_name, s_id, source, "message_count", unread)
                    q.mark_watermark(profile, s_id, unread[-1]['id'], "message_count")
                    continue
                
                # Tetikleyici 3: Ungraceful close (Zaman aşımı)
                if (now_ts - last_msg_ts) > (UNGRACEFUL_THRESHOLD * 60):
                    q.enqueue_messages(profile, agent_name, s_id, source, "ungraceful_close", unread)
                    q.mark_watermark(profile, s_id, unread[-1]['id'], "ungraceful_close")
                    
        except Exception as e:
            import logging
            logging.error(f"Error reading {profile} db: {e}", exc_info=True)
        finally:
            conn.close()

if __name__ == "__main__":
    poll_databases()
