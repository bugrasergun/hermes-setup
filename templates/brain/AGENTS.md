---
type: Guide
title: Brain — Knowledge Bundle Context
description: Guide to the ~/brain/ shared knowledge bundle for all Hermes agents. Auto-discovered by Hermes at startup.
tags: [guide, okf, brain, config, multi-agent]
timestamp: '2026-01-01T00:00:00+00:00'
---

# Brain — Knowledge Bundle Context

This `~/brain/` directory is the **shared knowledge base** (OKF v0.1 format) for all Hermes AI agents.
It is the single source of truth — every agent reads from and writes to it.

## Quick Start for Any Agent

1. Read `agents/rules.md` first — generic vault rules shared by all agents
2. Read `index.md` — top-level directory map to discover available domains
3. Navigate to your domain directory based on your role

## Agent Discovery

See [agents/index.md](agents/index.md) for the list of active agents, their profiles, and roles.
Each agent's identity is defined in its own Hermes profile `SOUL.md`, not in this vault.

## Vault Rules

- **No secrets in vault** — API keys, tokens, and credentials go to `~/.hermes/.env` or `~/.hermes/auth.json`
- **Durable data goes to brain** — PRDs, roadmaps, decisions, and other persistent outputs go under `projects/`
- **OKF format** — concept files need YAML frontmatter; `index.md` and `log.md` are reserved (no frontmatter)
- **Relative paths only** — never use absolute `/` paths in links
- **Validate** — run `scripts/validate.py` after bulk changes
- **Always git push** — `git add -A && git commit -m "..." && git push origin main`

## Directory Map

| Path | Purpose | Write Owner |
|---|---|---|
| `self/` | Owner's personal profile: identity, goals, values, preferences | Any agent |
| `agents/` | Agent catalog, platform configs, **vault rules** (rules.md) | Primary agent |
| `projects/` | Active and archived projects | Any agent |
| `tech/` | Dev environment, languages, frameworks | Any agent |
| `learning/` | Books, courses, research | Any agent |
| `health/` | Fitness program, nutrition plan, health metrics | Any agent |
| `finance/` | Budget, subscriptions, investments | Any agent |
| `growth/` | Personal growth workspace | Any agent |
| `network/` | People and organizations | Any agent |
| `playbooks/` | SOPs, runbooks, operational procedures | Any agent |
| `reports/` | Daily / weekly / monthly session reports | Any agent |
| `references/` | Glossary, standards, service notes | Any agent |
| `timeline.json` | Agent cross-session context — managed by Librarian Daemon | **Librarian only** |

## Notes

- `timeline.json` is strictly managed by the external Librarian Daemon. Agents only **READ** this file at the start of sessions; they do **NOT** write to it directly.
- Session reports: write daily summaries to `reports/daily/YYYY-MM-DD.md`
- Durable facts always go to brain/ — never rely on in-context memory alone
