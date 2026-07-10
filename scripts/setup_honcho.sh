#!/usr/bin/env bash
# =============================================================================
# setup_honcho.sh
# Honcho Memory Plugin — Setup Script
#
# Configures the Honcho long-term memory plugin for Hermes.
# Creates ~/.hermes/honcho.json from a clean template.
#
# Safe to re-run: backs up existing config before overwriting.
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
HERMES_DIR="$HOME/.hermes"
HONCHO_CONFIG="$HERMES_DIR/honcho.json"

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║        Honcho Memory Plugin — Setup Script       ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# -----------------------------------------------------------------------------
# 1. Verify Hermes is installed
# -----------------------------------------------------------------------------
echo "► Verifying Hermes installation..."

if [ ! -d "$HERMES_DIR" ]; then
    echo "  ✗ Hermes not found at $HERMES_DIR"
    echo "    Please install Hermes first, then re-run this script."
    exit 1
fi
echo "  ✓ Hermes found at $HERMES_DIR"

# -----------------------------------------------------------------------------
# 2. Collect configuration interactively
# -----------------------------------------------------------------------------
echo ""
echo "► Honcho Configuration"
echo "  Honcho connects Hermes agents to a long-term memory backend."
echo ""

read -r -p "  Your username (peer name) [$(whoami)]: " PEER_NAME
PEER_NAME="${PEER_NAME:-$(whoami)}"

read -r -p "  Primary agent name [Ayda]: " PRIMARY_AGENT
PRIMARY_AGENT="${PRIMARY_AGENT:-Ayda}"

read -r -p "  Honcho workspace name [hermes]: " WORKSPACE
WORKSPACE="${WORKSPACE:-hermes}"

read -r -p "  Honcho server base URL [http://localhost:8000]: " BASE_URL
BASE_URL="${BASE_URL:-http://localhost:8000}"

# Additional profiles
echo ""
echo "  Do you want to add additional agent profiles to Honcho?"
echo "  (e.g., personal-growth-mentor, business-strategist, product-manager)"
read -r -p "  Add extra profiles? [y/N]: " ADD_EXTRA
ADD_EXTRA="${ADD_EXTRA:-N}"

declare -a EXTRA_HOSTS=()
if [[ "${ADD_EXTRA,,}" == "y" ]]; then
    echo "  Enter profile directory names one by one (e.g., personal-growth-mentor)"
    echo "  Press Enter with empty input when done."
    while true; do
        read -r -p "  Profile dir name [done]: " PROF_DIR
        [ -z "$PROF_DIR" ] && break
        read -r -p "  Agent name for '$PROF_DIR': " PROF_AGENT
        EXTRA_HOSTS+=("$PROF_DIR:$PROF_AGENT")
    done
fi

# -----------------------------------------------------------------------------
# 3. Write honcho.json
# -----------------------------------------------------------------------------
echo ""
echo "► Writing honcho.json..."

if [ -f "$HONCHO_CONFIG" ]; then
    BACKUP="$HONCHO_CONFIG.bak.$(date +%Y%m%d%H%M%S)"
    cp "$HONCHO_CONFIG" "$BACKUP"
    echo "  — Backed up existing config to $(basename "$BACKUP")"
fi

# Build extra hosts JSON
EXTRA_HOSTS_JSON=""
for entry in "${EXTRA_HOSTS[@]:-}"; do
    if [ -n "$entry" ]; then
        IFS=':' read -r PROF_DIR PROF_AGENT <<< "$entry"
        EXTRA_HOSTS_JSON+=",
    \"${WORKSPACE}_${PROF_DIR}\": {
      \"pinUserPeer\": true,
      \"peerName\": \"${PEER_NAME}\",
      \"aiPeer\": \"${PROF_DIR}\",
      \"workspace\": \"${WORKSPACE}\",
      \"enabled\": true
    }"
    fi
done

cat > "$HONCHO_CONFIG" <<JSONEOF
{
  "baseUrl": "${BASE_URL}",
  "enabled": true,
  "workspace": "${WORKSPACE}",
  "recallMode": "hybrid",
  "writeFrequency": "async",
  "sessionStrategy": "per-directory",
  "hosts": {
    "${WORKSPACE}": {
      "aiPeer": "${PRIMARY_AGENT}",
      "peerName": "${PEER_NAME}",
      "pinPeerName": true
    }${EXTRA_HOSTS_JSON}
  }
}
JSONEOF

echo "  ✓ Written: $HONCHO_CONFIG"

# -----------------------------------------------------------------------------
# Done
# -----------------------------------------------------------------------------
echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  ✓ Honcho plugin setup complete!                 ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "  Config: ~/.hermes/honcho.json"
echo ""
echo "  ⚠  Important: Restart Hermes for the changes to take effect."
echo ""
echo "  If Honcho server is not running yet, start it with:"
echo "    cd ~/honcho && .venv/bin/python -m uvicorn app.main:app --port 8000"
echo ""
