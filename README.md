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
| **Honcho Server** | (Local self-hosted project) | Runs memory API + deriver services (lives at `~/honcho`) |

> [!NOTE]
> The Brain semantic search script (`index_brain.py`) shares the local PostgreSQL database (`honcho`) and the `pgvector` extension configured by the **Honcho server**. The Honcho server must be cloned and set up separately at `~/honcho/` on the machine (see the `honcho-management` skill for service control and startup instructions).



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

### 4. LLM Provider — NVIDIA NIM (Recommended)

The default configuration uses **NVIDIA NIM** as the primary inference provider. NVIDIA NIM gives access to high-quality models (GLM-5.2, DeepSeek V4) at low cost via a standard OpenAI-compatible API.

#### Step A: Get an NVIDIA API Key

1. Go to [https://build.nvidia.com](https://build.nvidia.com) and sign up / log in
2. Navigate to **API Keys** in your account
3. Create a new key — it will look like `nvapi-xxxxxxxxxxxxxxxxxxxx`

#### Step B: Set the Environment Variable

Add the key to your shell config so Hermes can read it:

```bash
# Add to ~/.zshrc (or ~/.bashrc)
echo 'export NVIDIA_API_KEY="nvapi-xxxxxxxxxxxxxxxxxxxx"' >> ~/.zshrc
source ~/.zshrc
```

Verify it's set:
```bash
echo $NVIDIA_API_KEY  # Should print your key
```

#### Step C: Register the Key with Hermes

Hermes stores credentials in its auth pool, reading directly from the environment variable:

```bash
hermes auth add nvidia --type api-key --api-key "$NVIDIA_API_KEY"
```

Verify it's registered:
```bash
hermes auth status nvidia
# Should print: nvidia: logged in
```

#### Step D: Set NVIDIA as the Default Provider

Run the interactive model picker and select NVIDIA:

```bash
hermes model
```

This command opens an interactive selector. Choose:
- **Provider**: NVIDIA
- **Model**: `z-ai/glm-5.2` (recommended — large context, high quality) or `nvidia/llama-3.1-nemotron-ultra-253b-v1`

Alternatively, edit `~/.hermes/config.yaml` directly:

```yaml
model:
  default: z-ai/glm-5.2
  provider: nvidia
  base_url: https://integrate.api.nvidia.com/v1
  context_length: 1048576
```

#### Step E: Configure Fallback Providers (Optional)

Add fallback models that Hermes switches to if the primary model fails or rate-limits:

```yaml
fallback_providers:
  - provider: nvidia
    model: deepseek-ai/deepseek-v4-pro
  - provider: nvidia
    model: deepseek-ai/deepseek-v4-flash
  - provider: openrouter
    model: deepseek/deepseek-v4-flash
```

> [!NOTE]
> If you also use **OpenRouter** as a fallback, set `OPENROUTER_API_KEY` the same way and register it with `hermes auth add openrouter --type api-key --api-key "$OPENROUTER_API_KEY"`.

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

Copies the custom `brain`, `brain-search`, and `honcho-management` skills into your `~/.hermes/skills/` directory and sets up symlinks for IDE auto-discovery.

```bash
./scripts/setup_skills.sh
```

**What it does:**
- Copies `brain`, `brain-search`, and `honcho-management` custom skill directories to `~/.hermes/skills/`
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

### Step 7: Bootstrap Hermes Agent Profiles

Add the Session Initialization Protocol to your Hermes agent profiles and patch the Vault Custodian Protocol into `config.yaml`:

```bash
python3 scripts/bootstrap_profiles.py
```

**What it does:**
- Patches `~/.hermes/config.yaml` `environment_hint` with the Vault Custodian Protocol — instructs agents to read `timeline.json`, load the `brain` skill for vault operations, and load the `brain-search` skill for semantic discovery queries
- Appends the Session Initialization Protocol to all `SOUL.md` files found in `~/.hermes/` and `~/.hermes/profiles/*/`
- Safe to re-run: idempotent (uses markers to skip already-patched files)

### Step 8: Initialize & Build Semantic Search Index

To create the semantic search tables, btree indexes, and HNSW vector index, run the initial build using Honcho's Python environment:

```bash
# Run the rebuild command
~/honcho/.venv/bin/python ~/brain/scripts/index_brain.py --rebuild
```

**What it does:**
- Automatically connects to the local `honcho` database.
- Idempotently creates the `brain_documents` table and HNSW index if they don't exist.
- Performs the first-time chunking and vector embedding generation for all your markdown files.



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
│   ├── setup_skills.sh                ← Step 5
│   ├── setup_obsidian.sh              ← Step 6
│   └── bootstrap_profiles.py          ← Step 7

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
    ├── config/
    │   └── honcho.example.json        ← Honcho config template
    └── skills/                        ← Custom Hermes skills templates
        ├── brain/
        ├── brain-search/
        └── honcho-management/

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
| `nvidia: logged out` | Run `hermes auth add nvidia --type api-key --api-key "$NVIDIA_API_KEY"`. Check `$NVIDIA_API_KEY` is exported in your shell. |
| NVIDIA 401 Unauthorized | Your API key may be expired or invalid. Generate a new one at [build.nvidia.com](https://build.nvidia.com) and re-register. |
| NVIDIA rate limit / 429 | You've hit the free tier limit. Wait or upgrade your NVIDIA NIM plan. Add an OpenRouter fallback in `config.yaml`. |
