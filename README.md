# Hermes Setup Repository

> **Full setup guide for the Hermes AI Agent architecture.**  
> This repository enables zero-configuration reconstruction of the complete multi-agent system on a new machine — or can be handed to an AI agent to perform the setup autonomously.

---

## 📋 Prerequisites

Before running any scripts, ensure the following are installed on the new machine:

### 1. Core Tools

| Tool | Install Command | Notes |
|---|---|---|
| **Homebrew** | `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"` | macOS package manager |
| **Git** | `brew install git` | Version control |
| **Python 3.14+** | `brew install python@3.14` | Required by Librarian daemon |
| **Ollama** | `brew install ollama` | Local LLM server |
| **Obsidian** | [Download from obsidian.md](https://obsidian.md) | Brain vault viewer |

### 2. Hermes

Hermes must be installed **first**, before running any scripts in this repo.

```bash
# Install Hermes (follow official installation guide)
curl -fsSL https://hermes.ai/install | bash
```

After Hermes is installed and you've logged in, come back to this repo.

### 3. Ollama Models

The Librarian daemon requires an LLM to analyze conversations. Install at least one:

```bash
# Recommended default (fast, low RAM, good quality)
ollama pull qwen2.5:4b

# Or for Apple Silicon Mac (MLX-optimized, even faster)
ollama pull qwen2.5:4b-mlx
```

---

## 🚀 Setup Order

Run these steps **in order**. Each script is idempotent (safe to re-run).

### Step 1: Clone This Repository

```bash
git clone https://github.com/bugrasergun/hermes-setup.git ~/hermes-setup
cd ~/hermes-setup
chmod +x scripts/*.sh
```

### Step 2: Set Up the Brain Vault

Creates the `~/brain/` OKF knowledge vault skeleton with all required directories, base files, git hooks, and Obsidian configuration.

```bash
./scripts/setup_brain_skeleton.sh
```

**What it does:**
- Creates `~/brain/` directory with the full OKF v0.1 folder hierarchy
- Copies custom brain scripts (`validate.py`, `index_brain.py`, etc.) to `~/brain/scripts/`
- Installs the git `post-commit` hook for automatic semantic re-indexing
- Creates an empty `timeline.json` using the v1 schema
- Creates starter `AGENTS.md` and `index.md`
- Configures `BRAIN_PATH` environment variable in `~/.zshrc`
- Creates starter Obsidian `.obsidian/appearance.json`

### Step 3: Set Up the Librarian Daemon

The Librarian is a background Python daemon that watches Hermes conversation databases and extracts meaningful events into the Brain's `timeline.json`.

```bash
./scripts/setup_librarian.sh
```

**What it does:**
- Creates `~/librarian/` with all Python source files
- Prompts you to configure your LLM provider (Ollama, OpenRouter, etc.)
- Prompts you to configure your Hermes agent profiles
- Creates a Python virtual environment and installs dependencies
- Initializes the SQLite database (`librarian.db`) using `schema.sql`
- Creates and loads a `launchd` plist so the daemon starts automatically at login

### Step 4: Set Up the Honcho Memory Plugin

Honcho provides long-term semantic memory for Hermes agents via a local vector store.

```bash
./scripts/setup_honcho.sh
```

**What it does:**
- Checks if Hermes is installed
- Creates a clean `honcho.json` configuration in `~/.hermes/`
- Prompts you to configure workspace name, peer name, and agent profiles
- Optionally installs and starts the Honcho server
### Step 5: Install Custom Hermes Skills

Copies the custom `brain` and `brain-search` skills into your `~/.hermes/skills/` directory and sets up symlinks for IDE auto-discovery.

```bash
./scripts/setup_skills.sh
```

**What it does:**
- Copies `brain` and `brain-search` custom skill directories to `~/.hermes/skills/`
- Dynamically resolves and sanitizes user paths
- Links them under `~/.gemini/config/skills/` for IDE auto-discovery

### Step 6: Configure Obsidian

```bash
./scripts/setup_obsidian.sh
```

**What it does:**
- Verifies the `~/brain/` directory exists
- Opens Obsidian (or provides instructions to open the vault manually)
- Provides guidance on recommended Obsidian plugins

### Step 7: (Optional) Bootstrap Hermes Agent Profiles

If you want to add the Session Initialization Protocol to your Hermes agent profiles (so they auto-read the brain at session start):

```bash
python3 scripts/bootstrap_profiles.py
```


---

## 🧠 Architecture Overview

```
~/brain/                        ← OKF Knowledge Vault (Obsidian + Git)
├── agents/                     ← Agent catalog & vault rules
├── projects/                   ← Active and archived projects
├── tech/                       ← Technical knowledge
├── learning/                   ← Books, courses, research
├── health/                     ← Fitness, nutrition (Maya agent)
├── finance/                    ← Budget, subscriptions (Maya agent)
├── growth/                     ← Maya PGM workspace
├── network/                    ← People and organizations
├── playbooks/                  ← SOPs & runbooks
├── reports/                    ← Daily/weekly/monthly reports
│   └── daily/                  ← Auto-generated by Librarian
├── references/                 ← Glossary, standards, sources
├── scripts/                    ← Custom tooling
│   ├── index_brain.py          ← Semantic search indexer (pgvector)
│   ├── validate.py             ← OKF conformance validator
│   └── post-commit             ← Git hook (auto re-index on commit)
├── AGENTS.md                   ← Auto-discovered by Hermes
├── index.md                    ← Vault table of contents
└── timeline.json               ← Session continuity file (managed by Librarian)

~/librarian/                    ← Librarian Daemon
├── main.py                     ← Entry point (event loop)
├── watcher.py                  ← Polls Hermes state.db files
├── processor.py                ← Sends messages to LLM, writes timeline
├── cron.py                     ← Daily report generation (runs at 06:00)
├── task_queue.py               ← FIFO SQLite queue
├── timeline.py                 ← Read/write ~/brain/timeline.json
├── schemas.py                  ← JSON schema for LLM structured output
├── config.py                   ← ⚙️ Edit this: profiles, LLM, paths
├── schema.sql                  ← Database schema
└── .venv/                      ← Python virtual environment

~/.hermes/
├── honcho.json                 ← Honcho memory plugin config
├── SOUL.md                     ← Primary agent identity (Ayda)
├── profiles/                   ← Additional agent profiles
│   ├── personal-growth-mentor/ ← Maya
│   ├── business-strategist/    ← Sage
│   └── product-manager/        ← Alex
└── skills/                     ← Hermes skill library
```

---

## 📦 Repository Structure

```
hermes-setup/
├── README.md                          ← This file
├── AGENTS.md                          ← AI-agent-readable setup instructions
├── scripts/
│   ├── setup_brain_skeleton.sh        ← Step 2
│   ├── setup_librarian.sh             ← Step 3
│   ├── setup_honcho.sh                ← Step 4
│   ├── setup_obsidian.sh              ← Step 5
│   └── bootstrap_profiles.py         ← Step 6 (optional)
└── templates/
    ├── librarian/                     ← Librarian source code
    │   ├── *.py                       ← All Python modules
    │   ├── schema.sql                 ← Database schema
    │   ├── requirements.txt           ← Python dependencies
    │   └── com.USERNAME.librarian.plist ← launchd template
    ├── brain_scripts/                 ← Custom brain scripts
    │   ├── index_brain.py
    │   ├── post-commit
    │   ├── setup.sh
    │   ├── validate.py
    │   └── validate.sh
    ├── brain/                         ← Brain vault skeleton files
    │   ├── AGENTS.md
    │   ├── index.md
    │   ├── timeline.json
    │   ├── .gitignore
    │   └── .stignore
    └── config/
        └── honcho.example.json        ← Honcho config template
```

---

## ⚙️ Manual Configuration

After running all setup scripts, you may want to customize:

### Librarian (`~/librarian/config.py`)

```python
# Your Hermes agent profiles
PROFILES = {
    "default": {
        "agent_name": "YourAgentName",
        "db_path": f"{HOME}/.hermes/state.db",
    },
}

# LLM settings
OLLAMA_URL   = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen2.5:4b"

# Behavior tuning
MSG_THRESHOLD        = 20   # Process queue when session hits N messages
UNGRACEFUL_THRESHOLD = 30   # Minutes of inactivity before treating as closed
CRON_HOUR            = 6    # Hour to generate daily report (24h format)
```

### Honcho (`~/.hermes/honcho.json`)

See `templates/config/honcho.example.json` for the full structure. Key fields:
- `workspace`: Your Honcho workspace name
- `hosts.hermes.peerName`: Your username (used to identify the human peer)
- `hosts.hermes.aiPeer`: Your primary agent name

---

## 🔄 Keeping the Librarian Up-to-Date

The Librarian daemon is managed by macOS `launchd`. Common commands:

```bash
# Check daemon status
launchctl list | grep librarian

# Stop the daemon
launchctl unload ~/Library/LaunchAgents/com.$(whoami).librarian.plist

# Start the daemon
launchctl load ~/Library/LaunchAgents/com.$(whoami).librarian.plist

# View logs
tail -f ~/librarian/logs/system.log
```

---

## 🔍 Troubleshooting

| Issue | Solution |
|---|---|
| Librarian daemon not starting | Check `~/librarian/logs/system.log`. Verify Ollama is running (`ollama serve`). |
| `timeline.json` not being updated | Ensure Librarian is running and Hermes sessions are being logged. |
| Brain semantic search not working | Ensure PostgreSQL + pgvector is running. Run `index_brain.py --rebuild`. |
| Obsidian not finding vault | Open Obsidian → "Open folder as vault" → select `~/brain/`. |
| Honcho plugin errors | Check `~/.hermes/honcho.json` matches the template. Restart Hermes. |
