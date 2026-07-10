# Structured Output Mode — Diagnosis & Fix

## The Problem

Honcho's Deriver (and Summary, Dream) uses structured output to parse LLM responses
into typed objects like `PromptRepresentation`. By default, Honcho sends structured
output in **`json_schema` mode** — the OpenAI `response_format` with a full JSON
schema definition. This works on OpenAI-native and OpenRouter endpoints, but **Ollama
does not support it**. Ollama's OpenAI-compatible API ignores the schema parameter and
receives only the raw prompt text with no indication that JSON output is expected.

### Symptom in the Log

```
ERROR - ❌ Repair failed: Expecting value: line 1 column 1 (char 0)
WARNING - Deriver generated zero observations for messages 2135:2135 in ...
```

The model output visible in the error is **markdown bullet points or prose**, not JSON:

```
input_value='- USERNAME uses Telegram for daily communication...'
input_value='## Explicit Atomic Facts about the user...'
```

### Root Cause Chain

1. Honcho calls `client.chat.completions.parse(**params)` with `response_format=PromptRepresentation`
2. Ollama receives the request but **silently ignores** the schema parameter
3. Model sees only a plain-text prompt: "Analyze messages to extract explicit atomic facts..."
4. With no JSON instruction in the prompt, the model responds in natural markdown
5. Honcho's JSON repair pipeline fails — the response is valid text but not valid JSON
6. `validate_and_repair_json()` returns empty string
7. `PromptRepresentation(explicit=[])` returned → **zero observations**

## The Fix: `structured_output_mode=json_object`

Set `structured_output_mode=json_object` on every model config in `.env`.
This switches Honcho from `json_schema` (incompatible with Ollama) to `json_object`
(lighter protocol): it injects the JSON schema into the prompt as a text instruction
and sets `response_format = {"type": "json_object"}`.

### All Model Configs That Need It

```
DERIVER_MODEL_CONFIG__STRUCTURED_OUTPUT_MODE=json_object
SUMMARY_MODEL_CONFIG__STRUCTURED_OUTPUT_MODE=json_object
DIALECTIC_LEVELS__minimal__MODEL_CONFIG__STRUCTURED_OUTPUT_MODE=json_object
DIALECTIC_LEVELS__low__MODEL_CONFIG__STRUCTURED_OUTPUT_MODE=json_object
DIALECTIC_LEVELS__medium__MODEL_CONFIG__STRUCTURED_OUTPUT_MODE=json_object
DIALECTIC_LEVELS__high__MODEL_CONFIG__STRUCTURED_OUTPUT_MODE=json_object
DIALECTIC_LEVELS__max__MODEL_CONFIG__STRUCTURED_OUTPUT_MODE=json_object
DREAM_DEDUCTION_MODEL_CONFIG__STRUCTURED_OUTPUT_MODE=json_object
DREAM_INDUCTION_MODEL_CONFIG__STRUCTURED_OUTPUT_MODE=json_object
```

> There are **9 model configs** total. Count them before restarting:
> ```bash
> grep "MODEL=" /Users/USERNAME/honcho/.env | wc -l
> grep "STRUCTURED_OUTPUT_MODE" /Users/USERNAME/honcho/.env | wc -l
> # Both should be 9 (or 10 if EMBEDDING_MODEL is counted)
> ```

### After Applying

1. **Restart Honcho** — `.env` changes require a full restart:
   ```bash
   launchctl bootout gui/$(id -u)/com.honcho.server
   launchctl bootout gui/$(id -u)/com.honcho.deriver
   sleep 1
   launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.honcho.server.plist
   launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.honcho.deriver.plist
   sleep 2
   launchctl list | grep honcho  # Verify both running
   ```

2. **Verify new messages produce observations** — after a few normal conversational
   messages, check:
   ```bash
   /opt/homebrew/opt/postgresql@18/bin/psql -d honcho -c "
   SELECT level, COUNT(*) FROM documents
   WHERE workspace_name='hermes'
   GROUP BY level;
   "
   ```
   Expected: `explicit` count should be growing.

3. **Check deriver log for success**:
   ```bash
   grep -c "zero observations" /Users/USERNAME/.hermes/logs/honcho-deriver.error.log
   ```
   Should stop increasing after the fix.

## Why Not Just `json_schema`?

Ollama's OpenAI-compatible API does not implement the `response_format` / `json_schema`
feature that OpenAI's SDK `parse()` method uses. The Ollama team has flagged this as
a known limitation — Ollama supports `json_object` mode (response_format type = object)
but not `json_schema` mode (type = json_schema with full schema body).

## How Honcho's Code Handles This

In `src/llm/backends/openai.py`, the `_structured_output_mode()` method reads from
`extra_params`:

```python
def _structured_output_mode(extra_params):
    return extra_params.get("structured_output_mode")
```

