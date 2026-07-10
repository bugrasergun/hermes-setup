---
name: honcho-management
description: "Manage, debug, and configure the self-hosted local Honcho memory provider running on macOS bare-metal. Handles LaunchAgent service control, .env configuration, and dialectic/auth troubleshooting."
version: 1.5.0
author: Ayda
platforms: [macos]
metadata:
  hermes:
    tags: [honcho, memory, self-hosted, postgresql, redis, management, diagnostics, launchd, ollama, model-migration]
    related_skills: [hermes-agent]
---

# Honcho Management

This skill enables the agent to monitor, maintain, and configure the local self-hosted Honcho memory server running on macOS without Docker.

## Installation Path

- **Honcho Server:** `/Users/USERNAME/honcho/`
- **Python venv:** `/Users/USERNAME/honcho/.venv/`
- **PostgreSQL database:** `honcho` (PostgreSQL 18, via Homebrew)
- **Redis:** running as macOS brew service
- **Honcho API:** `http://localhost:8000`
- **Hermes config:** `~/.hermes/honcho.json`

## Server Control

### Start / Stop Services (macOS Homebrew)

```bash
brew services start postgresql@18
brew services start redis
brew services stop postgresql@18
brew services stop redis
brew services restart postgresql@18
brew services restart redis
brew services list | grep -E "postgresql|redis"
```

### launchctl stop vs kill vs unload — What Each Does

| Command | Effect on launchd-managed processes |
|---------|--------------------------------------|
| `launchctl stop <service>` | Sends SIGSTOP — **pauses** the process. launchd still thinks it's running. Process stays in `launchctl list` with status `-15`. NOT a restart. |
| `kill <PID>` | Immediately respawned by launchd (auto-restart). **Kill alone does NOT permanently stop Honcho.** |
| `launchctl unload <plist>` | **Fully removes** the service from launchd. Process stops and does NOT restart. |
| `launchctl load <plist>` | Registers and starts the service. |

> **Pitfall:** `launchctl stop` does NOT restart a service — it only pauses (SIGSTOP). Use `unload` → `load` for a clean restart cycle.

### Start the Honcho API Server

```bash
cd /Users/USERNAME/honcho
source .venv/bin/activate
uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

Run in the background (non-blocking):
```bash
cd /Users/USERNAME/honcho
nohup .venv/bin/uvicorn src.main:app --host 127.0.0.1 --port 8000 > /tmp/honcho.log 2>&1 &
echo $! > /tmp/honcho.pid
```

Stop background server:
```bash
kill $(cat /tmp/honcho.pid) && rm /tmp/honcho.pid
```

---

## Server Restart (launchd-managed)

**CRITICAL:** Honcho is registered as a **macOS LaunchAgent** (not a manual process). Blunt `kill` will only trigger an automatic restart by launchd — you MUST use proper launchctl commands to truly stop the services.

LaunchAgent plists live at:
- `~/Library/LaunchAgents/com.honcho.server.plist`
- `~/Library/LaunchAgents/com.honcho.deriver.plist`

### Method 1 — unload / load (simpler, preferred)

```bash
# Verify launchd registration
launchctl list | grep honcho

# CORRECT restart flow (unload → load)
launchctl unload ~/Library/LaunchAgents/com.honcho.server.plist
launchctl unload ~/Library/LaunchAgents/com.honcho.deriver.plist
launchctl load ~/Library/LaunchAgents/com.honcho.server.plist
launchctl load ~/Library/LaunchAgents/com.honcho.deriver.plist

# Verify
curl -s http://127.0.0.1:8000/health
# Expected: {"status":"ok"}
```

### Method 2 — bootout / bootstrap (alternative, same effect)

```bash
# Verify launchd registration
launchctl list | grep honcho
# Expected: com.honcho.server, com.honcho.deriver

# CORRECT restart flow (bootout → bootstrap)
launchctl bootout gui/$(id -u)/com.honcho.server
launchctl bootout gui/$(id -u)/com.honcho.deriver
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.honcho.server.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.honcho.deriver.plist

