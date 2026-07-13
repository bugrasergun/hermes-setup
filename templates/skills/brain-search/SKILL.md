---
name: brain-search
description: > Semantic search across the ~/brain/ knowledge vault using vector embeddings. Finds the most relevant brain documents (markdown, PDF, transcript) for a given query by meaning, not just keywords. Supports per-agent profile filtering for Layer 3 reference sources. Uses Ollama nomic-embed-text + PostgreSQL pgvector  (same infrastructure as Honcho). Complements the `brain` skill — load `brain` for vault traversal, validation, and writing; load `brain-search` for semantic discovery. platforms: [linux, macos, windows]


triggers:
 - brain'de ara 
 - beyinde ara
 - brain search
 - brain query
 - brain'de var mı
 - beyinde var mı
 - semantic search brain
 - brain'de ne var
 - brain'de bul
 - PDF ara
 - transcript ara
 - kaynak ara
 - maya'nın kaynaklarında ara
 - alex'in kaynaklarında ara

trigger_keywords:
  - brain ara
  - beyin ara
  - semantic
  - vektör arama
  - brain search
  - brain query
  - brain'de ara
  - beyinde ara
  - brain'de var mı
  - brain'de bul
  - semantic search
  - PDF ara
  - transcript ara
  - kaynak ara
  - profile search
  - --profile

---

# Brain Semantic Search

This skill provides **semantic (vector-based) search** across the `~/brain/` knowledge vault.
It complements the `brain` skill (which handles vault operations: reading, writing, validation,
git sync) by adding the ability to **find relevant documents by meaning**, not just by filename
or keyword match.

## When to Use This Skill

| Situation | Use `brain` (manual traversal) | Use `brain-search` (semantic) |
|-----------|------------------------------|-------------------------------|
| "Brain'de Taco Bros var mı?" | ❌ Too slow — would need to read every index | ✅ One query, instant results |
| "Bu konuyu brain'e yaz" | ✅ Write + validate + commit | ❌ Not a search task |
| "Maya'nın fitness programı neydi?" | ❌ Don't know which file | ✅ Find by meaning |
| "Brain'de X konusuyla ilgili ne var?" | ⚠️ Only if you know the path | ✅ Best for discovery |
| "Bu dosyayı güncelle" | ✅ Read + patch | ❌ Not a search task |
| "Biz daha önce X'i konuşmuş muyuz?" | ❌ Brain is documents, not conversations | ⚠️ Use `session_search` for conversations, `brain-search` for documents |

**Rule of thumb:** If the question is "what do we have in brain about X?" → semantic search.
If the task is "read/write/update a specific brain file" → `brain` skill.

## Architecture

```
~brain/*.{md,pdf,txt,srt,vtt}  ->  extract (PyMuPDF4LLM for PDF)  ->  chunk
                                             |
                                    Ollama nomic-embed-text (768-dim)
                                             |
                              PostgreSQL pgvector (brain_documents table)
                                             |
                              HNSW cosine similarity index
                                             |
                              Search with --profile <agent> filter
```

- **Embedding model:** `nomic-embed-text` (768 dimensions, same as Honcho)
- **Database:** Honcho's PostgreSQL (`honcho` database, `brain_documents` table)
- **Index:** HNSW with cosine ops
- **PDF extraction:** PyMuPDF4LLM (converts PDF to markdown, preserves tables/formatting)
- **Citation:** Results include `page_num` for PDFs — agents can cite "Document, pg.47"
- **Profile filter:** `--profile maya` includes agent's sources + shared; `--profile all` = everything
- **Source types:** `markdown`, `pdf`, `txt`, `transcript` — shown in status/search results

## CLI Tool

The indexing and search tool lives at `~/brain/scripts/index_brain.py`.
It handles all file types: `.md`, `.pdf` (PyMuPDF4LLM), `.txt`, `.srt`/`.vtt`.
It must be run with Honcho's Python (which has `psycopg`, `httpx`, `pymupdf4llm`):

