#!/usr/bin/env bash
# =============================================================================
# setup_librarian.sh
# Librarian Daemon — Interactive Setup Script
#
# Sets up the ~/librarian/ Python daemon that watches Hermes conversation
# databases and extracts memory events into ~/brain/timeline.json.
#
# Safe to re-run: will not overwrite existing files.
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
LIB_ROOT="$HOME/librarian"
PYTHON_BIN=""

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║        Librarian Daemon — Setup Script           ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# -----------------------------------------------------------------------------
# 1. Detect Python 3.14+
# -----------------------------------------------------------------------------
echo "► Detecting Python installation..."

for candidate in \
    "$HOME/.hermes/node/bin/python3" \
    "$(brew --prefix python@3.14 2>/dev/null)/bin/python3.14" \
    "/opt/homebrew/opt/python@3.14/bin/python3.14" \
    "/usr/local/opt/python@3.14/bin/python3.14" \
    "python3.14" \
    "python3"; do

    if command -v "$candidate" &>/dev/null; then
        VER=$("$candidate" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
        MAJOR=$(echo "$VER" | cut -d. -f1)
        MINOR=$(echo "$VER" | cut -d. -f2)
        if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 12 ]; then
            PYTHON_BIN="$candidate"
            echo "  ✓ Found Python $VER at: $PYTHON_BIN"
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "  ✗ Python 3.12+ not found. Please install it first:"
    echo "    brew install python@3.14"
    exit 1
fi

# -----------------------------------------------------------------------------
# 2. Collect LLM configuration interactively
# -----------------------------------------------------------------------------
echo ""
echo "► LLM Provider Configuration"
echo "  The Librarian needs an LLM to analyze conversations."
echo ""
echo "  Select your LLM provider:"
echo "  1) Ollama (local, recommended)"
echo "  2) OpenRouter (cloud, requires API key)"
echo "  3) Other OpenAI-compatible API"
echo ""
read -r -p "  Enter choice [1]: " LLM_CHOICE
LLM_CHOICE="${LLM_CHOICE:-1}"

OLLAMA_URL="http://localhost:11434/api/chat"
OLLAMA_MODEL="qwen2.5:4b"
OLLAMA_TIMEOUT=600

case "$LLM_CHOICE" in
    1)
        echo ""
        read -r -p "  Ollama model name [qwen2.5:4b]: " MODEL_INPUT
        OLLAMA_MODEL="${MODEL_INPUT:-qwen2.5:4b}"
        echo "  ✓ Using Ollama with model: $OLLAMA_MODEL"
        ;;
    2)
        echo ""
        OLLAMA_URL="https://openrouter.ai/api/v1/chat/completions"
        read -r -p "  OpenRouter model name [qwen/qwen-2.5-7b-instruct]: " MODEL_INPUT
        OLLAMA_MODEL="${MODEL_INPUT:-qwen/qwen-2.5-7b-instruct}"
        read -r -s -p "  OpenRouter API Key: " OR_API_KEY
        echo ""
        echo "  ✓ Using OpenRouter with model: $OLLAMA_MODEL"
        ;;
    3)
        echo ""
        read -r -p "  API Base URL: " OLLAMA_URL
        read -r -p "  Model name: " OLLAMA_MODEL
        read -r -s -p "  API Key (leave blank if not needed): " OR_API_KEY
        echo ""
        echo "  ✓ Using custom API: $OLLAMA_URL"
        ;;
    *)
        echo "  Invalid choice. Using Ollama defaults."
        ;;
esac

# -----------------------------------------------------------------------------
# 3. Collect Hermes agent profile configuration
# -----------------------------------------------------------------------------
echo ""
echo "► Hermes Agent Profile Configuration"
echo "  The Librarian monitors Hermes agent databases."
echo "  At minimum, configure your primary agent (usually 'Ayda' or 'Hermes')."
echo ""

# Primary profile
read -r -p "  Primary agent name [Ayda]: " PRIMARY_AGENT
PRIMARY_AGENT="${PRIMARY_AGENT:-Ayda}"
PRIMARY_DB="$HOME/.hermes/state.db"
echo "  ✓ Primary agent: $PRIMARY_AGENT (db: $PRIMARY_DB)"

# Additional profiles
declare -a EXTRA_PROFILES=()
echo ""
echo "  Do you have additional Hermes profiles? (e.g., personal-growth-mentor, business-strategist)"
read -r -p "  Add profiles? [y/N]: " ADD_PROFILES

if [[ "${ADD_PROFILES,,}" == "y" ]]; then
    echo "  Enter profiles one by one. Format: profile-directory-name,AgentName"
    echo "  Example: personal-growth-mentor,Maya"
    echo "  Press Enter with empty input when done."
    while true; do
        read -r -p "  Profile [done]: " PROFILE_INPUT
        [ -z "$PROFILE_INPUT" ] && break
        EXTRA_PROFILES+=("$PROFILE_INPUT")
    done
fi

# -----------------------------------------------------------------------------
# 4. Create directory structure
# -----------------------------------------------------------------------------
echo ""
echo "► Creating Librarian directory structure..."

mkdir -p "$LIB_ROOT/logs"
echo "  ✓ Created: $LIB_ROOT"

# -----------------------------------------------------------------------------
# 5. Copy source files from templates
# -----------------------------------------------------------------------------
echo ""
echo "► Copying Librarian source files..."

TEMPLATE_DIR="$REPO_ROOT/templates/librarian"

