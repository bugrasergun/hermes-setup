# Summary & Queue Debugging

How to debug Honcho summary generation — queue inspection, trigger logic, and fallback behavior.

## Architecture

Honcho has **no `summaries` table** in PostgreSQL. Summaries are generated via the queue system and stored as documents/observations. The `queue` table (`task_type='summary'`) is the primary debugging surface.

## Trigger Logic

Summary is triggered automatically, **not manually**. There is no API endpoint to force summary generation.

```python
# From summarizer.py — check_and_create_summaries()
if message_seq_in_session % messages_per_long_summary == 0:
    → create_long_summary_task()

if message_seq_in_session % messages_per_short_summary == 0:
    → create_short_summary_task()
```

Default thresholds:
- `MESSAGES_PER_SHORT_SUMMARY`: **20**
- `MESSAGES_PER_LONG_SUMMARY`: **60**

So SHORT summaries fire at messages 20, 40, 60, 80... and LONG at 60, 120, 180...

### How to Force Summary Regeneration

Since there's no API trigger, the only way is to inject enough new messages to hit the next threshold:

1. Check current message count:
   ```sql
   SELECT s.name, COUNT(m.id) FROM messages m
   JOIN sessions s ON m.session_name = s.name
   WHERE s.name = 'agent-main-telegram-dm-1055137294'
   GROUP BY s.name;
   ```

2. Calculate messages needed to hit next threshold:
   - Next SHORT: `ceil(current / 20) * 20 - current`
   - Next LONG: `ceil(current / 60) * 60 - current`

3. POST small test messages to Honcho API until threshold reached.

## Queue Inspection

```bash
# All recent queue items
/opt/homebrew/opt/postgresql@18/bin/psql -d honcho -c "
SELECT session_id, task_type, processed, created_at
FROM queue ORDER BY created_at DESC LIMIT 10;
"

# Only summary tasks
/opt/homebrew/opt/postgresql@18/bin/psql -d honcho -c "
SELECT session_id, work_unit_key, processed, error, created_at
FROM queue WHERE task_type='summary'
ORDER BY created_at DESC;
"

# Pending (unprocessed) items
/opt/homebrew/opt/postgresql@18/bin/psql -d honcho -c "
SELECT id, session_id, task_type, created_at
FROM queue WHERE processed = false
ORDER BY created_at;
"
```

## Empty Summary / Fallback Diagnosis

### Symptoms

- `honcho-deriver.error.log`: `Generated summary is empty (finish_reasons=['length']). Falling back to basic summary.`
- `honcho-deriver.log`: `SHORT_summary_size=18` (nearly empty, 18 chars)
- `honcho-deriver.error.log`: `Invalid JSON: expected value at line 1 column 1` + `input_value='We{"explicit": [...]}'`

### Root Causes

1. **Structured output failure** — Model (e.g. gemma4 family) produces malformed JSON. Honcho's `PromptRepresentation` validation expects clean JSON; `We{...` prefix fails parsing.

2. **Output token limit** — `finish_reasons=['length']` means model hit `max_tokens` before completing the summary JSON. The incomplete output can't be parsed → fallback.

3. **Fallback behavior** — When LLM summary is empty/invalid, Honcho produces a mechanical "basic summary" (~18 chars, e.g. "Conversation today"). This is injected into Hermes' system prompt but provides almost no context.

### Fix

Switch to an MLX-optimized model with proven structured output ability:
- **Recommended:** `qwen3.5:4b-mlx` (262K context, good JSON generation)
- **Alternative:** `llama3.2:3b`, `deepseek-r1:8b`
- **Avoid:** Gemma 4 family (gemma4:12b, gemma4:4b) — known JSON issues

### Verification After Fix

1. Force a summary by hitting message threshold (add test messages)
2. Check `honcho-deriver.error.log` for `empty` or `finish_reasons=['length']` — should be absent
3. Check `honcho-deriver.log` for `SHORT_summary_size` — should be >100 chars (meaningful summary)
4. Queue item for summary should show `processed = true` with no `error`

## Sliding Window Mechanism

Honcho does NOT send all session messages to the LLM. It uses a sliding window:

```python
messages_per_summary = config.messages_per_long_summary  # 60
start_seq = max(message_seq_in_session - messages_per_summary + 1, 1)
messages = get_messages_by_seq_range(start_seq, message_seq_in_session)
```

This means:
- SHORT summary sees last **20 messages** (~6K tokens)
- LONG summary sees last **60 messages** (~18K tokens)

**Context window requirement:** 32K is sufficient. 262K is overkill but harmless. The `finish_reasons=['length']` error was about **output** token limit, not context window.

## Database Schema (Relevant Tables)

| Table | Purpose |
|-------|---------|
| `queue` | Task queue — summary, representation, dream, reconciler |
| `messages` | All conversation messages |
| `sessions` | Session metadata (name, workspace) |
| `documents` | Observations/conclusions storage (explicit, deductive, inductive) |
| `collections` | Vector storage for peer representations |

> **Note:** No `summaries` table exists. Summaries are stored as observations in `documents` under the appropriate collection.