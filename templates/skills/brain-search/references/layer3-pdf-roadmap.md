# Layer 3 — Reference Library Architecture (IMPLEMENTED)

> **Status:** IMPLEMENTED ✅
> **Date:** 2026-07-08 (research), 2026-07-09 (implementation)
> **Validated with:** Prana_and_Pranayama.pdf (1.4MB, 338 pages, 627 chunks)

## Quick Reference: Add a Source for an Agent

```
1. User: "I want to add this PDF to Maya's sources"
2. Agent: Place file in → references/sources/maya/<filename>.pdf
3. Agent: Update references/sources/maya/index.md (add link + description)
4. git add + git commit (post-commit hook auto-indexes)
5. Verify: index_brain.py --search "topic" --profile maya --show-content
   → check: page numbers appear in output (e.g. "pg.285")
   → check: source_type='pdf', agent_profile='maya'
```

## Current Architecture

### Directory Structure

```
~/brain/references/sources/
  ├── index.md              ← master index (no frontmatter!)
  ├── shared/               ← all agents access (profile=shared)
  │   └── index.md
  ├── ayda/                 ← orchestrator-specific
  │   └── index.md
  ├── alex/                 ← PM-specific
  │   └── index.md
  ├── sage/                 ← BS-specific
  │   └── index.md
  └── maya/                 ← PGM-specific
      ├── index.md
      └── Prana_and_Pranayama.pdf   ← example added 2026-07-09
```

**Key rule:** Every subdirectory MUST have an `index.md` with NO frontmatter
(OKF reserved file rule). The validator (`validate.py`) catches this.

### File Type Support

| Type | Ext | Extraction Library | Chunking | Page Tracking |
|------|-----|--------------------|----------|--------------|
| Markdown | .md | Direct read | Header-based | N/A |
| PDF | .pdf | PyMuPDF4LLM | Header-based | ✅ fingerprint match |
| Text | .txt | Direct read | Header-based | N/A |
| Transcript | .srt/.vtt | Timestamp strip | Header-based | N/A |

### Profile Derivation (how `agent_profile` is assigned)

- `references/sources/maya/file.pdf` → `agent_profile = 'maya'`
- `references/sources/shared/file.md` → `agent_profile = 'shared'`
- Any file NOT under `references/sources/` → `agent_profile = 'shared'`
- `_derive_profile()` function in `index_brain.py` handles this by path inspection

### Search Behavior

| `--profile` value | Returns chunks from | Use case |
|------------------|---------------------|---------|
| `shared` (default) | `agent_profile = 'shared'` only | Brain vault markdown |
| `maya` | `agent_profile IN ('maya', 'shared')` | Maya's sources + brain |
| `all` | Every chunk regardless of profile | Cross-agent discovery |

### Citation Format

Search results include:
```
[1] references/sources/maya/Prana_and_Pranayama.pdf (chunk 489)
    Similarity: 75.5%  [profile=maya, type=pdf, pg.285]
```

Agent formats: *"Kapalabhati tekniği: ... (Kaynak: Prana_and_Pranayama, s. 285)"*

## Known Patterns & Pitfalls (from implementation)

### SQL parameter pinning for `--profile`

When the SQL query constructs `agent_profile IN (%s, 'shared')` with psycopg,
you MUST use an f-string for the profile value, NOT a placeholder:

```python
# ✅ CORRECT
sql = f"""SELECT ... WHERE agent_profile IN ({profile!r}, 'shared') ...
ORDER BY embedding <=> %s::vector LIMIT %s;"""
params = (emb_str, emb_str, top_k)

# ❌ WRONG — causes "4 placeholders but 5 parameters"
sql = """... WHERE agent_profile IN (%s, 'shared') ...
ORDER BY embedding <=> %s::vector LIMIT %s;"""
params = (emb_str, profile, emb_str, emb_str, top_k)  # 5 params for 4 %s
```

psycopg counts `%s` placeholders strictly. String interpolation for the profile
name (which is a known-safe string) is the correct approach here.

### `index.md` files MUST NOT have frontmatter

The OKF validator rejects YAML frontmatter in `index.md` files. When creating
sources subdirectories, write plain markdown without `---` blocks.

### PDF page numbers are approximate (±1 page)

Page number detection uses fingerprint matching: first 50 chars of each chunk
are matched against per-page text extracted by PyMuPDF. Cross-page content or
empty pages can throw off the assignment by 1 page. Always verify by reading
the chunk content.

### Large PDF index is slow on first build

- PyMuPDF4LLM extraction ~3-5s/page
- 338-page PDF took ~60s first time
- Subsequent `--update` runs: instant (hash check)
- Full `--rebuild` with all brain + PDFs: ~90s total

## Original Research (kept for reference)

The alternatives evaluation below was done before implementation and informed
the PyMuPDF4LLM + pgvector approach. The session's implementation followed
the "A" path (extend existing `index_brain.py`) rather than adding a framework.

### Alternatives Evaluated

| Solution | Type | Fit | Finding |
|----------|------|-----|---------|
| AnythingLLM | Full RAG app | ❌ | Desktop app, not Hermes-native |
| PrivateGPT | Full RAG app | ❌ | Separate FastAPI service |
| Open WebUI | Full RAG app | ❌ | ChromaDB, weakest citations |
| LlamaIndex | Framework | ⚠️ | Overkill for 1-file pipeline |
| LangChain | Framework | ⚠️ | Framework overhead unnecessary |
| RAGFlow | Deep doc processing | ⚠️ | Docker-based 9GB image |
| **PyMuPDF4LLM** | Library | ✅ | **Chosen — quality over size** |
| txtai | All-in-one | ❌ | Own vector DB conflicts with pgvector |
| LightRAG | Lightweight | ❌ | Own storage, conflicts |
| Hermes #844 | Feature request | ⏸️ | We use pgvector, not sqlite-vec |

### Why `--profile` was added

Hermes Agent has issue #844 for a native knowledgebase RAG system (sqlite-vec + FTS5).
Our `agent_profile` column + `--profile` filter implements a cleaner version of the
same concept using pgvector — already running, more powerful, zero new infrastructure.