```bash
# Honcho venv Python (has psycopg3 + httpx + pymupdf4llm)
HONCHO_PY=/Users/USERNAME/honcho/.venv/bin/python
SCRIPT=/Users/USERNAME/brain/scripts/index_brain.py

# Full re-index (drop everything, re-insert all)
$HONCHO_PY $SCRIPT --rebuild

# Update only changed files (hash-based, all supported types)
$HONCHO_PY $SCRIPT --update

# Show index statistics (by profile + source type)
$HONCHO_PY $SCRIPT --status

# Semantic search — shared brain only (default)
$HONCHO_PY $SCRIPT --search "Taco Bros marketing strategy"

# Search with agent profile filter (agent's own sources + shared)
$HONCHO_PY $SCRIPT --search "Kapalabhati technique" --profile maya

# Search all sources (shared + all agent profiles)
$HONCHO_PY $SCRIPT --search "market validation" --profile all --top 10 --show-content
```

## Search Protocol

When performing a semantic search, follow these steps:

### Step 1: Run the Search

```bash
/Users/USERNAME/honcho/.venv/bin/python /Users/USERNAME/brain/scripts/index_brain.py \\
  --search "user's query here" --top 5 --show-content --profile <agent_or_all>
```

- Use `--show-content` to get chunk previews in the output
- Use `--profile shared` (default) for brain-only search
- Use `--profile maya` for Maya's reference sources + shared brain (Layer 3)
- Use `--profile all` to search everything
- Default top 5; increase to 10 for broader queries
- The query should capture the **meaning** the user is looking for, not just keywords

### Layer 3 Source Search

When searching for content from agent-specific reference sources (PDFs, transcripts):

1. Determine the agent profile (e.g., `maya` for fitness/health, `sage` for business)
2. Use `--profile <agent>` to include that agent's `references/sources/<agent>/` files
3. Results include `page_num` for PDF chunks — use this for citations: "Document, pg.47"
4. Always verify the cited page by reading the chunk content; do not fabricate references

### Step 2: Read the Full File

Semantic search returns **chunks**, not full files. Always read the full file for
context before answering:

```python
from hermes_tools import read_file
read_file(f"/Users/USERNAME/brain/{result['file_path']}")
```

### Step 3: Synthesize and Answer

1. Present the findings with file paths as sources
2. If multiple files are relevant, synize across them
3. Quote or reference specific sections
4. If no good results (similarity < 30%), say so — don't fabricate

### Step 4: Verify with `brain` Skill

If the search results are ambiguous or you need to understand the vault structure
better, load the `brain` skill for manual traversal.

## Index Maintenance

### When to Re-index

| Trigger | Action |
|---------|--------|
| After writing a new brain file | `--update` (indexes only the new/changed file) |
| After bulk changes (migration, multiple files) | `--rebuild` (full re-index) |
| After git pull on brain repo | `--update` (catches externally changed files) |
| User asks "brain'de ara" and search returns stale results | `--update` first, then search |
| Before a critical search (ensure freshness) | `--status` to check, `--update` if needed |

### Re-index After Writing

