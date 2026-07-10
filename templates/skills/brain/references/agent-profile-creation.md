# Agent Profile Creation Workflow

Steps to create a new Assistio agent profile. Used when building Product Manager, Business Strategist, Personal Growth Mentor, or future agents.

## Prerequisites

- Hermes installed and running
- Honcho server running (for memory)
- Default profile configured with credentials
- OpenRouter API key in ~/.hermes/.env

## Step-by-Step

### 1. Create the Hermes Profile

```bash
hermes profile create <profile-name>
# Example: hermes profile create product-manager
```

This creates: `~/.hermes/profiles/<profile-name>/` with default SOUL.md, config.yaml, .env, and bundled skills.

Also creates a wrapper script at `~/.local/bin/<profile-name>` for direct access.

### 2. Sync Honcho aiPeer

```bash
hermes honcho sync
```

This adds a new host entry to `~/.hermes/honcho.json` with:
- `peerName: "USERNAME"` (shared user memory — ALL agents)
- `aiPeer: "<profile-name>"` (isolated AI memory — only this agent)

### 3. Create SOUL.md from Identity Source

**SOURCE RULE — CRITICAL:**
- **SOUL.md source** → identity repos like `msitarzewski/agency-agents` (who the agent is)
- **Skills source** → capability repos like `shawnpang/startup-founder-skills` (what the agent can do)
- **Never copy skill content into SOUL.md** — SOUL.md only has identity

Extract identity from the identity repo, adapt to:
- Agent's unique name (e.g. Alex, Sage, Maya — never reuse "Ayda")
- Role and mission
- Core beliefs and critical rules
- Team section (include all 4 agents with their roles)
- Owner: reference Buğra's `self/profile.md` in brain
- Which brain directories to read/write
- Honcho aiPeer identity
- Assistio-specific rules (kalıcı veri brain'e yazma kuralı, orchestration protocol)
- Skills (reference only, no content)
- Language: English for specialized agents (BS, PGM), Turkish+English for Ayda

Write to: `~/.hermes/profiles/<profile-name>/SOUL.md`

### 4. Copy API Credentials

```bash
cp ~/.hermes/.env ~/.hermes/profiles/<profile-name>/.env
```

### 5. Set Model

```bash
hermes --profile <profile-name> config set model.default deepseek/deepseek-v4-flash
hermes --profile <profile-name> config set model.provider openrouter
```

### 6. Install Domain Skills

Each agent's skills live ONLY in their own profile's skills directory — **not in the global `~/.hermes/skills/` directory** and **not as symlinks to global skills**. This keeps each agent's capabilities isolated.

```bash
# 6a. Create domain skill directories under the profile
cd ~/.hermes/profiles/<profile-name>/skills
mkdir -p assistio/<skill-name>
# Example: mkdir -p assistio/assistio-competitive-analysis

# 6b. Write SKILL.md directly into the profile directory
# (Use write_file or skill_manage with profile path)

# 6c. Link brain (shared vault operations — this IS appropriate as a symlink)
cd ~/.hermes/profiles/<profile-name>/skills
ln -s ../../../skills/brain brain
```

**CRITICAL — Profile skills directory vs Global skills directory:**

| Location | Purpose | Example |
|----------|---------|---------|
| `~/.hermes/skills/<category>/` | Global — loaded by ALL profiles | `brain`, `honcho-management` |
| `~/.hermes/profiles/<name>/skills/` | Profile-specific — loaded only by that agent | `assistio-competitive-analysis` (Sage only) |

**Rule:** Domain-specific skills (like `assistio-competitive-analysis`, `assistio-prd-writing`) belong ONLY in the profile that uses them. The global skills directory is for shared infrastructure skills (`brain`, `github`, etc.).

**Common pitfall:** When you `skill_manage(action='create')`, the skill is created in `~/.hermes/skills/` (global). Agent-specific skills must be CREATED DIRECTLY in the profile's skills directory, NOT via `skill_manage`. Use `mkdir -p` + `write_file` instead.

### 7. Set Up Telegram Bot

Each profile needs its own bot token from @BotFather. Multiple profiles CAN run simultaneously with separate launchd plists.

**Prerequisites:** Bot token, your Telegram user ID.

```bash
# Add token to profile's .env
echo 'TELEGRAM_BOT_TOKEN=<token>' >> ~/.hermes/profiles/<profile-name>/.env
echo 'TELEGRAM_ALLOWED_USERS=<your-telegram-id>' >> ~/.hermes/profiles/<profile-name>/.env
echo 'TELEGRAM_HOME_CHANNEL=<your-telegram-id>' >> ~/.hermes/profiles/<profile-name>/.env

# Install gateway as launchd service (creates separate plist)
hermes --profile <profile-name> gateway install

# Verify
hermes --profile <profile-name> gateway status
tail -30 ~/.hermes/profiles/<profile-name>/logs/gateway.log | grep -i telegram
# Expected: "✓ telegram connected"
```

**Restart after config/model changes:**
```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/ai.hermes.gateway-<profile-name>.plist
sleep 2
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/ai.hermes.gateway-<profile-name>.plist
```

**Pitfall:** Do NOT use `hermes --profile <name> gateway setup telegram` — that command does not accept platform name as an argument.

**OAuth for secondary profiles:**
```bash
hermes --profile <name> auth add <provider>  # e.g. auth add nous
```
Each profile stores its own OAuth credentials independently.

### 8. Test the Profile

```bash
hermes --profile <profile-name> chat -q "Hi! What's your name and role?" -Q
# Expected: agent identifies itself with its unique name and role
```

## Naming Convention

| Agent Type | Profile Name | Display Name | Emoji |
|-----------|-------------|--------------|-------|
| Product Manager | `product-manager` | Alex | 🧭 |
| Business Strategist | `business-strategist` | Sage | ♟️ |
| Personal Growth Mentor | `personal-growth-mentor` | Maya | 🌱 |
| (future agents) | kebab-case | unique name | per role |

**Rule:** Every agent must have a UNIQUE display name. Never reuse "Ayda" — that's the orchestrator.

## Verification Checklist

- [ ] `hermes profile list` shows the profile
- [ ] `hermes honcho status` shows the aiPeer
- [ ] Profile responds to `chat -q` queries with correct name
- [ ] Profile knows its team members
- [ ] Profile can read/write to brain/ (brain skill symlinked)
- [ ] Profile skills are accessible (category symlinked)
- [ ] .env has API key (copied from default)