# Verify
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/openapi.json
# Expected: 200
```

**FALLBACK (if LaunchAgents not installed or bootstrap fails):**
```bash
cd /Users/USERNAME/honcho
.venv/bin/uvicorn src.main:app --host 127.0.0.1 --port 8000 &
.venv/bin/python -m src.deriver &
```

> **Pitfall:** `--reload` flag does NOT detect `.env` changes — always do a full `bootout`→`bootstrap` cycle after `.env` edits.

---

## Diagnostics & Health Checks

```bash
# API health (openapi.json is the health endpoint; /health does exist since v3)
curl -s http://127.0.0.1:8000/health
# Expected: {"status":"ok"}

# Redis
redis-cli ping   # Expected: PONG

# PostgreSQL tables
/opt/homebrew/opt/postgresql@18/bin/psql -d honcho -c "\\dt"

# View logs
tail -f ~/.hermes/logs/honcho.log
tail -f ~/.hermes/logs/honcho.error.log
# Deriver-specific errors
tail -f ~/.hermes/logs/honcho-deriver.error.log
```

## Slow Response / Timeout Troubleshooting Flow

When Hermes is unreasonably slow to respond (minutes instead of seconds), Honcho's dialectic/deriver LLM calls may be timing out. Follow this flow:

1. **Run `hermes doctor`** — if Honcho shows ✅ "connected", the issue is upstream, not connectivity
2. **Check Honcho health** — `curl -s http://localhost:8000/health`
3. **Verify Honcho processes are running** — `ps aux | grep honcho | grep -v grep | grep -v postgres`
4. **Check error logs for `APITimeoutError` or `RateLimitError`:**
   ```bash
   grep -i "timeout\|ratelimit\|429\|503" ~/.hermes/logs/honcho.error.log | tail -20
   grep -i "timeout\|ratelimit\|429\|503" ~/.hermes/logs/honcho-deriver.error.log | tail -20
   ```
5. **Check which LLM model Honcho is using:**
   ```bash
   grep -i "MODEL=" /Users/USERNAME/honcho/.env
   ```
6. **If models contain `:free` suffix** (e.g. `google/gemma-4-31b-it:free`) — this is the root cause. Free-tier models on OpenRouter constantly return 429/503 rate limits, causing 30s+ timeout + retry cascades that kill response time.
7. **Fix:** Replace ALL model references. Current preferred provider is **Nvidia NIM** (free, no rate limit):
   ```bash
   cd /Users/USERNAME/honcho
   cp .env .env.bak.$(date +%Y%m%d_%H%M%S)
   sed -i '' 's|deepseek/deepseek-v4-flash|deepseek-ai/deepseek-v4-flash|g' .env
   sed -i '' 's|https://openrouter.ai/api/v1|https://integrate.api.nvidia.com/v1|g' .env
   perl -pi -e 's/API_KEY_ENV=.*E_KEY$/g' .env
   # Add standalone NVIDIA_API_KEY=<key> line to .env (use Python, not echo)
   ```
   See the **Provider Migration** section in `references/env-config-gotcha.md` for the full migration checklist.
8. **Restart Honcho** (launchctl unload + load, see below)
9. **Verify** — error logs should stop showing timeout/rate-limit errors

> **Pitfall:** Model names appear in ~9 env vars (Deriver, Summary, 5× Dialectic levels, Dream Deduction, Dream Induction). The sed above replaces ALL at once, but always `grep -i "MODEL=" .env` to confirm before restarting.

---

## Hermes Integration

```bash
hermes honcho status          # Verify connection to http://localhost:8000
hermes honcho sync            # Sync new profiles to honcho.json hosts block
hermes honcho mode hybrid     # context injection + tools (default)
hermes honcho mode context    # injection only, tools hidden
hermes honcho mode tools      # tools only, no injection
```

---