copy_if_missing() {
    local src="$1"
    local dst="$2"
    if [ ! -f "$dst" ]; then
        cp "$src" "$dst"
        echo "  ✓ Copied: $(basename "$dst")"
    else
        echo "  — Already exists: $(basename "$dst")"
    fi
}

for pyfile in main.py watcher.py processor.py cron.py task_queue.py timeline.py schemas.py logger.py; do
    copy_if_missing "$TEMPLATE_DIR/$pyfile" "$LIB_ROOT/$pyfile"
done
copy_if_missing "$TEMPLATE_DIR/schema.sql" "$LIB_ROOT/schema.sql"

# -----------------------------------------------------------------------------
# 6. Generate config.py from collected inputs
# -----------------------------------------------------------------------------
echo ""
echo "► Generating config.py..."

CONFIG_FILE="$LIB_ROOT/config.py"

if [ ! -f "$CONFIG_FILE" ]; then
    # Build PROFILES dict
    PROFILES_BLOCK="PROFILES = {\n"
    PROFILES_BLOCK+="    \"default\": {\n"
    PROFILES_BLOCK+="        \"agent_name\": \"$PRIMARY_AGENT\",\n"
    PROFILES_BLOCK+="        \"db_path\": f\"{HOME}/.hermes/state.db\",\n"
    PROFILES_BLOCK+="    },"

    for entry in "${EXTRA_PROFILES[@]:-}"; do
        if [ -n "$entry" ]; then
            IFS=',' read -r PROF_DIR PROF_NAME <<< "$entry"
            PROFILES_BLOCK+="\n    \"$PROF_DIR\": {\n"
            PROFILES_BLOCK+="        \"agent_name\": \"$PROF_NAME\",\n"
            PROFILES_BLOCK+="        \"db_path\": f\"{HOME}/.hermes/profiles/$PROF_DIR/state.db\",\n"
            PROFILES_BLOCK+="    },"
        fi
    done
    PROFILES_BLOCK+="\n}"

    cat > "$CONFIG_FILE" <<PYEOF
import os

HOME = os.path.expanduser("~")

$(echo -e "$PROFILES_BLOCK")

TIMELINE_PATH = f"{HOME}/brain/timeline.json"
LIBRARIAN_DB  = f"{HOME}/librarian/librarian.db"
OLLAMA_URL    = "$OLLAMA_URL"
OLLAMA_MODEL  = "$OLLAMA_MODEL"
OLLAMA_TIMEOUT= $OLLAMA_TIMEOUT
POLL_INTERVAL = 10
MSG_THRESHOLD = 20
UNGRACEFUL_THRESHOLD = 30
MAX_RETRIES   = 3
CRON_HOUR     = 6
REPORTS_DIR   = f"{HOME}/brain/reports/daily"
PYEOF
    echo "  ✓ Generated config.py"
else
    echo "  — config.py already exists (not overwriting)"
fi

# -----------------------------------------------------------------------------
# 7. Set up Python virtual environment
# -----------------------------------------------------------------------------
echo ""
echo "► Setting up Python virtual environment..."

VENV_DIR="$LIB_ROOT/.venv"
if [ ! -d "$VENV_DIR" ]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
    echo "  ✓ Created virtual environment at $VENV_DIR"
else
    echo "  — Virtual environment already exists"
fi

"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install -r "$TEMPLATE_DIR/requirements.txt" -q
echo "  ✓ Dependencies installed"

# -----------------------------------------------------------------------------
# 8. Initialize the SQLite database
# -----------------------------------------------------------------------------
echo ""
echo "► Initializing Librarian database..."

DB_FILE="$LIB_ROOT/librarian.db"
if [ ! -f "$DB_FILE" ]; then
    "$VENV_DIR/bin/python" -c "
import sqlite3, pathlib
db = sqlite3.connect('$DB_FILE')
db.executescript(pathlib.Path('$LIB_ROOT/schema.sql').read_text())
db.commit()
db.close()
print('  ✓ Database initialized')
"
else
    echo "  — librarian.db already exists"
fi

# -----------------------------------------------------------------------------
# 9. Create and load launchd plist
# -----------------------------------------------------------------------------
echo ""
echo "► Setting up macOS launch daemon (launchd)..."

USERNAME=$(whoami)
PLIST_LABEL="com.${USERNAME}.librarian"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_LABEL}.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"

mkdir -p "$LAUNCH_AGENTS_DIR"

if [ ! -f "$PLIST_PATH" ]; then
    cat > "$PLIST_PATH" <<PLISTEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${VENV_DIR}/bin/python</string>
        <string>-u</string>
        <string>${LIB_ROOT}/main.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${LIB_ROOT}/logs/system.log</string>
    <key>StandardErrorPath</key>
    <string>${LIB_ROOT}/logs/system.log</string>
</dict>
</plist>
PLISTEOF
    echo "  ✓ Created $PLIST_PATH"
else
    echo "  — Plist already exists at $PLIST_PATH"
fi

# Load the daemon
if launchctl list | grep -q "$PLIST_LABEL" 2>/dev/null; then
    echo "  — Daemon already loaded. Reloading..."
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
fi

launchctl load "$PLIST_PATH"
echo "  ✓ Daemon loaded and running"

# -----------------------------------------------------------------------------
# Done
# -----------------------------------------------------------------------------
echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  ✓ Librarian daemon setup complete!              ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "  Installation: ~/librarian/"
echo "  Config:       ~/librarian/config.py"
echo "  Logs:         ~/librarian/logs/system.log"
echo ""
echo "  To check status:  launchctl list | grep librarian"
echo "  To view logs:     tail -f ~/librarian/logs/system.log"
echo ""