**CRITICAL:** After writing a new file to brain (via the `brain` skill's write workflow),
you MUST re-index so the new content is searchable:

```bash
# After commit & push in brain skill workflow:
/Users/USERNAME/honcho/.venv/bin/python /Users/USERNAME/brain/scripts/index_brain.py --update
```

This is fast — only changed files (detected by SHA-256 hash) are re-indexed.

**Auto-indexing:** Git `post-commit` hook automatically runs `--update` when any
supported file (`.md`, `.pdf`, `.txt`, `.srt`, `.vtt`) changes in a commit.

### Chunking Details

- **Strategy:** Markdown header-based (`#`, `##`, `###` split points)
- **Max chunk size:** 1500 characters (split with overlap if larger)
- **Min chunk size:** 80 characters (skip tiny fragments)
- **Overlap:** 150 characters between sub-chunks within a long section
- **Break priority:** paragraph boundary → sentence boundary → hard cut
- **PDF chunking:** PyMuPDF4LLM converts PDF to markdown, then header-based chunking
  with page number tracking (fingerprint matching against per-page text)
- **Transcript chunking:** SRT/VTT stripped of timestamps, then header-based

## How to Search from Agent Code

When you need to search brain programmatically (e.g., via `execute_code` or `terminal`):

```python
import subprocess, json

result = subprocess.run([
    "/Users/USERNAME/honcho/.venv/bin/python",
    "/Users/USERNAME/brain/scripts/index_brain.py",
    "--search", "your query here",
    "--top", "5",
    "--show-content"
], capture_output=True, text=True, timeout=30)
print(result.stdout)
```

Or via terminal:
```bash
/Users/USERNAME/honcho/.venv/bin/python /Users/USERNAME/brain/scripts/index_brain.py \
  --search "your query" --top 5 --show-content
```

## Pitfalls

1. **Stale index** — If brain files were changed externally (git pull, manual edit)
   without re-indexing, search returns old content. Run `--update` before searching
   if freshness is uncertain.

2. **Ollama must be running** — Embedding requires Ollama with `nomic-embed-text`
   model. Check: `ollama list | grep nomic-embed-text`. If missing: `ollama pull nomic-embed-text`.

3. **PostgreSQL must be running** — The `honcho` database must be accessible.
   Check: `brew services list | grep postgresql`.

4. **Honcho venv required** — The script uses `psycopg` (v3) and `httpx` which are
   only in Honcho's venv at `/Users/USERNAME/honcho/.venv/`. System Python
   does NOT have these packages.

5. **Chunk != full file** — Search returns chunks (sections of a file). Always read
   the full file with `read_file` for complete context before answering.

6. **Low similarity doesn't mean "no match"** — Brain has 125 files across diverse
   topics. A 40% similarity might be the best match for a niche topic. Check the
   actual content before dismissing results.

7. **AGENTS.md and scripts/ are excluded** — The auto-generated `AGENTS.md` and
   the `scripts/` directory (where `index_brain.py` itself lives) are not indexed.

8. **Larger queries work better** — "Taco Bros restaurant marketing strategy in Albania"
   gives better results than just "Taco Bros" because the embedding captures more
   semantic meaning.

9. **`--update` reports 0-chunk files as "new"** — Files smaller than MIN_CHUNK_CHARS
   (80 chars) or with no extractable headers produce 0 chunks. `--update` still logs
   them as "new file found" but skips indexing. This is cosmetic noise, not a bug —
   the file IS registered with a hash, it just has no searchable chunks. Don't chase
   these entries.

10. **Turkish queries work well** — `nomic-embed-text` is multilingual. Turkish
    queries (e.g., "beslenme fitness sağlık") return relevant results at ~79% similarity.
    Do not assume English-only queries are needed.

11. **Git post-commit hook auto-indexes all supported file types** — A `post-commit` hook in
    `~/brain/.git/hooks/` runs `index_brain.py --update` automatically after each commit
    that touches `.md`, `.pdf`, `.txt`, `.srt`, or `.vtt` files. Manual `--update` after
    writing is still recommended for verification, but the hook provides a safety net.

12. **PDF page numbers are approximate** — Page detection uses fingerprint matching
    (matching chunk content against per-page text). For multi-page sections or cross-page
    content, the assigned page may be off by ±1. Verify by checking chunk content.

13. **Large PDFs are slow** — PyMuPDF4LLM extraction + page fingerprint matching adds
    overhead. Expect ~3-5 seconds per PDF page on the first index. Subsequent `--update`
    runs are fast (hash check: instant).

14. **--profile is NOT required for shared brain** — Omitting `--profile` defaults to
    `shared`, which searches only the brain vault markdown. Use `--profile all` to include
    all agent sources, or `--profile maya` for a specific agent's library.

## Related Skills

- **`brain`** — Load this for vault operations: reading specific files, writing new
  content, validation, git sync, traversal protocol. `brain-search` is for
  **discovery**; `brain` is for **operations**.
- **`obsidian`** — OKF format rules, frontmatter templates, wikilink conventions.
- **`honcho-management`** — Managing the Honcho server, PostgreSQL, Ollama models.

## References

- `references/infrastructure.md` — DB schema, chunking strategy, embedding pipeline, performance, SQL parameter pinning patterns.
- `references/layer3-pdf-roadmap.md` — **IMPLEMENTED** Layer 3 architecture: add-source workflow, per-agent search, citation format, profile derivation, known pitfalls, and original research.
