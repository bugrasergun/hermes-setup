---
name: brain
description: >
  Complete operator for the ~/brain/ OKF knowledge vault. Handles reading, writing,
  migration, validation, git sync, and session reporting. This is the single source
  of truth skill — obsidian skill covers read/write of individual files, brain-search
  covers semantic discovery, but this skill governs ALL vault operations end-to-end.
platforms: [linux, macos, windows]
triggers:
  - /brain
  - brain
  - beyin
  - kaydet
  - hatırla

trigger_keywords:
  - brain
  - beyin
  - bilgi
  - belge
  - doküman
  - döküman
  - kavram
  - kavram dosyası
  - index
  - proje hakkında yaz
  - bunu brain'e yaz
  - bunu beyne yaz
  - brain'e ekle
  - beyne ekle
  - knowledge vault
  - vault
  - rapor
  - günlük
  - haftalık
  - aylık

---

# Brain Vault — Complete Operator

This skill governs **all** operations on `~/brain/` — the shared, git-tracked OKF v0.1
knowledge bundle used by **all Assistio agents** (Ayda, Product Manager, Business Strategist,
Personal Growth Mentor). It is the single source of truth.

**Related skills (do NOT modify):**
- `obsidian` — detailed OKF format rules, wikilink conventions, report frontmatter templates
- `brain-search` — semantic vector search, Layer 3 source discovery

This skill **complements** them with the complete picture: check-first patterns, git push,
report index updates, and dangerous pitfalls.

> **Session origin:** This skill was patched on 2026-07-02 to add the SOUL.md vs Skills
> Agent Knowledge Architecture section (Section 7.5). The user explicitly said:
> "Skill dosyalarının içeriklerinin soul.md'ye olduğu gibi transfer edilmesini istemiyorum."
> → SOUL.md = identity only; Skills = capabilities. Never merge them.

### References

- `brain` references: traversal protocol, Hermes integration, migration guide (in `brain/references/`)
- `references/multi-agent-brain-setup.md` — access matrix, directory structure, migration steps for multi-agent brain architecture
- `references/agent-profile-creation.md` — **step-by-step workflow for creating new Assistio agent profiles** (consult this BEFORE creating any new agent — covers profile creation, SOUL.md authoring, skills installation, Honcho sync, naming conventions, and the symlink pitfall)

---

## Vault Path

```
~/brain/
```

Resolve to absolute path before any file operation. Never pass `~` literally to tools.

The `BRAIN_PATH` env variable is the canonical source — expand it before use. Never pass
`$BRAIN_PATH` as a literal string to `read_file` or `write_file`.

> **iCloud warning:** Do not move the vault to iCloud-synced paths. Vault is local disk only.

### Pre-Vault Checklist

Before processing any vault operation, always load:
1. `~/brain/agents/rules.md` — generic vault rules (shared by all agents)
2. `~/brain/index.md` — top-level directory map

> `self/` is now Buğra's personal profile only (identity, goals, values, preferences, health-context, life-context).
> Vault rules live in `agents/rules.md`.

### User Preferences (Buğra)

- **No premature optimization** — don't over-engineer directory structures upfront. Start flat, split when content grows. Observe before adding detail layers.
- **Source over memory** — always read files before answering; never rely on memory alone for domain questions.
- **Incremental detail** — when uncertain whether to add more detail (e.g. category descriptions in index.md), defer. Revisit only when the agent actually struggles to find things.
- **Plan first, then implement** — before starting any agent-workflow task (creating a new agent, refactoring infrastructure, etc.), lay out the full architecture and get user approval. Never jump to implementation without sign-off. The workflow is: "önce kurgula, sonra plan yap, sonra implemente et, onaysız başlama."
- **Skill files in English** — all SKILL.md files must be written in English. Do NOT write skills in Turkish; the agent's Turkish has spelling and grammar errors. English is the agent's stronger language. This applies to all `assistio-*` domain skills, any new skills created, and skill updates/patches.

---

## Section 1 — CHECK FIRST Pattern (MANDATORY)

**Before ANY file write or directory creation**, run this checklist:

1. **List existing files** — `search_files(target="files", path="~/brain/<subdir>", pattern="*.md")`
2. **Read the subdirectory's `index.md`** — if it exists, understand current structure
3. **Read existing concept files** — if writing something related, read what's already there
4. **Never overwrite an existing concept** — use `patch` for edits, never `write_file`
5. **Duplicate check** — verify no similar file exists (same topic, different name)
6. **No Manual Traversal for Searching**: Do not manually search folders or read index files to find where information is located. You MUST use the `brain-search` skill to execute a semantic search first.

> **Critical Pitfall:** `search_files(pattern="reports")` returns 0 for folders — it searches
> **file names**, not directory names. Always traverse index structure to discover directories.

> **Memory is not truth.** Even if you "remember" a directory doesn't exist, CHECK. Especially
> for `reports/`, `projects/`, `tech/` — these have been migrated multiple times.

---

## Section 2 — Reading & Traversal

### Search

Use `search_files` with:
- `target: "files"` + `pattern: "*.md"` — list files in a subdirectory
- `target: "content"` + `file_glob: "*.md"` — search inside file contents

> **Pitfall:** `search_files(pattern="reports")` returns 0 for folders — searches **file names**,
> not directories. Always traverse index structure to discover directories.

### Progressive Traversal

Never load the whole vault. Traverse:

1. `~/brain/index.md` — top-level categories
2. `<subdirectory>/index.md` — contents of one category
3. Load only the specific files related to the query

### Cross-Link Extraction (Depth 1)

When you load a concept file:
1. Extract any relative markdown links in the body
2. Fetch those linked concepts immediately if they are critical to the current task
3. Stop at depth 1 unless explicitly requested to prevent token overflow

### Directory Map

| Path | Purpose | Write Owner |
|---|---|---|
| `self/` | Buğra's personal profile: identity, goals, values, preferences, health & life context | Buğra + Maya (updates) |
| `agents/` | Agent catalog, platform configs, **vault rules** (rules.md) | Ayda (infra) |
| `projects/` | Active and archived projects (PM + BS read all; PGM reads relevant) | PM + BS |
| `tech/` | Dev environment, languages, frameworks | Any agent |
| `learning/` | Books, courses, research | Any agent |
| `health/` | Fitness program, nutrition plan, health metrics | **Maya** |
| `finance/` | Budget, subscriptions, investments, monthly reviews | **Maya** |
| `growth/` ✦ | **NEW** — Maya PGM workspace: diagnostics, habits, reviews, routine tracking | **Maya** |
| `network/` | People and organizations | Any agent |
| `playbooks/` | SOPs, runbooks, operational procedures (agent reference only) | Ayda (infra) |
| `reports/` | Daily / weekly / monthly session reports | Any agent |
| `references/` | Glossary, standards, service notes | Any agent |

> **Key changes (2026-07-05):**
> - `self/rules.md` → `agents/rules.md` (vault rules moved to agent catalog)
> - `self/` is now Buğra's personal profile only (identity, goals, values, preferences, health-context, life-context)
> - `growth/` created — Maya's workspace for diagnostics, habits, reviews, and routine tracking
> - `playbooks/` refined to SOP-only (personal routines moved to `growth/routine/`)

> **Architectural principle — "WHO vs WHAT":** `self/` holds WHO the owner is (permanent profile, identity, health/life context — agents read this as reference). `growth/` holds WHAT an agent is working on right now (mutable diagnostics, habit logs, reviews, routine tracking — the agent writes new content here over time). Never mix the two: don't put a 30-day execution plan in `self/`, and don't put permanent health history in `growth/`. When a new agent domain needs a workspace, create a new top-level directory (like `growth/`), don't overload `playbooks/` or `self/`.

---

## Section 3 — Writing & Preserving (All Content Types)

### Content Type → Location Map

| Content belongs... | Store in | Write Owner |
|---|---|---|
| **Buğra's profile, goals, values, preferences, health/life context** | `self/` | Buğra + Maya |
| **Maya's growth diagnostics, habits, reviews, routine tracking** | `growth/` | Maya |
| About a **project** (overview, agents, sub-projects, decisions) | `projects/<name>/index.md` | PM + BS |
| About a **tool, language, framework, environment** | `tech/<topic>.md` | Any |
| From a **book, course, research, experiment** | `learning/<topic>.md` | Any |
| **Health, fitness, nutrition** data (program, plan, log, metrics) | `health/<topic>.md` | Maya |
| **Budget, subscription, investment, monthly review** data | `finance/<topic>.md` | Maya |
| A **person or organization** | `network/<name>.md` | Any |
| A **SOP, runbook, operational procedure** (agent reference) | `playbooks/<topic>.md` | Ayda |
| **Agent-specific reference sources** (PDFs, transcripts, text) | `references/sources/<agent>/` | Any agent (place in own folder) |
| **Glossary, standard, reference** | `references/<topic>.md` | Any |
| **Agent platform configs** | `agents/platforms/` | Ayda |
| A **session summary** (this happened today...) | `reports/daily/YYYY-MM-DD.md` | Any |

