# AGENTS.md — Hermes Setup Repository

> **FOR AI AGENTS**: This file contains step-by-step, deterministic instructions for setting up the full Hermes AI Agent architecture on a new macOS machine. Read this entire document before taking any action. Execute each step in order.

---

## Your Mission

You are setting up a multi-agent AI system on a new Mac. The system consists of:
1. **Hermes** — The AI agent platform (must already be installed)
2. **Brain Vault** — A shared knowledge base at `~/brain/` in OKF format
3. **Librarian Daemon** — A Python background process that monitors Hermes sessions and writes memory events to the Brain
4. **Honcho Plugin** — A long-term memory plugin for Hermes
5. **Obsidian** — A markdown editor configured to view the Brain vault

## Before You Start

**STOP** and verify:
- [ ] Hermes is installed and the user has logged in (`~/.hermes/` directory exists)
- [ ] macOS is running (this setup is Mac-only)
- [ ] The user has Homebrew installed, or you can install it

If Hermes is NOT installed, instruct the user to install Hermes first, then come back.

---

## Step 1: Install System Prerequisites

Check each tool and install if missing.

### 1a. Homebrew
```bash
which brew || /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 1b. Python 3.14+
```bash
brew install python@3.14
```
Verify: `python3 --version` should show 3.14+.

### 1c. Git
```bash
brew install git
```

### 1d. Ollama (Local LLM Server)
```bash
brew install ollama
```
After install, pull the required model:
```bash
ollama pull qwen2.5:4b
```
Start Ollama in background:
```bash
ollama serve &
```

### 1e. Obsidian
Obsidian is a GUI app. Instruct the user:
> "Please download and install Obsidian from https://obsidian.md — it's the note-taking app for your Brain vault."

---

## Step 2: Set Up the Brain Vault

**Script location**: `scripts/setup_brain_skeleton.sh`

```bash
cd ~/hermes-setup
chmod +x scripts/setup_brain_skeleton.sh
./scripts/setup_brain_skeleton.sh
```

**Verify success** by checking:
```bash
ls ~/brain/  # Should show: agents/ finance/ growth/ health/ learning/ network/ playbooks/ projects/ references/ reports/ scripts/ self/ tech/ AGENTS.md index.md timeline.json
```

**If the script fails**, check the error message. Common issues:
- Permission denied → `chmod +x scripts/setup_brain_skeleton.sh`
- `~/brain` already exists → The script is idempotent, it will not overwrite existing files. This is safe to re-run.

---

## Step 3: Set Up the Librarian Daemon

**Script location**: `scripts/setup_librarian.sh`

The script will ask you for configuration. Collect this information from the user BEFORE running:
1. **LLM Provider**: Ask: "Which LLM will Librarian use? (a) Ollama/local model [default], (b) OpenRouter, (c) Other"
2. **Model name**: If Ollama → `qwen2.5:4b`. If OpenRouter → ask for the model name.
3. **Agent profiles**: Ask the user to list their Hermes agent profiles (name + profile directory). Default is `Ayda` (the main agent, using `~/.hermes/state.db`).

```bash
chmod +x scripts/setup_librarian.sh
./scripts/setup_librarian.sh
```

**Verify success**:
```bash
# Check the daemon is loaded
launchctl list | grep librarian
# Should show a line with com.USERNAME.librarian

# Check the log
tail -20 ~/librarian/logs/system.log
```

If the log shows `Librarian Daemon started.` — success!

---

## Step 4: Set Up the Honcho Memory Plugin

**Script location**: `scripts/setup_honcho.sh`

Collect from user before running:
1. **Username/peer name**: The user's username for Honcho (e.g., `bugrasergun`)
2. **Primary agent name**: The name of the main Hermes agent (e.g., `Ayda`)
3. **Additional agent profiles**: Names of other Hermes profiles (e.g., `personal-growth-mentor`, `business-strategist`)

```bash
chmod +x scripts/setup_honcho.sh
./scripts/setup_honcho.sh
```

**Verify success**:
```bash
cat ~/.hermes/honcho.json  # Should show a valid JSON config
```

Restart Hermes after this step.
---

## Step 5: Install Custom Hermes Skills

**Script location**: `scripts/setup_skills.sh`

This script copies the custom `brain` and `brain-search` skills into your `~/.hermes/skills` directory and sets up symlinks under `~/.gemini/config/skills/` for IDE auto-discovery.

```bash
chmod +x scripts/setup_skills.sh
./scripts/setup_skills.sh
```

**Verify success**:
```bash
ls ~/.hermes/skills/  # Should show: brain/ brain-search/
```

---

## Step 6: Configure Obsidian

```bash
chmod +x scripts/setup_obsidian.sh
./scripts/setup_obsidian.sh
```

Then instruct the user to:
1. Open Obsidian
2. Click "Open folder as vault"
3. Select `~/brain/`
4. Accept any prompts

**Recommended Obsidian plugins** (install from Obsidian Settings → Community Plugins):
- `Templater` — template support
- `Dataview` — query vault data like a database
- `Calendar` — calendar view for daily notes
---

## Step 7: (Optional) Bootstrap Hermes Profiles

This step adds the Session Initialization Protocol to existing Hermes agent profiles so they auto-read the Brain vault at session start.

```bash
python3 scripts/bootstrap_profiles.py
```

---

## Step 8: Final Verification

Run this checklist to confirm everything is working:

```bash
# 1. Brain vault exists
ls ~/brain/AGENTS.md && echo "✓ Brain vault OK"

# 2. timeline.json is valid JSON
python3 -c "import json; json.load(open('$HOME/brain/timeline.json'))" && echo "✓ timeline.json OK"

# 3. Librarian daemon is running
launchctl list | grep librarian && echo "✓ Librarian daemon running"

# 4. Librarian can connect to Ollama
curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; d=json.load(sys.stdin); print('✓ Ollama OK, models:', [m['name'] for m in d.get('models',[])])"

# 5. Honcho config exists
test -f ~/.hermes/honcho.json && echo "✓ Honcho config OK"

# 6. Brain scripts are executable
test -x ~/brain/scripts/validate.sh && echo "✓ Brain scripts OK"
```

---

## Error Reference

| Error | Cause | Fix |
|---|---|---|
| `~/.hermes not found` | Hermes not installed | Install Hermes first |
| `ollama: command not found` | Ollama not installed | `brew install ollama` |
| `connection refused 11434` | Ollama not running | `ollama serve` |
| `launchctl: no such file` | Plist not created | Re-run `setup_librarian.sh` |
| `ModuleNotFoundError: requests` | venv not set up | Re-run `setup_librarian.sh` from Step 4 |
| `Permission denied` | Script not executable | `chmod +x scripts/*.sh` |

---

## Key File Locations (Reference)

| File | Purpose |
|---|---|
| `~/brain/timeline.json` | Session continuity — AI agents read at session start |
| `~/brain/AGENTS.md` | Brain vault context — auto-loaded by Hermes |
| `~/librarian/config.py` | Librarian configuration (profiles, LLM settings) |
| `~/.hermes/honcho.json` | Honcho memory plugin configuration |
| `~/.hermes/SOUL.md` | Primary agent identity file |
| `~/Library/LaunchAgents/com.USERNAME.librarian.plist` | macOS daemon configuration |
| `~/librarian/logs/system.log` | Librarian daemon logs |