When set to `"json_object"`:
1. `_apply_json_object_mode()` injects the schema into the first system message
2. Sets `response_format = {"type": "json_object"}` in the request
3. Falls back to `_parse_or_repair_structured_content()` on the response

When `structured_output_mode` is `None` (the default):
1. Sends `response_format=PromptRepresentation` → `parse()` → Ollama ignores it
2. Falls to `BadRequestError` handler → returns empty PromptRepresentation
3. Or silently returns markdown prose that fails validation → `zero observations`

## Test: Before vs After Raw Response

To verify whether a model responds in JSON, send a simple query directly to Ollama:

```bash
curl -s http://localhost:11434/v1/chat/completions -d '{
  "model": "qwen3.5:4b-mlx",
  "messages": [{"role": "user", "content": "Name 3 colors in JSON array."}],
  "temperature": 0.1,
  "max_tokens": 100
}' | python3 -m json.tool
```

With `json_object` mode: model returns `["red", "blue", "green"]`
Without: model returns `Here are 3 colors:\n1. Red\n2. Blue\n3. Green`

## Token Limit: The Second Half of the Problem

After applying `structured_output_mode=json_object`, the "Repair failed" errors
stop — but **zero observations may still occur** if the model is a **thinking model**
(e.g. `qwen3.5:4b-mlx`). Thinking models spend output tokens on internal reasoning
before producing the final JSON. If `max_output_tokens` is too low, **all tokens are
consumed by thinking** and the model hits `finish_reason: length` before emitting
any JSON.

### Symptom After json_object Fix

```
WARNING - Deriver generated zero observations for messages 2154:2155 in ...
INFO - PERFORMANCE ... | llm_call_duration=99344ms | observation_count=0
```

**No "Repair failed" error** — but still zero observations. The Summary module
also shows: `Generated summary is empty (finish_reasons=['length'])`.

### Token Budget Flow

```
max_output_tokens = 2500 (old default)
  └─ thinking tokens: ~2500 (model thinks until limit)
  └─ JSON output tokens: 0 (nothing left)
  → finish_reason: "length" → empty response → zero observations
```

### Fix: Raise Token Limits in config.py

Honcho's `config.py` has **hard上限 limits** (`le=100_000`) on several token fields.
To set 256K, first raise the validators, then set the defaults:

**Fields to update in `/Users/USERNAME/honcho/src/config.py`:**

| Field | Old `le=` | New `le=` | Old Default | New Default |
|-------|-----------|-----------|-------------|-------------|
| `LLM.DEFAULT_MAX_TOKENS` | `le=100_000` | `le=300_000` | 2500 | 256000 |
| `DIALECTIC.MAX_OUTPUT_TOKENS` | `le=100_000` | `le=300_000` | 8192 | 256000 |
| `SUMMARY.MAX_TOKENS_SHORT` | `le=10_000` | `le=300_000` | 1000 | 256000 |
| `SUMMARY.MAX_TOKENS_LONG` | `le=20_000` | `le=300_000` | 4000 | 256000 |
| `ConfiguredModelSettings.max_output_tokens` | `le=100_000` | `le=300_000` | None | None (uses DEFAULT) |

> **Why `le=300_000` not `le=256_000`?** Pydantic's `Field(le=N)` is inclusive
> upper bound. Setting 300K gives headroom above 256K.

**Deriver** doesn't have its own `max_output_tokens` — it falls back:
```python
max_tokens = base_model_config.max_output_tokens or settings.LLM.DEFAULT_MAX_TOKENS
```
So setting `LLM.DEFAULT_MAX_TOKENS=256000` covers Deriver automatically.

### Verify After Restart

```bash
cd /Users/USERNAME/honcho && .venv/bin/python -c "
import os; os.chdir('/Users/USERNAME/honcho')
from dotenv import load_dotenv; load_dotenv()
from src.config import settings
print(f'LLM.DEFAULT_MAX_TOKENS:       {settings.LLM.DEFAULT_MAX_TOKENS:>10,}')
print(f'DIALECTIC.MAX_OUTPUT_TOKENS:   {settings.DIALECTIC.MAX_OUTPUT_TOKENS:>10,}')
print(f'SUMMARY.MAX_TOKENS_SHORT:      {settings.SUMMARY.MAX_TOKENS_SHORT:>10,}')
print(f'SUMMARY.MAX_TOKENS_LONG:       {settings.SUMMARY.MAX_TOKENS_LONG:>10,}')
print(f'DERIVER (fallback to LLM):     {settings.DERIVER.MODEL_CONFIG.max_output_tokens or settings.LLM.DEFAULT_MAX_TOKENS:>10,}')
"
```

Expected: all values show `256,000`.

> **Pitfall:** `config.py` changes require Honcho restart — the Python module
> is loaded at process startup. `.env` changes alone take effect on restart too,
> but `config.py` changes are NOT hot-reloaded even with `--reload`.