### Decision Tree: "Bu nereye?"

1. "Bu bir **proje** hakkında" → `projects/<name>/index.md`
2. "Bu bir **teknik bilgi**" → `tech/<topic>.md`
3. "Bu bir **öğrenim/araştırma**" → `learning/<topic>.md`
4. "Bu bir **kişi/organizasyon**" → `network/<name>.md`
5. "Bu bir **SOP/prosedür** (agent reference)" → `playbooks/<topic>.md`
6. "Bu bir **hedef, değer veya tercih**" → `self/goals.md`, `self/values.md`, `self/preferences.md`
7. "Bu **sağlık bağlamı** (geçmiş, kısıt, tercih)" → `self/health-context.md`
8. "Bu **yaşam bağlamı** (rutin, enerji, commitments)" → `self/life-context.md`
9. "Bu **Maya'nın çalışma çıktısı** (teşhis, alışkanlık, review, rutin takip)" → `growth/<subdir>/`
10. "Bu **sağlık verisi** (program, plan, log, metrics)" → `health/<subdir>/`
11. "Bu **finans verisi** (bütçe, review, overview)" → `finance/<topic>.md`
12. "Bu **bugün/şimdi olan bir şey**" (geçici) → session_search (memory'ye kaydetme)
13. "Bu **bugün/şimdi olan bir şey**" (kalıcı) → `reports/daily/YYYY-MM-DD.md`
14. "Bu bir **terim/standart**" → `references/<topic>.md`

### Writing New Notes — Full Flow

1. **CHECK FIRST** (Section 1)
2. Determine content type → find target subdirectory from map above
3. Filename: `kebab-case.md`
4. Write with `write_file` — include OKF frontmatter (see `obsidian` skill for format)
5. **Update `index.md`** — append link to the new note
6. **Update parent index** — if new project/domain, add to section index
7. **Validate** — `python3 ~/brain/scripts/validate.py`
8. **Commit & Push**
9. **Re-index** — Automatic via git `post-commit` hook. To verify or force:
   ```bash
   /Users/USERNAME/honcho/.venv/bin/python /Users/USERNAME/brain/scripts/index_brain.py --update
   ```

### Wikilinks & Link Format

Obsidian wikilinks (`[[Note Name]]`) are supported in `~/brain/`.

**Required Obsidian setting (one-time):**
`Settings → Files & Links → New link format` → set to **"Path from current file"**

When **agents write cross-links**, always use **relative markdown links**:

- ✅ `[Profile](../self/profile.md)` — preferred for agent-written links
- ✅ `[[../self/profile]]` — correct wikilink after Obsidian setting
- ❌ `[Profile](/Users/USERNAME/brain/self/profile.md)` — never absolute

### Append / Edit a Note

- Read the target note with `read_file` first
- Use `patch` for anchored edits (stable context)
- Use `write_file` to rewrite when change is structural
- Never use shell heredocs or `echo` — use file tools

### Frontmatter — Reserved Files (NO frontmatter!)

- `index.md` — directory index, plain markdown only
- `log.md` — append-only log, plain markdown only

### Frontmatter — Concept Files

```yaml
---
type: Project | Person | Task | Note | Guide
title: Human-readable
description: One-line
tags: [tag1, tag2]
timestamp: 'YYYY-MM-DDTHH:MM:SS+03:00'
---
```

### AGENTS.md Pitfall

Do **not** create `AGENTS.md` in the brain root. The OKF validator treats it as a concept file
and errors on missing frontmatter. Put root-level guide content in `index.md` instead.

> **Validator error:** "Reserved file must NOT contain YAML frontmatter" = you added
> frontmatter to an `index.md`. Strip it entirely.

### Inner Link Format

- ✅ `[Profile](../self/profile.md)` — preferred for agent links
- ❌ `[Profile](/Users/USERNAME/brain/self/profile.md)` — never absolute

---

## Section 4 — Migration Protocol (External → Brain)

When importing from `~/Documents/` or external URLs:

1. **Read all source files first** — batch-read before writing anything
2. **Classify by domain** — map each file to correct subdirectory
3. **CHECK FIRST** — verify no similar concept exists in target location
4. **Convert to clean markdown** with OKF frontmatter
5. **Split large documents** by topic when they cover multiple concepts
6. **Create/update index files** — each subdirectory gets an `index.md`
7. **Update root `index.md`** and section indexes
8. **Validate** — `python3 ~/brain/scripts/validate.py` — fix ALL errors
9. **Commit & Push**
10. **Memory update** — save durable facts to memory, not task details

---

## Section 5 — Session Reports

Reports live under `reports/` with strict naming:

| Type | Path | Frontmatter type |
|---|---|---|
| Daily | `reports/daily/YYYY-MM-DD.md` | `Daily Report` |
| Weekly | `reports/weekly/YYYY-MM_W[N].md` | `Weekly Report` |
| Monthly | `reports/monthly/YYYY-MM.md` | `Monthly Report` |

### Daily Report Frontmatter

```yaml
---
type: Daily Report
title: Günlük Rapor — DD Ay YYYY
description: One-line summary of the session.
tags: [report, daily, YYYY-MM]
timestamp: 'YYYY-MM-DDTHH:MM:SS+03:00'
---
```

### Weekly Report Frontmatter

```yaml
---
type: Weekly Report
title: Haftalık Rapor — DD-DD Ay YYYY
description: Weekly session metrics and decisions for DD-DD Ay YYYY.
tags: [report, weekly, YYYY-MM]
timestamp: 'YYYY-MM-DDTHH:MM:SS+03:00'
---
```

### Monthly Report Frontmatter

```yaml
---
type: Monthly Report
title: Aylık Rapor — Ay YYYY
description: Monthly summary and retrospective for Ay YYYY.
tags: [report, monthly, YYYY]
timestamp: 'YYYY-MM-DDTHH:MM:SS+03:00'
---
```

### Writing a Report (CHECK FIRST!)

1. **Check existing reports** — `search_files(target="files", path="~/brain/reports/daily", pattern="*.md")`
2. **Read `reports/daily/index.md`** — see what's already there
3. **Do NOT overwrite** — if `2026-06-29.md` exists, use `patch` to update
4. Write report with frontmatter (templates above)
5. **Append link to `reports/daily/index.md`** (and `index.md` for weekly/monthly)
6. Commit & Push

> **Pitfall:** `search_files(pattern="reports")` returns 0 — it's a directory, not a file.
> Always traverse `index.md` → `reports/index.md` → `reports/daily/index.md` first.

---

## Section 6 — Validation & Git

### Validate

```bash
cd ~/brain && python3 scripts/validate.py
```

Pass = 0 errors. Fix before committing.

### Commit & Push (ALWAYS together)

```bash
cd ~/brain && git add -A && git commit -m "docs: <description>" && git push origin main
```

Use conventional prefixes: `docs:`, `feat:`, `fix:`, `refactor:`.

> **No commit without push.** GitHub must always be current.
> **Auto re-index:** Git `post-commit` hook runs `index_brain.py --update` automatically
> when `.md`, `.pdf`, `.txt`, `.srt`, or `.vtt` files change — semantic search stays fresh
> without manual steps. Layer 3 reference sources (PDFs, transcripts) are auto-indexed too.

---

## Section 7 — Memory Management

### Memory vs Brain Durability (CRITICAL)

| Store | Durability | Use for | Will be cleaned up? |
|-------|-----------|---------|---------------------|
| **Honcho** (user peer) | Medium | User preferences, patterns, habits | Survives sessions but may be consolidated |
| **MEMORY.md** (per-profile) | Low | Temporary notes, session context, current task state | ❗ YES — auto-consolidated when char limit reached |
| **brain/** (git-tracked) | **HIGH** | **PRDs, roadmaps, MVP specs, architecture decisions** | NO — version-controlled, permanent |

**Rule:** If data must survive longer than one session, write it to `~/brain/` — NOT to MEMORY.md.

Mistakes to avoid:
- ❌ Writing a PRD draft to MEMORY.md → lost when memory fills up
- ✅ Writing a PRD draft to `projects/assistio/product-manager/prd-feature-x.md`
- ❌ Recording roadmap items in MEMORY.md → lost on consolidation
- ✅ Recording roadmap in `projects/assistio/product-manager/roadmap-q3.md`

### After Complex Tasks (5+ tool calls)

1. Summarize what changed — durable facts only
2. Add to memory: project names, architecture decisions, new patterns learned
3. **Do NOT save to:** task progress, PR numbers, session outcomes, temporary TODO state
4. **Do NOT save daily reports to memory** — they live in `reports/`

### Memory vs Reports

- **Memory:** "Assistio has 5 agents: MD Assistio, Nefes Koçu, Personal Growth Mentor, Product Manager, Business Strategist"
- **Reports:** Full session narrative with what was done, why, and what went wrong

---

## Section 7.5 — Agent Knowledge Architecture (SOUL.md vs Skills)

**Critical principle:** SOUL.md and Hermes skills serve DIFFERENT purposes and must NEVER be merged.

| Component | Purpose | Source | Location |
|-----------|---------|--------|----------|
| **SOUL.md** | Agent identity — "who I am, what I do, my principles" | agency-agents reposu (identity repo) | `~/.hermes/profiles/<name>/SOUL.md` |
| **Hermes Skills** | Technical capabilities — "how I do specific tasks" | startup-founder-skills gibi yetenek repoları | `~/.hermes/profiles/<name>/skills/` |

**Rules:**
- ❌ NEVER copy skill content into SOUL.md — SOUL.md should NOT contain PRD templates, RICE scoring formulas, or workflow steps
- ✅ SOUL.md references skills generically: "I can write PRDs using my prd-writing skill"
- ✅ Skills contain the full methodology: "8-section PRD template, assumption tracking, etc."
- ❌ NEVER treat SOUL.md as a dumping ground for every repo you find — it's identity only
- ✅ When creating a new agent profile: derive SOUL.md from identity repos (e.g. `agency-agents`), install technical skills from capability repos (e.g. `startup-founder-skills`)

**CRITICAL — Profile-specific skills vs global skills:**

| Tool | Creates in | When to use |
|------|-----------|-------------|
| `skill_manage(action='create')` | `~/.hermes/skills/` (global) | Infrastructure skills shared by all agents (e.g. `brain`, `github`) |
| `mkdir -p` + `write_file` | `~/.hermes/profiles/<name>/skills/` | Agent-specific domain skills |

**Pitfall:** `skill_manage(action='create')` always writes to `~/.hermes/skills/` (the global directory). If you create an agent-specific skill there, it becomes accessible to ALL agents — not just the intended one. For agent-specific skills, create the directory manually and use `write_file` directly into the profile's skills path.

**Profile skills directories should be REAL directories, NOT symlinks.** A symlink to global skills (e.g. `assistio -> ../../../skills/assistio`) masks where skills actually live and causes confusion when adding/removing skills. Use `mkdir -p` to create a real directory structure.

**Detect-before-write rule:** Before writing a skill into a profile's skills directory, ALWAYS check if the target path is a symlink:
```bash
ls -la ~/.hermes/profiles/<name>/skills/<category>
# If output shows '->' it's a symlink pointing to global skills
# → Remove the symlink, create a real directory, then write
```
If you write through a symlink, the file ends up in the GLOBAL skills directory, not the profile's directory. This caused a real bug in the Assistio agent setup (Sage's skills were written to global because Alex's `assistio` was a symlink).

**Exception:** The `brain` skill IS appropriate as a symlink (`ln -s ../../../skills/brain brain`) because it's a shared infrastructure skill that every agent needs.

**Pitfall:** If you get a request like "create SOUL.md from this GitHub repo" — first check whether the repo provides IDENTITY or CAPABILITIES. Identity repos → SOUL.md. Capability repos → Hermes skills. Never both in the same file.

## Section 8 — What NOT To Do

- ❌ Write files without `CHECK FIRST` — you may overwrite existing content
- ❌ Create `index.md` with frontmatter — validator will fail
- ❌ Use absolute paths in links
- ❌ Use `search_files(pattern="<dirname>")` to check if a directory exists — it won't work
- ❌ `mkdir` without checking if the path already exists
- ❌ Commit without push
- ❌ Save sensitive data (tokens, credentials, .env) to vault
- ❌ Use iCloud-synced paths — vault is local disk only (`~/brain/`)
- ❌ Guess where content belongs — use the Decision Tree in Section 3
- ❌ Create `AGENTS.md` in brain root — validator treats it as a concept file
- ❌ Write to the wrong subdirectory — `tech/` for tech, `learning/` for courses, etc.
- ❌ **Create a subdirectory without an `index.md`** — OKF requires **every** subdirectory to have its own `index.md` (no frontmatter, plain markdown listing contents). When creating multi-level structures like `growth/diagnostics/`, `growth/habits/`, `growth/reviews/`, `growth/routine/`, intermediate-level directories need their own `index.md` too, not just the root and leaves. Missing index files break traversal — agents navigating from `growth/index.md` → `growth/diagnostics/index.md` hit a dead end. User explicitly corrected this.
- ❌ **Use `playbooks/` for personal routines, habits, or tracking data** — `playbooks/` is **SOP-only** (agent reference procedures). Personal routine data belongs in `growth/routine/`, habit tracking in `growth/habits/`, accountability reviews in `growth/reviews/`. User explicitly corrected this.
- ❌ **Write SKILL.md files in Turkish** — all SKILL.md files MUST be written in English. The agent's Turkish has spelling and grammar errors; English is the agent's stronger language. This applies to all `assistio-*` domain skills, new skills created, and skill updates/patches. User explicitly corrected this: "Türkçe yazarken anlam ve imla hataları yapmışsın. Dosyaları yine teker teker değiştir." → all 4 Maya skills rewritten in English.
- ❌ Mix "WHO someone is" (identity, profile, permanent context) with "WHAT they're working on now" (current plan, log, tracking) in the same directory — `self/` holds permanent profile/context (read by agents); `growth/` holds the agent's mutable working output (written by the agent)

---

## Section 11 — Integration with brain-search

For **discovery queries** ("what does brain have about X?"), do not perform manual traversal. Pivot to the `brain-search` skill to run vector similarity searches.

### Synergy Protocol
- **Discovery Mode**: When asked to find documents or check if information exists, use `brain-search`.
- **Operation Mode**: Once `brain-search` identifies the file path, return to this `brain` skill to read, modify, validate, or commit the file.
- **Index Sync**: A git `post-commit` hook in `~/brain/.git/hooks/` automatically runs `--update` when any supported file changes in a commit. No manual indexing is required under normal circumstances, but if search results are stale, run:
  ```bash
  /Users/USERNAME/honcho/.venv/bin/python /Users/USERNAME/brain/scripts/index_brain.py --update
  ```

---

## Section 9 — Command Interface

### `/brain status`
- Run validator
- Show last 5 git log entries
- List directory structure health

### `/brain query <topic>`
- Traverse indexes
- Find matching concepts by tags/description
- Return summaries + file paths

### `/brain report [daily|weekly|monthly]`
- CHECK FIRST — list existing reports
- Create new or patch existing
- Update index
- Commit & push

---

## Section 10 — Proactive Harvesting Protocol

When you detect the following topics in chat:
1. **User Preferences:** "Bundan sonra kodları test etmeden yollama", "I prefer using x over y", "z kütüphanesini kullanma", etc. -> Target: `~/brain/self/preferences.md`
2. **Personal Updates:** Contact info, new roles, personal bio -> Target: `~/brain/self/profile.md`
3. **Project/Design Decisions:** Architecture paths chosen, tech stack additions, workflow definitions -> Target: `~/brain/projects/<project_name>/` or its index

**Procedure:**
1. **Detect & Pause:** Do not wait for the user to tell you to save it. Identify that a durable fact has emerged.
2. **Propose:** Ask the user: *"Bu bilgi önemli görünüyor. Beynime [dosya_adı](dosya_yolu) olarak kaydetmemi/güncellememi ister misin?"* showing a quick markdown draft of the change.
3. **Confirm & Write:** Upon the user's approval, run the `CHECK FIRST` protocol and write/patch the file. Commit & push the changes to sync.
