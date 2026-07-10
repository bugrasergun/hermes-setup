-- Hangi mesajların işlendiğini takip eder
CREATE TABLE IF NOT EXISTS librarian_watermarks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    profile     TEXT    NOT NULL,
    session_id  TEXT    NOT NULL,
    last_msg_id INTEGER NOT NULL,
    last_processed_at REAL NOT NULL,
    trigger_type TEXT,
    UNIQUE(profile, session_id)
);

-- FIFO işlem kuyruğu
CREATE TABLE IF NOT EXISTS processing_queue (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    profile     TEXT    NOT NULL,
    agent_name  TEXT    NOT NULL,
    session_id  TEXT    NOT NULL,
    source      TEXT    NOT NULL,
    trigger     TEXT    NOT NULL,
    messages_json TEXT  NOT NULL,
    last_entry_json TEXT,
    created_at  REAL    NOT NULL,
    status      TEXT    DEFAULT 'pending',
    retry_count INTEGER DEFAULT 0
);

-- Başarısız işlemler (Dead Letter Queue)
CREATE TABLE IF NOT EXISTS dead_letter_queue (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    original_id INTEGER,
    profile     TEXT    NOT NULL,
    session_id  TEXT    NOT NULL,
    messages_json TEXT  NOT NULL,
    error_msg   TEXT,
    failed_at   REAL    NOT NULL,
    retry_count INTEGER
);