## Second-Level Diagnosis: Thinking-Mode Token Consumption

After fixing `structured_output_mode=json_object`, if Deriver STILL produces zero observations but the "Repair failed" errors stop, the model may be consuming all its output tokens on internal thinking before producing JSON.

### Symptoms

```
WARNING - Deriver generated zero observations for messages 2150:2153 in ...
INFO - PERFORMANCE minimal_deriver_2153_USERNAME | llm_call_duration=373199ms | observation_count=0
INFO - Generated summary is empty (finish_reasons=['length']). Falling back to basic summary.
```

Key indicators:
- **`finish_reasons=['length']`** — model hit max_tokens, didn't complete output
- **`observation_count=0`** — nothing was generated
- **llm_call_duration = 99-373 seconds** — model is running internal thinking
- **No "Repair failed"** — the json_object mode is working, model just returns empty response

### Root Cause

Some models (notably `qwen3.5:4b-mlx`) have a built-in **thinking mode** triggered by complex instructions. The model:

1. Receives the structured output instruction (schema embedded in system prompt)
2. Spends all available output tokens on internal reasoning/thinking
3. Runs out of output token budget → `done_reason='length'`, response is empty string
4. Honcho gets `{"response": "", "thinking": "Thinking Process..."}` → zero observations

This is visible in direct Ollama API tests:
```json
{"response":"", "thinking":"Thinking Process:", "done_reason":"length"}
```

The `qwen3.5:4b-mlx` model on Apple Silicon (19 GB VRAM) uses its large 65536 context window aggressively, running extended thinking loops on structured tasks.

### Fix Options

1. **Switch model** — Choose a model without aggressive thinking mode:
   - `deepseek-r1:8b` — focused reasoning, produces output
   - `llama3.2:3b` — simple structured output
   - `qwen2.5:7b` — good JSON mode support, no excessive thinking

2. **Increase max_output_tokens** — Set `MAX_OUTPUT_TOKENS` in `.env`:
   ```env
   DERIVER_MODEL_CONFIG__MAX_OUTPUT_TOKENS=4096
   ```
   This gives the model more room to think AND produce JSON. Risk: thinking may still consume all tokens.

3. **Use remote API model instead** — Nvidia NIM or OpenRouter models (non-local) tend to be more token-efficient on structured tasks.

### Diagnosis Tip: Exact Model Behavior

To see exactly what the model returns (not just Honcho's interpretation), capture the raw Ollama response when Honcho calls it. Since Honcho's deriver doesn't log raw responses, check:

```bash
# If Honcho runs on Ollama, check Ollama's own logs
grep "response" ~/.ollama/logs/server.log 2>&1 | tail -5
# Or check Honcho deriver log for performance metrics
grep "observation_count=0" ~/.hermes/logs/honcho-deriver.error.log | tail -5
```

## Direct API Test Method

To verify whether the `structured_output_mode=json_object` fix actually changes model behavior, test directly against Ollama's API:

```bash
# Test WITH json_object mode (simulates Honcho's fix):
curl -s http://localhost:11434/api/chat -d '{
  "model": "qwen3.5:4b-mlx",
  "messages": [
    {"role": "system", "content": "You must respond with a single JSON object. Extract explicit facts from the conversation below."},
    {"role": "user", "content": "This is a test message."}
  ],
  "stream": false,
  "format": "json",
  "options": {"temperature": 0.1, "num_predict": 200}
}'
```

- If `format: json` is set (Ollama's native JSON mode) and model returns valid JSON → the fix is working
- If response is empty or thinking-only → model has a thinking-token problem

## Historical Context

- **2026-06-28** — First observed: Gemma 4 models fail on structured output.
  Initially attributed to model bugs (`We{...` prefix, `finish_reasons=['length']`).
  Mitigation: switched to `qwen3.5:4b-mlx`.
- **2026-07-08/09** — `qwen3.5:4b-mlx` also fails on Deriver, producing 21+
  consecutive "zero observations" batches. Root cause identified: missing
  `structured_output_mode=json_object` in `.env`. Fix applied to all 9 model configs.
- **2026-07-09 (continued)** — After `json_object` fix, "Repair failed" errors stopped,
  but thinking-mode token consumption on `qwen3.5:4b-mlx` still prevents observation
  generation. Second-level diagnosis added. Sensitivity: user respects model intelligence
  and expects infrastructure/config-level analysis, not "model is broken" conclusions.
- **2026-07-09** — After `json_object` fix, zero observations **persisted**.
  Root cause: `qwen3.5:4b-mlx` is a thinking model consuming all 2500 output tokens
  on reasoning, leaving none for JSON. Fix: raised `config.py` hard limits from
  `le=100_000` to `le=300_000` and set all defaults to 256000.