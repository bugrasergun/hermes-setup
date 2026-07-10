# .env Configuration Gotcha: Missing API_KEY_ENV

## The Problem

When configuring Honcho's `.env` file for OpenRouter (or any provider), the `OVERRIDES__API_KEY_ENV` field is **only set for Deriver by default**. Dialectic, Summary, Dream, and Embedding modules silently inherit **no API key** → all LLM calls return `401 Missing Authentication header`.

## Symptoms

- `honcho_reasoning` / `honcho_context` return: `"No result from Honcho"`
- `honcho.error.log`: `openai.AuthenticationError: Error code: 401 - Missing Authentication header`
- `honcho.log`: `POST /v3/workspaces/hermes/peers/hermes/chat" 500 Internal Server Error`
- **GET** requests (context, card) return **200 OK**; **POST** (chat/synthesis) return **500**
- Dialectic context injection silently fails; no compiled memory in responses

## Root Cause

Honcho's `_resolve_secret(api_key, api_key_env)` function in `src/config.py`:

```python
def _resolve_secret(value: str | None, env_name: str | None) -> str | None:
    if value is not None:
        return value
    if env_name is None:
        return None  # <-- returns None, no getenv() call
    return os.getenv(env_name)
```

When `api_key_env` is `None`, `os.getenv()` is never called, so requests go to the provider with an empty/missing key.

## Diagnosis Flow

1. **Check logs**: `tail -20 ~/.hermes/logs/honcho.error.log` — look for `AuthenticationError` or `401`
2. **Check access pattern**: `tail -50 ~/.hermes/logs/honcho.log` — GET 200 + POST 500 = auth issue
3. **Verify config**: Run the verify script to confirm which modules lack `api_key_env`
4. **Fix**: Add `API_KEY_ENV` to all modules in `.env`
5. **Restart**: Kill + relaunch Honcho processes (`--reload` does NOT detect `.env` changes)

## Verify Script

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

All modules should show `OPENROUTER_API_KEY` (or your chosen env var name).

## Provider Migration (OpenRouter → Nvidia NIM, or any provider swap)

When changing the upstream LLM provider, **three** fields must be changed across **all 9 modules** (Deriver, Summary, 5 Dialectic, Dream Deduction, Dream Induction):
1. `MODEL` — the model name (note: OpenRouter uses `deepseek/deepseek-v4-flash`, Nvidia NIM uses `deepseek-ai/deepseek-v4-flash`)
2. `OVERRIDES__BASE_URL` — e.g. `https://openrouter.ai/api/v1` → `https://integrate.api.nvidia.com/v1`
3. `OVERRIDES__API_KEY_ENV` — e.g. `OPENROUTER_API_KEY` → `***

**CRITICAL**: The API key env var must also be **defined as a standalone line** in Honcho's `.env` for `os.getenv` to find it. If it only exists in `~/.hermes/.env`, Honcho won't see it. Copy the key value from `~/.hermes/.env` and add as a standalone line in `/Users/USERNAME/honcho/.env`.

**forget about migration** — you also need the standalone key. Don't forget.

### Migration commands (from OpenRouter to Nvidia NIM)

```bash
cd /Users/USERNAME/honcho
cp .env .env.bak  # backup

# 1. Model name: deepseek/ -> deepseek-ai/
sed -i '' 's|deepseek/deepseek-v4-flash|deepseek-ai/deepseek-v4-flash|g' .env

# 2. Base URL: openrouter -> nvidia
sed -i '' 's|https://openrouter.ai/api/v1|https://integrate.api.nvidia.com/v1|g' .env

# 3. API key env var name: use python (sed chokes on backslash-heavy API names)
perl -pi -e 's/API_KEY_ENV=OPENRO...Y/g' .env

# 4. Add standalone NVIDIA_API_KEY=*** (copy from ~/.hermes/.env)
#    Append after OPENROUTER_API_KEY line (use python — bash is fragile, see session 2026-07-05)

# 5. Restart Honcho (launchctl, not --reload)
launchctl unload ~/Library/LaunchAgents/com.honcho.server.plist
launchctl unload ~/Library/LaunchAgents/com.honcho.deriver.plist
sleep 2
launchctl load ~/Library/LaunchAgents/com.honcho.server.plist
launchctl load ~/Library/LaunchAgents/com.honcho.deriver.plist
```

**keep it simple.**

## Fix Template

Add these lines to `/Users/USERNAME/honcho/.env` for each module that's missing `API_KEY_ENV`:

```env
# Summary
SUMMARY_MODEL_CONFIG__OVERRIDES__API_KEY_ENV=***

# Dialectic - all 5 levels
DIALECTIC_LEVELS__minimal__MODEL_CONFIG__OVERRIDES__API_KEY_ENV=***
DIALECTIC_LEVELS__low__MODEL_CONFIG__OVERRIDES__API_KEY_ENV=***
DIALECTIC_LEVELS__medium__MODEL_CONFIG__OVERRIDES__API_KEY_ENV=***
DIALECTIC_LEVELS__high__MODEL_CONFIG__OVERRIDES__API_KEY_ENV=***
DIALECTIC_LEVELS__max__MODEL_CONFIG__OVERRIDES__API_KEY_ENV=***

# Dream
DREAM_DEDUCTION_MODEL_CONFIG__OVERRIDES__API_KEY_ENV=***
DREAM_INDUCTION_MODEL_CONFIG__OVERRIDES__API_KEY_ENV=***
```

(Replace `***` env var with whichever provider key name you use — `OPENROUTER_API_KEY` or `***.

## Restart Procedure

Honcho is managed as **macOS LaunchAgent**. Use `launchctl`, NOT `kill`:

```bash
# Check registration
launchctl list | grep honcho

# Bootout (truly stop — kill alone causes auto-restart)
launchctl bootout gui/$(id -u)/com.honcho.server
launchctl bootout gui/$(id -u)/com.honcho.deriver

# Bootstrap (relaunch with fresh config)
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.honcho.server.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.honcho.deriver.plist

# Verify
sleep 5 && curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/openapi.json
# Expected: 200
```

**FALLBACK** (if LaunchAgents unavailable):
```bash
cd /Users/USERNAME/honcho
.venv/bin/uvicorn src.main:app --host 127.0.0.1 --port 8000 &
.venv/bin/python -m src.deriver &
```

> **CRITICAL:** `--reload` does NOT detect `.env` changes. Always do full `bootout`→`bootstrap`.

## Session History

| Date | Event |
|------|-------|
| 2026-06-30 | Dialectic 401 errors surfaced after using `honcho_reasoning`. Root cause: all modules except Deriver were missing `API_KEY_ENV` in `.env`. Also discovered Honcho runs as LaunchAgent (blunt `kill` causes infinite restart loop). Fixed via launchctl cycle. |
