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

### 1d. LLM Mode Decision — Ask First!

> **STOP — Ask the user before installing anything.**

Ask the user:
> "Bu kurulumu yapacağınız bilgisayar yerel AI modeli çalıştıracak güçte mi? (Apple Silicon M3/M4 veya ≥16 GB RAM ile NVIDIA GPU önerilir). Yoksa NVIDIA NIM veya OpenRouter gibi bir bulut servis mi kullanmak istiyorsunuz?"

**Wait for the answer and branch:**

---

#### 🖥️ Option A: Local Mode (Ollama)

*Use this when: Apple Silicon Mac (M1/M2/M3/M4) or machine with ≥16 GB RAM. Models run locally, no API cost, no internet dependency.*

```bash
brew install ollama
```

Pull the recommended model:
```bash
# Best default for Apple Silicon (fast, low RAM, good quality)
ollama pull qwen2.5:4b

# Alternatively, for MLX-optimized speed on Apple Silicon:
ollama pull qwen2.5:4b-mlx
```

Start Ollama in background:
```bash
ollama serve &
```

Verify:
```bash
curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; d=json.load(sys.stdin); print('Ollama OK, models:', [m['name'] for m in d.get('models',[])])"
```

> **Note for Librarian (Step 3):** Set `PROVIDER=ollama` and `MODEL=qwen2.5:4b` when the setup script asks.

---

#### ☁️ Option B: Cloud Mode (NVIDIA NIM / OpenRouter — For low-power machines)

*Use this when: Machine has less than 16 GB RAM, no GPU, or you prefer cloud inference. No local GPU required.*

**Components affected — all three must be configured for cloud:**

| Component | Local Mode | Cloud Mode |
|-----------|-----------|------------|
| **Hermes** (main agent) | Ollama local LLM | NVIDIA NIM / OpenRouter |
| **Librarian** (session analyzer) | Ollama local LLM | OpenRouter / NVIDIA NIM |
| **Honcho** (memory system — `.env`) | Ollama local LLM + embeddings | OpenRouter/NVIDIA for LLM **AND** embeddings |

> **No Ollama Required:** In full Cloud Mode, you do **not** need to install Ollama at all. Honcho supports cloud embeddings via OpenAI-compatible endpoints.

**Step 1 — Skip Ollama installation entirely.**

**Step 2 — Proceed to Step 1g** to configure NVIDIA NIM as the Hermes provider.

**Step 3 — After NVIDIA is configured, set Honcho's models AND embedding config to cloud in `~/honcho/.env`** (see Step 4 Cloud Config below). *Crucial: This must be done BEFORE initializing the Honcho database.*

> **Note for Librarian (Step 3):** Set `PROVIDER=openrouter` (or `nvidia`) and provide the model name (e.g., `deepseek/deepseek-v4-flash`) when the setup script asks.

---

### 1e. Obsidian
Obsidian is a GUI app. Instruct the user:
> "Please download and install Obsidian from https://obsidian.md — it's the note-taking app for your Brain vault."

### 1f. Verify Honcho Backend (for Brain Semantic Search)
The semantic search script (`index_brain.py`) shares the local PostgreSQL database (`honcho`) and the `pgvector` extension configured by the **Honcho backend**.
Verify the Honcho server is installed and running at `http://localhost:8000` (or the configured base URL). You do not need to install or configure PostgreSQL manually if Honcho is already configured.

### 1g. Configure NVIDIA NIM as LLM Provider

This setup uses **NVIDIA NIM** as the primary inference provider. You must collect the API key from the user, store it as an environment variable, and register it with Hermes.

**Ask the user:**
> "Do you have an NVIDIA NIM API key? If not, go to https://build.nvidia.com, sign up, and generate one. It looks like `nvapi-xxxxxxxxxxxxxxxxxxxx`."

**Once the user provides the key:**

**Step 1 — Add to shell environment:**
```bash
# Append to ~/.zshrc (run exactly as shown — replace the value with the real key)
echo 'export NVIDIA_API_KEY="nvapi-xxxxxxxxxxxxxxxxxxxx"' >> ~/.zshrc
source ~/.zshrc
```

Verify:
```bash
echo $NVIDIA_API_KEY
# Must print the key, not an empty line. If empty, re-run the echo and source commands.
```

**Step 2 — Register with Hermes auth pool:**
```bash
hermes auth add nvidia --type api-key --api-key "$NVIDIA_API_KEY"
```

Verify:
```bash
hermes auth status nvidia
# Expected output: nvidia: logged in
```

**Step 3 — Set NVIDIA as the default provider in `~/.hermes/config.yaml`:**

Check if `~/.hermes/config.yaml` already has a `model:` block at the top. If yes, ensure it reads:
```yaml
model:
  default: z-ai/glm-5.2
  provider: nvidia
  base_url: https://integrate.api.nvidia.com/v1
  context_length: 1048576
```
If the block is missing or has a different provider, use `write_file` to replace it.

**Step 4 — Add fallback providers (append under `fallback_providers:` in config.yaml):**
```yaml
fallback_providers:
  - provider: nvidia
    model: deepseek-ai/deepseek-v4-pro
  - provider: nvidia
    model: deepseek-ai/deepseek-v4-flash
  - provider: openrouter
    model: deepseek/deepseek-v4-flash
```

> If the user also has an OpenRouter API key, register it the same way:
> ```bash
> hermes auth add openrouter --type api-key --api-key "$OPENROUTER_API_KEY"
> ```

