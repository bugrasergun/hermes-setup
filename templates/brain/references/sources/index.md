# Sources — Reference Library (Layer 3)

Per-agent and shared reference sources for the knowledge architecture.
Files here are automatically indexed by `index_brain.py` and made searchable
via semantic search (`brain-search` skill).

## Structure

Each agent has a dedicated folder. Files placed in an agent's folder are
tagged with that agent's profile in the database, so searches with
`--profile <agent>` only return that agent's sources plus shared.

| Folder | Profile Tag | Access |
|--------|-------------|--------|
| [shared/](shared/index.md) | `shared` | All agents |
| [ayda/](ayda/index.md) | `ayda` | Ayda (orchestrator) only |
| [alex/](alex/index.md) | `alex` | Alex (PM) only |
| [sage/](sage/index.md) | `sage` | Sage (BS) only |
| [maya/](maya/index.md) | `maya` | Maya (PGM) only |

## Supported File Types

| Type | Extensions | Extraction |
|------|-----------|------------|
| Markdown | `.md` | Direct read |
| PDF | `.pdf` | PyMuPDF4LLM → markdown |
| Text | `.txt` | Direct read |
| Transcript | `.srt`, `.vtt` | Parse → plain text |

## How It Works

1. Place a file in the appropriate agent folder (e.g. `maya/pranayama-guide.pdf`)
2. `git add` + `git commit` — the post-commit hook triggers auto re-index
3. The file is extracted, chunked, embedded, and stored in `brain_documents`
4. Agent searches with `--profile maya` can now retrieve chunks from this file
5. Citations include file name, page number (for PDFs), and similarity score

## Manual Re-index

```bash
# Update only changed files
/Users/USERNAME/honcho/.venv/bin/python /Users/USERNAME/brain/scripts/index_brain.py --update

# Full rebuild
/Users/USERNAME/honcho/.venv/bin/python /Users/USERNAME/brain/scripts/index_brain.py --rebuild
```
