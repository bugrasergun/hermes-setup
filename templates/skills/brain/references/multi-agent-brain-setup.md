# Multi-Agent Brain Architecture

This reference documents how multiple Hermes profiles (agents) share the `~/brain/` vault.

## Agent → Directory Access Matrix (Updated 2026-07-05)

| Directory | Ayda | Alex (PM) | Sage (BS) | Maya (PGM) |
|-----------|------|-----------|-----------|------------|
| self/ | ✅ RW | ✅ | ✅ | ✅ RW (health, life context) |
| agents/index.md | ✅ | ✅ | ✅ | ✅ |
| agents/rules.md | ✅ | ✅ | ✅ | ✅ |
| agents/platforms/ | ✅ | ✅ | ✅ | ✅ |
| projects/ (ALL) | ✅ | ✅ | ✅ | ❌ (relevant only) |
| projects/assistio/pm/ | ✅ | ✅ RW | ❌ | ❌ |
| projects/assistio/bs/ | ✅ | ❌ | ✅ RW | ❌ |
| projects/assistio/pgm/ | ✅ | ❌ | ❌ | ✅ RW |
| tech/ | ✅ | ✅ | ✅ | ✅ |
| learning/ | ✅ | ✅ | ✅ | ✅ |
| health/ | ✅ | ❌ | ❌ | ✅ RW |
| finance/ | ✅ | ❌ | ❌ | ✅ RW |
| growth/ ✦ | ✅ | ❌ | ❌ | ✅ RW |
| network/ | ✅ | ✅ | ✅ | ✅ |
| playbooks/ | ✅ RW | ✅ | ✅ | ✅ |
| reports/ | ✅ RW | ✅ | ✅ | ✅ |
| references/ | ✅ | ✅ | ✅ | ✅ |

✅ = Read   ✅ RW = Read+Write   ❌ = Skip

## Directory Restructuring History (2026-07-05)

### What changed
1. **`self/rules.md` → `agents/rules.md`** — Vault rules moved from owner profile to agent catalog. `self/` is now Buğra's personal profile only.
2. **`growth/` created** — New workspace for Maya (PGM). Contains: `diagnostics/`, `habits/`, `reviews/`, `routine/`. Each subdir has its own `index.md` (OKF compliance).
3. **`self/health-context.md` + `self/life-context.md`** — New files. Health/life context = Buğra's reference (Maya reads, doesn't write routine data here). Routine data goes to `growth/routine/`.
4. **`playbooks/` refined** — SOP-only now. Personal routines removed. `playbooks/daily-routine.md` (placeholder template) deleted. Personal routines → `growth/routine/`.
5. **`health/` and `finance/` ownership clarified** — Maya owns writes. Index files updated to note Maya ownership.

### Why `growth/` vs `self/`
- `self/` = **who Buğra is** (identity, goals, values, preferences, health/life context as reference)
- `growth/` = **Maya's working output** (diagnostics she ran, habits she's tracking, reviews she wrote, daily routine logs)
- Key distinction: `self/health-context.md` = "Buğra has a past knee injury, prefers gym" (stable reference). `health/fitness/program.md` = "This week's program" (changing output).

### Why `playbooks/` is SOP-only
- User explicitly said: "Playbooks genel olarak SOP'ler ve diğer günlük prosedürler için düşünülmüş genel bir klasör yapısı. Yani ajanlar yeni bir şey yapacakları zaman buradan o işin standartlarını öğrenmeleri için düşüldü."
- Personal routines are NOT SOPs — they change and need tracking. They go to `growth/routine/`.

## Key Migration Steps (Historical)

1. ~~Delete `agents/agents.md`~~ (done — identity → SOUL.md)
2. ~~Rename `self/context.md` → `self/rules.md`~~ (done)
3. **NEW**: Move `self/rules.md` → `agents/rules.md` (2026-07-05)
4. **NEW**: Create `growth/` with full subdir structure + all index.md files (2026-07-05)
5. **NEW**: Create `self/health-context.md` and `self/life-context.md` skeletons (2026-07-05)
6. **NEW**: Delete `playbooks/daily-routine.md` (was placeholder template, not real routine)
7. **NEW**: Update `playbooks/index.md` to SOP-only definition (2026-07-05)
8. Update brain skill Directory Map, Content Type map, Decision Tree, Pre-Vault Checklist

## Honcho Integration

Each profile gets a unique `aiPeer` in `~/.hermes/honcho.json`:
- `peerName: "USERNAME"` → shared user memory (ALL agents)
- `aiPeer` per profile → isolated AI memory

Sync with: `hermes honcho sync`