## .env Configuration Pitfall: Missing API_KEY_ENV

**KNOWN ISSUE:** When configuring `.env` model settings, `OVERRIDES__API_KEY_ENV` is **only set for Deriver by default**. Dialectic, Summary, Dream, and Embedding modules silently inherit **no API key** → all LLM calls return `401 Missing Authentication header`.

**Symptoms:**
- `honcho_reasoning` / `honcho_context` return: `"No result from Honcho"`
- `honcho.error.log`: `openai.AuthenticationError: Error code: 401 - Missing Authentication header`
- `honcho.log`: `POST /v3/workspaces/hermes/peers/hermes/chat" 500 Internal Server Error`
- **GET** requests (context, card) return **200 OK**; **POST** (chat/synthesis) return **500**
- Dialectic context injection silently fails; you see no compiled memory in responses

**Root Cause:** Honcho's `_resolve_secret(api_key, api_key_env)` — when `api_key_env` is `None`, `os.getenv()` is never called, so requests go to the provider with an empty key.

**Fix:** Ensure ALL modules in `/Users/USERNAME/honcho/.env` have `API_KEY_ENV`:

```env
# Deriver (always present)
DERIVER_MODEL_CONFIG__OVERRIDES__API_KEY_ENV=OPENROUTER_API_KEY
# Summary (ADD if missing)
SUMMARY_MODEL_CONFIG__OVERRIDES__API_KEY_ENV=OPENROUTER_API_KEY
# Dialectic - all 5 levels (ADD if missing)
DIALECTIC_LEVELS__minimal__MODEL_CONFIG__OVERRIDES__API_KEY_ENV=OPENROUTER_API_KEY
DIALECTIC_LEVELS__low__MODEL_CONFIG__OVERRIDES__API_KEY_ENV=OPENROUTER_API_KEY
DIALECTIC_LEVELS__medium__MODEL_CONFIG__OVERRIDES__API_KEY_ENV=OPENROUTER_API_KEY
DIALECTIC_LEVELS__high__MODEL_CONFIG__OVERRIDES__API_KEY_ENV=OPENROUTER_API_KEY
DIALECTIC_LEVELS__max__MODEL_CONFIG__OVERRIDES__API_KEY_ENV=OPENROUTER_API_KEY
# Dream (ADD if missing)
DREAM_DEDUCTION_MODEL_CONFIG__OVERRIDES__API_KEY_ENV=OPENROUTER_API_KEY
DREAM_INDUCTION_MODEL_CONFIG__OVERRIDES__API_KEY_ENV=OPENROUTER_API_KEY
```

**Verify config loads correctly:**
```bash
cd /Users/USERNAME/honcho
.venv/bin/python -c "
import os; os.chdir('/Users/USERNAME/honcho')
from dotenv import load_dotenv; load_dotenv(override=True)
from src.config import settings
print('Summary:', settings.SUMMARY_MODEL_CONFIG.overrides.api_key_env)
print('Deriver:', settings.DERIVER_MODEL_CONFIG.overrides.api_key_env)
for level, cfg in settings.DIALECTIC.LEVELS.items():
    print(f'Dialectic {level}: env={cfg.MODEL_CONFIG.overrides.api_key_env}')
"
```

After any `.env` change, **restart Honcho** (kill + relaunch). `--reload` does not detect `.env` changes.
**Debug checklist when Dialectic/Reasoning fails:**
1. Check `honcho.error.log` for `AuthenticationError` or `401`
2. Check `honcho.log` for POST 500 vs GET 200 pattern
3. Run the verify script above to confirm all modules have `api_key_env` set
4. Restart Honcho processes
5. Test with `honcho_reasoning` tool

---

## Peer Identity & `pinPeerName`

**CRITICAL for single-user setups:** Without `pinPeerName`, the Hermes gateway passes the raw platform user ID (e.g. Telegram numeric UID `1055137294`) as the peer name. This creates **duplicate peers** — one per platform — fragmenting memory.

