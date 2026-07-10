# Honcho API Test Methodology

How to test Honcho's Deriver, Summary, and memory pipeline directly via the REST API — without waiting for natural conversation flow.

## When to Use This

- After changing `.env` config (model, structured_output_mode, API keys)
- After restarting Honcho processes
- When Deriver shows "zero observations" and you want to verify the fix
- When Summaries aren't generating

## API Endpoint Reference

All routes under `http://localhost:8000/v3/workspaces/hermes/`. Full schema at `/openapi.json`.

## Test Flow

### 1. Create a Test Session

```bash
curl -s -X POST "http://localhost:8000/v3/workspaces/hermes/sessions" \
  -H "Content-Type: application/json" \
  -d '{"name": "test_verify_structured_output"}' | python3 -m json.tool
```

Response includes: `id`, `is_active: true`, `created_at`.

### 2. Send a Test Message

```bash
curl -s -X POST "http://localhost:8000/v3/workspaces/hermes/sessions/test_verify_structured_output/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "content": "This is a test message. My name is Bugra and I run the Taco Bros business in Vlore.",
        "peer_id": "USERNAME"
      }
    ]
  }' | python3 -m json.tool
```

**Schema:** `MessageCreate` requires `content` (string) and `peer_id` (string). Optional: `metadata` (dict), `configuration`, `created_at`.
**Batch:** Wrapped in `MessageBatchCreate` with `messages` array (min 1, max 100).

### 3. Wait for Deriver Processing

The Deriver runs asynchronously via a queue. Check after 30-90 seconds:

```bash
tail -20 ~/.hermes/logs/honcho-deriver.error.log
```

Expected patterns:
```
INFO - performance ... observation_count=3 ...  ← Success! Observations created.
WARNING - Deriver generated zero observations   ← Still broken
ERROR - Repair failed: Expecting value...       ← JSON parsing problem
```

### 4. Verify Observations in Database

```bash
/opt/homebrew/opt/postgresql@18/bin/psql -d honcho -c "
SELECT level, COUNT(*) FROM documents
WHERE workspace_name='hermes'
GROUP BY level ORDER BY level;
"
```

Expected: `explicit` count should increase after each successfully processed message.

### 5. Clean Up Test Data

```bash
# Test sessions auto-expire, but you can delete explicitly:
curl -s -X DELETE "http://localhost:8000/v3/workspaces/hermes/sessions/test_verify_structured_output"
```

## Deriver Diagnostics via API

### Check Queue Status

```bash
# Direct SQL for queue inspection:
/opt/homebrew/opt/postgresql@18/bin/psql -d honcho -c "
SELECT session_id, task_type, processed, error, created_at
FROM queue ORDER BY created_at DESC LIMIT 10;
"
```

### Check Deriver Logs

```bash
# Watch live processing
tail -f ~/.hermes/logs/honcho-deriver.error.log
tail -f ~/.hermes/logs/honcho-deriver.log

# Count recent failures
grep -c "zero observations" ~/.hermes/logs/honcho-deriver.error.log

# Count recent successes
grep -c "observation_count=[1-9]" ~/.hermes/logs/honcho-deriver.error.log
```

## Common Test Scenarios

| Scenario | What to Check |
|----------|---------------|
| Config change deployed | After `.env` edit → restart Honcho → send test message → check observations in DB |
| Model switch | Same flow — if observations still zero, check deriver log for `finish_reasons` |
| Thinking mode suspected | Check deriver log for `finish_reasons=['length']` without "Repair failed" errors |
| Summary not generating | Check if message count hit a threshold (SHORT=20, LONG=60). Add test messages to bump count. |