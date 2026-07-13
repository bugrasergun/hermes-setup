---
type: Guide
title: Vault Rules — Critical Reading
description: Generic vault rules that all Assistio agents must read before taking action in the ~/brain/ knowledge bundle.
tags:
- vault-rules
- critical
- instructions
timestamp: '2026-07-02T00:00:00+03:00'
---

> **All agents: Read this file at the start of every session before taking significant action in ~/brain/.**

## Owner

Buğra Sergun. See [profile](profile.md) for full context.

## Shared Knowledge Base

This `~/brain/` bundle is the single source of truth, shared by all Assistio agents.
Each agent's identity comes from its own `SOUL.md` (per Hermes profile).

## Brain Reading & Discovery Protocol

When answering questions or searching for information about projects, finance, health, tech, network, playbooks, or references: **do NOT rely on memory alone.**

1. **Semantic Search First**: Always run a semantic search using the `brain-search` skill (or CLI: `/Users/USERNAME/honcho/.venv/bin/python /Users/USERNAME/brain/scripts/index_brain.py --search "query"`) to find relevant files and content chunks.
2. **Fallback Manual Traversal**: Only if semantic search returns no relevant results (or database is offline), fall back to reading `~/brain/<domain>/index.md` to discover available concepts.
3. **Read those files**: Read the discovered concept files using file tools before answering.
4. **Cross-check**: Cross-check linked concepts if needed (depth 1 only).
5. **Always source from files**: Brain is the ground truth.

This applies to: `projects/`, `tech/`, `finance/`, `health/`, `network/`, `playbooks/`, `learning/`, `references/`, `reports/`, `self/`

## Important Rules for All Agents

- **Security first:** Credentials, tokens, and sensitive data are sacred. Never commit to git.
- **Verify, don't assume:** Check before claiming something works. Run the command, read the file, confirm.
- **Root cause, not workaround:** Find the source of the problem. Don't suggest temporary/manual fixes.
- **Confirm before destructive actions:** Deleting files, modifying code/config, sending external messages — always get explicit approval.
- **Stay organized:** Durable facts go to `~/brain/`, procedures go to skills.
- **Kalıcı veriler brain'e, geçici veriler MEMORY.md'ye:** PRD'ler, roadmap'ler, MVP kararları gibi kalıcı çıktılar brain proje klasörlerine yazılır. MEMORY.md sadece session geçici notları içindir.

## Credentials & Sensitive Data

- Credentials are stored in `~/.hermes/auth.json` — never commit to git
- API keys: see `~/.hermes/.env`
- `~/brain/` is git-tracked — do not put secrets here

## Known Issues / Quirks

- OpenViking extraction pipeline broken with VLM models (gemma4, qwen3) — use bypass method if needed
- hermes update breaks gateway patches — must re-apply after update