**Symptoms:**
- 3+ peers exist when you expect 2 (one user + one AI)
- Memory split across peers: `USERNAME`, `hermes`, and a numeric Telegram ID
- `honcho_reasoning` / `honcho_context` return partial context (only from one peer's collection)

**Fix:** Add `pinPeerName: true` to `honcho.json` hosts block. This forces the config's `peerName` to win over platform IDs.

```json
{
  "hosts": {
    "hermes": {
      "aiPeer": "hermes",
      "peerName": "your-name",
      "pinPeerName": true
    }
  }
}
```

> **Reference:** [GitHub issue #15984](https://github.com/NousResearch/hermes-agent/issues/15984), fixed in Hermes v2026.4.30 via `pinPeerName` opt-in.

### Verifying `pinPeerName` is Active

After adding `pinPeerName: true` and restarting the gateway, verify it's working BEFORE assuming it failed:

```bash
# Send a test message, then check which peer got the new message:
/opt/homebrew/opt/postgresql@18/bin/psql -U USERNAME -d honcho -c "
SELECT peer_name, COUNT(*) as cnt FROM messages
WHERE workspace_name='hermes' GROUP BY peer_name ORDER BY cnt DESC;
"
```

> **Pitfall:** Gateway restart alone does NOT guarantee new peer identity. The Honcho session manager caches peer resolution per session. If a session was already opened under the old identity (before `pinPeerName`), it **continues using the old peer** for that session. New.g. new conversation after restart) should use the pinned identity. Verify with a fresh message, not by checking if the old peer still exists.

If a duplicate peer still reappears after `pinPeerName: true`:
1. Check gateway logs for `Honcho session '...'` — the session key will show which identity was resolved
2. Try `hermes gateway restart` — ensures the Honcho plugin re-initializes with fresh config
3. Send a NEW message (don't reply in an existing session) — old sessions are sticky
4. Check `_resolve_user_peer_id` debug: the config object must have `pin_peer_name = True`

### Merging Duplicate Peers (DB Migration)

When a duplicate peer already exists (e.g. `1055137294` alongside `USERNAME`), merge them before setting `pinPeerName` to preserve historical data:

```sql
BEGIN;

-- 1. Drop FK constraint temporarily (documents → collections)
ALTER TABLE documents DROP CONSTRAINT fk_documents_observer_observed_workspace_name_collections;

-- 2. Reassign all messages
UPDATE messages SET peer_name = 'USERNAME'
WHERE peer_name = '1055137294' AND workspace_name = 'hermes';

-- 3. Reassign session_peers
UPDATE session_peers SET peer_name = 'USERNAME'
WHERE peer_name = '1055137294' AND workspace_name = 'hermes';

-- 4. Reassign message_embeddings
UPDATE message_embeddings SET peer_name = 'USERNAME'
WHERE peer_name = '1055137294' AND workspace_name = 'hermes';

-- 5. Reassign documents
UPDATE documents SET observer = 'USERNAME'
WHERE observer = '1055137294' AND workspace_name = 'hermes';
UPDATE documents SET observed = 'USERNAME'
WHERE observed = '1055137294' AND workspace_name = 'hermes';

-- 6. Merge collections (delete duplicates that would violate unique constraint)
DELETE FROM collections WHERE workspace_name = 'hermes'
  AND (
    (observer = 'hermes' AND observed = '1055137294')
    OR (observer = '1055137294' AND observed = '1055137294')
    OR (observer = '1055137294' AND observed = 'USERNAME')
  );
UPDATE collections SET observed = 'USERNAME'
WHERE observed = '1055137294' AND workspace_name = 'hermes';
UPDATE collections SET observer = 'USERNAME'
WHERE observer = '1055137294' AND workspace_name = 'hermes';

-- 7. Re-add FK constraint
ALTER TABLE documents ADD CONSTRAINT fk_documents_observer_observed_workspace_name_collections
  FOREIGN KEY (observer, observed, workspace_name)
  REFERENCES collections (observer, observed, workspace_name);

-- 8. Delete the old peer
DELETE FROM peers WHERE name = '1055137294' AND workspace_name = 'hermes';

COMMIT;
```

> **FK constraint is NOT deferrable** in Honcho's schema — must DROP andADD it. Always run as a single transaction so the FK gap is brief.

**Verification:**
```sql
SELECT name FROM peers WHERE workspace_name = 'hermes' ORDER BY name;
-- Expected: only your configured peer(s) + AI peer
```

---

## Configuration Reference

Config priority: `~/.hermes/honcho.json` → `~/.honcho/config.json`

### Current `~/.hermes/honcho.json`

```json
{
  "baseUrl": "http://localhost:8000",
  "enabled": true,
  "workspace": "hermes",
  "recallMode": "hybrid",
  "writeFrequency": "async",
  "sessionStrategy": "per-directory",
  "hosts": {
    "hermes": {
      "aiPeer": "ayda",
      "peerName": "USERNAME",
      "pinPeerName": true
    }
  }
}
```

### Multi-Agent Honcho Setup

When running multiple Hermes profiles (multi-agent architecture), each profile needs its own entry in the `hosts` block with a unique `aiPeer` identity:

```json
{
  "hosts": {
    "hermes": {
      "aiPeer": "ayda",
      "peerName": "USERNAME",
      "pinPeerName": true
    },
    "product-manager": {
      "aiPeer": "product-manager",
      "peerName": "USERNAME",
      "pinPeerName": true
    },
    "business-strategist": {
      "aiPeer": "business-strategist",
      "peerName": "USERNAME",
      "pinPeerName": true
    },
    "personal-growth-mentor": {
      "aiPeer": "personal-growth-mentor",
      "peerName": "USERNAME",
      "pinPeerName": true
    }
  }
}
```

**How it works:**
- `peerName` (always `USERNAME`) → shared user memory. ALL agents read/write observations about the human user here.
- `aiPeer` (unique per profile) → per-agent AI memory. Each agent's own observations are isolated. `ayda`, `product-manager`, `business-strategist`, `personal-growth-mentor` each get their own AI peer identity.

**Auto-sync:** `hermes honcho sync` scans all profiles and syncs them to `honcho.json` automatically. Run after creating a new profile:

```bash
hermes honcho sync    # adds new profiles to hosts block
hermes gateway restart # re-initializes Honcho plugin
```

> **Verify per-agent peers in DB:**
> ```bash
> /opt/homebrew/opt/postgresql@18/bin/psql -d honcho -c "
> SELECT name FROM peers WHERE workspace_name='hermes' ORDER BY name;
> "
> ```
> Expected: `USERNAME` (user) + `ayda`, `product-manager`, etc. (AI peers)

---

## Database Operations

```bash
# Run update
cd /Users/USERNAME/honcho && git pull
source .venv/bin/activate
uv pip install -e . && alembic upgrade head

# Direct psql access
/opt/homebrew/opt/postgresql@18/bin/psql -d honcho
```

### Honcho Venv as Python Dependency Source

Honcho's venv (`/Users/USERNAME/honcho/.venv/`) contains packages NOT available in system Python:
- `psycopg` (v3.3.4) — PostgreSQL driver (NOT psycopg2)
- `httpx` (0.28.1) — HTTP client
- `sqlalchemy` (2.0.49) — ORM
- `pgvector` — vector type support
- `aiohttp` (3.13.5) — async HTTP

When writing scripts that need DB access or HTTP calls and system Python lacks the deps,
use Honcho's venv Python directly:

```bash
/Users/USERNAME/honcho/.venv/bin/python /path/to/script.py
```

**DB connection string** (from `.env`):
```
DB_CONNECTION_URI=postgresql+psycopg://localhost/honcho
```

For raw `psycopg3` connections (without SQLAlchemy):
```python
conn = psycopg.connect("host=localhost port=5432 dbname=honcho user=USERNAME")
```

### pgvector Schema (as of 2026-07-08)

| Table | Purpose | Embedding Column | Index |
|-------|---------|------------------|-------|
| `message_embeddings` | Conversation message embeddings | `vector(768)` | HNSW cosine |
| `documents` | Honcho observations (explicit/deductive/inductive) | `vector(768)` | HNSW cosine |
| `brain_documents` | Brain markdown file chunks (custom - not Honcho native) | `vector(768)` | HNSW cosine |

All embedding tables use `nomic-embed-text` (768-dim) via Ollama at `localhost:11434`.

Useful SQL:
```sql
SELECT * FROM peers;
SELECT session_name, COUNT(*) FROM messages GROUP BY session_name;
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `curl http://localhost:8000/health` non-200 | API server not running | `launchctl bootstrap` the plist |
| `hermes honcho status` shows no baseUrl | `honcho.json` missing | Check `~/.hermes/honcho.json` |
| `redis-cli ping` fails | Redis not running | `brew services start redis` |
| `No result from Honcho` on reasoning/context | Dialectic API key missing | Check `API_KEY_ENV` in `.env`, restart Honcho |
| `POST .../chat 500` but `GET .../context 200` | LLM auth failure (401 upstream) | Same as above |
| `.env` changes not taking effect | launchd restart needed, not just `--reload` | `bootout` → `bootstrap` cycle |
| After `kill`, process immediately respawns | launchd auto-restarts crashed services | Use `launchctl unload` or `bootout` instead of `kill` |
| **Hermes responds in 10–16 minutes** | Honcho LLM calls timeout on rate-limited free model (`google/gemma-4-31b-it:free` → 429/503 on OpenRouter) | Switch all `.env` model refs to `deepseek/deepseek-v4-flash` (see Slow Response section above) |
| **SHORT summary empty (size=18), `finish_reasons=['length']`** | Local LLM model (e.g. `gemma4:12b-mlx`) has poor structured output / tool calling — produces malformed JSON (`We{...` prefix), hits output token limit, falls back to basic summary | Switch to an MLX-optimized model with proven structured output (e.g. `qwen3.5:4b-mlx`, 262K context). See Local Model Migration below. |
| **Deriver produces zero observations for every batch — "Repair failed: Expecting value at line 1 column 1" in deriver.error.log** | Honcho's default `json_schema` structured output mode is incompatible with Ollama. Model responds in natural language (markdown lists) instead of JSON. | Add `STRUCTURED_OUTPUT_MODE=json_object` to ALL model configs in `.env`. See [Structured Output Mode](references/structured-output-mode.md). |
| **After `json_object` fix: "Repair failed" stops, but still "zero observations" — `finish_reasons=['length']`** | Model has built-in thinking mode (e.g. `qwen3.5:4b-mlx`) that consumes all output tokens before JSON is produced. | Switch to a model without aggressive thinking, or increase `max_output_tokens` in `.env`. See [Structured Output Mode](references/structured-output-mode.md) section 'Second-Level Diagnosis: Thinking Mode Token Consumption'. |
| **Summaries not being generated / missing from DB** | Honcho has no `summaries` table — summaries are triggered via queue (`task_type='summary'`), only at message multiples (SHORT=20, LONG=60). No manual trigger endpoint. | Check queue table for pending summary tasks: `psql -d honcho -c "SELECT session_id, task_type, processed FROM queue WHERE task_type='summary' ORDER BY created_at DESC LIMIT 5;"`. See [Summary & Queue Debugging](references/summary-queue-debugging.md). |

---

## Local Model Migration (Ollama → Honcho)

When switching Honcho's LLM model from one local Ollama model to another (e.g. `gemma4:12b-mlx` → `qwen3.5:4b-mlx`):

### 1. Pull new model

```bash
ollama pull qwen3.5:4b-mlx
# 4.0 GB, 262K context, MLX optimized
```

### 2. Check all MODEL references in .env

Models appear in **9 places** across Honcho modules:
- `DERIVER_MODEL_CONFIG__MODEL`
- `SUMMARY_MODEL_CONFIG__MODEL`
- `DIALECTIC_LEVELS__{minimal,low,medium,high,max}__MODEL_CONFIG__MODEL` (×5)
- `DREAM_DEDUCTION_MODEL_CONFIG__MODEL`
- `DREAM_INDUCTION_MODEL_CONFIG__MODEL`

```bash
grep -n "MODEL=" /Users/USERNAME/honcho/.env
# Count must be 9 (or 10 if EMBEDDING_MODEL included)
```

### 3. Replace all model references

```bash
cd /Users/USERNAME/honcho
cp .env .env.bak.$(date +%Y%m%d_%H%M%S)
sed -i '' 's/gemma4:12b-mlx/qwen3.5:4b-mlx/g' .env
grep -c "qwen3.5:4b-mlx" .env  # Must return the same count as step 2
```

### 4. Restart Honcho (model change requires full restart)

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.honcho.server.plist
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.honcho.deriver.plist
sleep 2
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.honcho.server.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.honcho.deriver.plist
sleep 5
launchctl list | grep honcho  # Verify both running
```

### 5. Verify new model is active

```bash
tail -f ~/.hermes/logs/honcho-deriver.error.log
# Watch for model-related errors; if none appear after a few messages, model is working
```

### 6. Clean up old models (optional)

```bash
ollama list                          # See all models
ollama rm gemma4:12b-mlx             # Remove old model
```

### Model Selection Criteria for Honcho

For Honcho's summary/deriver/dialectic tasks, prioritize:
- **Structured output / tool calling ability** — Honcho expects JSON (`PromptRepresentation`)
- **Output token capacity** — must not hit `finish_reasons=['length']` on summary tasks
- **Context window** — 32K is sufficient (SHORT=20 msg, LONG=60 msg sliding window)
- **MLX optimization** — Apple Silicon native acceleration via `-mlx` suffix

| Model | Structured Output | Context | MLX | Honcho Fit | Pitfalls |
|-------|-------------------|---------|-----|------------|----------|
| `qwen3.5:4b-mlx` | ✅ Good (requires `structured_output_mode=json_object`) | 262K | ✅ | ✅ Recommended | ⚠️ Built-in thinking mode can consume all output tokens → empty response. Increase `max_output_tokens` or switch model if Deriver still produces zero observations. |
| `gemma4:12b-mlx` | ❌ Poor (`We{...` prefix, JSON errors) | 128K | ✅ | ❌ Avoid | — |
| `llama3.2:3b` | ✅ Good | 128K | ⚠️ | ✅ Alternative | — |
| `deepseek-r1:8b` | ✅ Good (reasoning) | 128K | ⚠️ | ✅ Alternative | — |

> **Critical .env Requirement for Ollama-backed Models:** Every model config that uses Ollama as the provider (through the OpenAI-compatible transport) MUST include `STRUCTURED_OUTPUT_MODE=json_object`. Without this, Honcho sends OpenAI `json_schema`/`parse()` structured output format — Ollama ignores the schema instruction and receives only the raw prompt text. The model responds in natural language (markdown lists) instead of JSON, causing all Deriver batches to produce **zero observations** and silently breaking Honcho's memory pipeline. See [Structured Output Mode](references/structured-output-mode.md) for the full diagnosis and fix checklist.

Honcho's Dream system creates higher-level observations from accumulated explicit facts. Triggered automatically when a collection accumulates enough new explicit documents.

### Architecture

| Component | Role |
|-----------|------|
| **DreamScheduler** | Timer-based (`asyncio.sleep` via `IDLE_TIMEOUT_MINUTES`); cancels pending dreams if a new message arrives, preventing redundant processing |
| **Deduction Specialist** | Logical implications, knowledge updates, contradiction detection, peer card updates (max 12 iterations) |
| **Induction Specialist** | Pattern detection across observations — behavioral tendencies, generalizations (max 10 iterations, runs AFTER deduction to use its new observations) |
| **Surprisal Sampling** | (Optional) Pre-selects "interesting" (geometrically surprising) observations as hints for specialists |
| **DreamType** | Only one type: `"omni"` — runs deduction then induction sequentially per dream cycle |

### Trigger Logic (`check_and_schedule_dream`)

Dream fires ONLY when ALL conditions met:
1. `settings.DREAM.ENABLED == True`
2. Explicit documents since last dream ≥ `DOCUMENT_THRESHOLD`
3. At least `MIN_HOURS_BETWEEN_DREAMS` elapsed since last dream
4. No dream already pending in queue for this `(observer, observed)` collection
5. Collection config doesn't disable dreams

### Development/Test Settings

For faster dream cycles during active development (current prod: threshold=50, min_hours=8, idle=60):
```env
DREAM_DOCUMENT_THRESHOLD=10
DREAM_MIN_HOURS_BETWEEN_DREAMS=1
DREAM_IDLE_TIMEOUT_MINUTES=5
```
Then restart Honcho (bootout → bootstrap).

### Diagnostic Queries (psql)

```bash
# Is the dream schedule firing?
/opt/homebrew/opt/postgresql@18/bin/psql -U USERNAME -d honcho -c "
SELECT task_type, work_unit_key, created_at, processed
FROM queue WHERE task_type='dream' AND workspace_name='hermes'
ORDER BY created_at DESC LIMIT 10;
"

# Which collections have hit threshold?
/opt/homebrew/opt/postgresql@18/bin/psql -U USERNAME -d honcho -c "
SELECT c.observer, c.observed,
       c.internal_metadata->'dream'->>'last_dream_at' as last_dream,
       c.internal_metadata->'dream'->>'last_dream_document_count' as dream_count_at,
       (SELECT COUNT(*) FROM documents d
        WHERE d.workspace_name=c.workspace_name
          AND d.observer=c.observer AND d.observed=c.observed
          AND d.level='explicit') as current_count
FROM collections c WHERE c.workspace_name='hermes';
"

# Deductive/inductive observations that resulted?
/opt/homebrew/opt/postgresql@18/bin/psql -U USERNAME -d honcho -c "
SELECT level, COUNT(*) FROM documents
WHERE workspace_name='hermes' AND level IN ('deductive','inductive')
GROUP BY level;
"
```

> **Pitfall:** After a dream cycle runs (queue `task_type='dream'` shows `processed=t`), if no `deductive`/`inductive` observations appear, the dream specialists failed silently. Check Honcho's stderr/dream logs for specialist errors. **Common cause:** LLM model used by Honcho (`google/gemma-4-31b-it:free`) doesn't follow the specialist's tool-calling format well and/or rate-limits constantly. Fix: switch ALL Honcho model references to `deepseek/deepseek-v4-flash` (see Slow Response Troubleshooting section).

> **Note:** `ENABLED_TYPES` only supports `"omni"` — there is no separate `deductive` or `inductive` type. A single `omni` dream runs deduction THEN induction sequentially.
```

### References

- [Env Config Gotcha](references/env-config-gotcha.md) — detailed diagnosis flow for API_KEY_ENV issues
- [Structured Output Mode](references/structured-output-mode.md) — diagnosis and fix for Ollama's `json_object` requirement, plus second-level thinking-mode diagnosis
- [Dream System](references/dream-system.md) — architecture, specialist prompts, and configuration deep-dive
- [Summary & Queue Debugging](references/summary-queue-debugging.md) — summary trigger logic, sliding window, queue inspection, empty summary / fallback diagnosis, and model selection criteria for Honcho
- [API Test Methodology](references/api-test-methodology.md) — test Honcho's Deriver/Summary pipeline via REST API to verify config changes