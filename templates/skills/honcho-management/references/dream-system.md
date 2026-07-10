# Dream System — Architecture & Configuration

## Overview

Honcho's Dream mechanism is inspired by human sleep: during idle periods, the system runs two specialized LLM agents to consolidate accumulated observations into higher-order knowledge.

## Specialists

### Deduction Specialist (`DeductionSpecialist`)

- **Goal:** Derive logical conclusions from existing observations
- **Capabilities:**
  - Logical implication (A ∧ B → C)
  - Knowledge update (old fact superseded by new → delete old, create new)
  - Contradiction detection (flag conflicting facts)
  - Peer card updates (only stable identity markers — behavioral patterns stay as observations)
- **Max iterations:** 12
- **Max output tokens:** 8192

### Induction Specialist (`InductionSpecialist`)

- **Goal:** Find patterns across multiple observations
- **Capabilities:**
  - Pattern detection ("Buğra always does X when Y")
  - Generalization from specific instances
  - Behavioral tendency inference
- **Max iterations:** 10
- **Max output tokens:** 8192
- **Does NOT** update peer card (patterns ≠ identity markers)

### Execution Order

```
1. [Optional] Surprisal sampling → interesting observations as hints
2. Deduction runs → creates deductive observations + updates peer card
3. Induction runs → sees deduction's new observations, finds patterns
```

## Configuration (.env)

```env
# Global toggle
DREAM_ENABLED=true

# Trigger thresholds
DREAM_DOCUMENT_THRESHOLD=50          # explicit docs needed to trigger
DREAM_MIN_HOURS_BETWEEN_DREAMS=8      # cooldown between dreams
DREAM_IDLE_TIMEOUT_MINUTES=60         # wait for idle before executing

# Model configs (each needs API_KEY_ENV!)
DREAM_DEDUCTION_MODEL_CONFIG__TRANSPORT=openai
DREAM_DEDUCTION_MODEL_CONFIG__MODEL=google/gemma-4-31b-it:free
DREAM_DEDUCTION_MODEL_CONFIG__OVERRIDES__BASE_URL=https://openrouter.ai/api/v1
DREAM_DEDUCTION_MODEL_CONFIG__OVERRIDES__API_KEY_ENV=OPENROUTER_API_KEY

DREAM_INDUCTION_MODEL_CONFIG__TRANSPORT=openai
DREAM_INDUCTION_MODEL_CONFIG__MODEL=google/gemma-4-31b-it:free
DREAM_INDUCTION_MODEL_CONFIG__OVERRIDES__BASE_URL=https://openrouter.ai/api/v1
DREAM_INDUCTION_MODEL_CONFIG__OVERRIDES__API_KEY_ENV=OPENROUTER_API_KEY
```

## Observation Levels

| Level | Source | Description |
|-------|--------|-------------|
| `explicit` | Deriver (automatic from messages) | Raw facts extracted from conversation |
| `deductive` | Deduction specialist | Logical conclusions from explicit facts |
| `inductive` | Induction specialist | Patterns across multiple observations |

## Queue Format

Dream work units use this key format:
```
dream:omni:{workspace}:{observer}:{observed}
```

## Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| No deductive/inductive docs ever created | Dream not enabled or threshold not reached | Check `DREAM_ENABLED`, lower `DOCUMENT_THRESHOLD` |
| Dreams scheduled but never execute | `IDLE_TIMEOUT_MINUTES` too high, or new messages keep resetting the timer | Lower to 5 min for testing |
| Dreams execute but produce no output | API key missing on Dream models | Add `API_KEY_ENV` to deduction/induction configs |
| Queue shows `processed=t` but no new docs | Specialist ran but found nothing actionable (all observations already consolidated) | Normal — means knowledge is current |

## Session History

| Date | Event |
|------|-------|
| 2026-06-30 | Investigated Dream mechanics. Found 4 collections had crossed threshold (62-1294 explicit docs) but no deductive/inductive observations existed. Root cause: Dream models were missing `API_KEY_ENV` (same issue as Dialectic). Fixed by adding API_KEY_ENV to all Dream configs. Dreams had executed (queue showed `processed=t`) but silently failed due to 401 errors. |