**Verify NVIDIA is working end-to-end:**
```bash
hermes auth status nvidia   # Must say "logged in"
echo $NVIDIA_API_KEY        # Must not be empty
```


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
1. **LLM Provider**: Use the decision made in **Step 1d** above.
   - **Local Mode (Ollama)**: Select option (a) — `Provider=ollama`, `Model=qwen2.5:4b`
   - **Cloud Mode (NVIDIA NIM)**: Select option (b) OpenRouter or (c) Other — provide model name (e.g. `deepseek/deepseek-v4-flash`). Ensure the API key env var (`OPENROUTER_API_KEY` or `NVIDIA_API_KEY`) is set in the shell before running the script.
2. **Model name**: Pre-filled from Step 1d decision.
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

### Step 4 Cloud Config (Cloud Mode only — skip if Local Mode)

If the user chose **Option B: Cloud Mode** in Step 1d, the Honcho server's models (both reasoning and embeddings) must be pointed at a cloud provider.

**CRITICAL: You MUST configure `EMBEDDING_VECTOR_DIMENSIONS` in `~/honcho/.env` to match your cloud embedding model *before* the database initializes.** Once pgvector tables are created, dimensions cannot be changed.

**Open `~/honcho/.env`** and replace the default Ollama configurations:

Example for using **OpenRouter** (for reasoning) and **OpenAI** (for embeddings):

```bash
# 1. Update Reasoning Models (DERIVER, SUMMARY, DIALECTIC, DREAM):
sed -i '' \
  -e 's|OVERRIDES__BASE_URL=http://localhost:11434/v1|OVERRIDES__BASE_URL=https://openrouter.ai/api/v1|g' \
  -e 's|MODEL=qwen3.5:4b-mlx|MODEL=deepseek/deepseek-v4-flash|g' \
  ~/honcho/.env

# Add reasoning API key:
echo "OPENROUTER_API_KEY=$OPENROUTER_API_KEY" >> ~/honcho/.env

# 2. Update Embedding Model (EMBEDDING_MODEL_CONFIG):
# Using OpenAI text-embedding-3-small as an example (dimension: 1536)
sed -i '' \
  -e 's|EMBEDDING_MODEL_CONFIG__MODEL=nomic-embed-text|EMBEDDING_MODEL_CONFIG__MODEL=text-embedding-3-small|g' \
  -e 's|EMBEDDING_MODEL_CONFIG__OVERRIDES__BASE_URL=https://openrouter.ai/api/v1|EMBEDDING_MODEL_CONFIG__OVERRIDES__BASE_URL=https://api.openai.com/v1|g' \
  -e 's|EMBEDDING_VECTOR_DIMENSIONS=768|EMBEDDING_VECTOR_DIMENSIONS=1536|g' \
  ~/honcho/.env

# Add embedding API key:
echo "OPENAI_API_KEY=$OPENAI_API_KEY" >> ~/honcho/.env
```

After editing `~/honcho/.env`, restart the Honcho server:
```bash
# If using the Honcho launchd service:
launchctl kickstart -k gui/$(id -u)/com.$(whoami).honcho
# Or manually:
cd ~/honcho && .venv/bin/python -m honcho.main
```

Restart Hermes after this step.
---

## Step 5: Install Custom Hermes Skills

**Script location**: `scripts/setup_skills.sh`

This script copies the custom `brain`, `brain-search`, and `honcho-management` skills into your `~/.hermes/skills` directory and sets up symlinks under `~/.gemini/config/skills/` for IDE auto-discovery.

```bash
chmod +x scripts/setup_skills.sh
./scripts/setup_skills.sh
```

**Verify success**:
```bash
ls ~/.hermes/skills/  # Should show: brain/ brain-search/ honcho-management/
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

## Step 7: Bootstrap Hermes Profiles

This step adds the Session Initialization Protocol to existing Hermes agent profiles so they auto-read the Brain vault and timeline at session start. It also patches `~/.hermes/config.yaml` to set `hygiene_hard_message_limit` to `1500` to prevent premature context compression on large-context models.

```bash
python3 scripts/bootstrap_profiles.py
```

---

## Step 8: Initialize & Build Semantic Search Index

To create the semantic search tables, btree indexes, and HNSW vector index, run the initial build using Honcho's Python environment:

```bash
~/honcho/.venv/bin/python ~/brain/scripts/index_brain.py --rebuild
```

**Verify success**:
The command should complete without errors, scanning files and creating chunks. You can verify the tables:
```bash
/opt/homebrew/opt/postgresql@18/bin/psql -d honcho -c "SELECT count(*) FROM brain_documents;"
```

---

## Step 9: Final Verification


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

# 7. NVIDIA provider is authenticated
hermes auth status nvidia && echo "✓ NVIDIA auth OK"

# 8. NVIDIA_API_KEY env var is set
[ -n "$NVIDIA_API_KEY" ] && echo "✓ NVIDIA_API_KEY is set" || echo "✗ NVIDIA_API_KEY is EMPTY — add to ~/.zshrc and re-source"
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
| `nvidia: logged out` | API key not registered | Run `hermes auth add nvidia --type api-key --api-key "$NVIDIA_API_KEY"` |
| `NVIDIA_API_KEY is EMPTY` | Env var not exported | Add `export NVIDIA_API_KEY="..."` to `~/.zshrc` and `source ~/.zshrc` |
| NVIDIA 401 Unauthorized | Key expired or invalid | Generate new key at [build.nvidia.com](https://build.nvidia.com) and re-register |

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
