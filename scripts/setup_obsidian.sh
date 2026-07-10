#!/usr/bin/env bash
# =============================================================================
# setup_obsidian.sh
# Obsidian Vault Configuration — Setup Script
#
# Ensures the ~/brain/.obsidian/ configuration is correctly initialized
# and guides the user through opening the vault in Obsidian.
# =============================================================================

set -euo pipefail

BRAIN_ROOT="$HOME/brain"
OBSIDIAN_DIR="$BRAIN_ROOT/.obsidian"

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║        Obsidian Vault — Setup Script             ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# -----------------------------------------------------------------------------
# 1. Verify brain vault exists
# -----------------------------------------------------------------------------
echo "► Verifying Brain vault..."

if [ ! -d "$BRAIN_ROOT" ]; then
    echo "  ✗ ~/brain/ not found!"
    echo "    Please run scripts/setup_brain_skeleton.sh first."
    exit 1
fi
echo "  ✓ Brain vault found at $BRAIN_ROOT"

# -----------------------------------------------------------------------------
# 2. Create .obsidian config directory and base files
# -----------------------------------------------------------------------------
echo ""
echo "► Setting up Obsidian configuration..."

mkdir -p "$OBSIDIAN_DIR"

# app.json — core editor settings
if [ ! -f "$OBSIDIAN_DIR/app.json" ]; then
    cat > "$OBSIDIAN_DIR/app.json" <<'EOF'
{
  "legacyEditor": false,
  "livePreview": true,
  "defaultViewMode": "source",
  "foldHeading": true,
  "strictLineBreaks": false,
  "showLineNumber": false,
  "readableLineLength": true,
  "spellcheck": false,
  "alwaysUpdateLinks": true
}
EOF
    echo "  ✓ Created app.json"
else
    echo "  — app.json already exists"
fi

# appearance.json — theme settings
if [ ! -f "$OBSIDIAN_DIR/appearance.json" ]; then
    cat > "$OBSIDIAN_DIR/appearance.json" <<'EOF'
{
  "theme": "obsidian",
  "baseFontSize": 16,
  "interfaceFontFamily": "",
  "textFontFamily": "",
  "monospaceFontFamily": ""
}
EOF
    echo "  ✓ Created appearance.json"
else
    echo "  — appearance.json already exists"
fi

# hotkeys.json — empty placeholder
if [ ! -f "$OBSIDIAN_DIR/hotkeys.json" ]; then
    echo "{}" > "$OBSIDIAN_DIR/hotkeys.json"
    echo "  ✓ Created hotkeys.json"
fi

# core-plugins.json — enable useful built-in plugins
if [ ! -f "$OBSIDIAN_DIR/core-plugins.json" ]; then
    cat > "$OBSIDIAN_DIR/core-plugins.json" <<'EOF'
[
  "file-explorer",
  "global-search",
  "switcher",
  "graph",
  "backlink",
  "canvas",
  "outgoing-link",
  "tag-pane",
  "properties",
  "page-preview",
  "daily-notes",
  "templates",
  "command-palette",
  "note-composer",
  "editor-status",
  "starred",
  "markdown-importer",
  "word-count",
  "outline"
]
EOF
    echo "  ✓ Created core-plugins.json"
else
    echo "  — core-plugins.json already exists"
fi

# community-plugins.json — empty (user installs manually)
if [ ! -f "$OBSIDIAN_DIR/community-plugins.json" ]; then
    echo "[]" > "$OBSIDIAN_DIR/community-plugins.json"
    echo "  ✓ Created community-plugins.json (empty)"
fi

# workspace.json gitignore note
echo "  (workspace.json is gitignored — Obsidian will create it on first open)"

# -----------------------------------------------------------------------------
# 3. Open Obsidian if installed
# -----------------------------------------------------------------------------
echo ""
echo "► Opening Obsidian..."

if [ -d "/Applications/Obsidian.app" ]; then
    echo "  ✓ Obsidian found. Attempting to open vault..."
    # Use obsidian:// URI to open a specific vault
    open "obsidian://open?path=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$BRAIN_ROOT'))")" 2>/dev/null || \
    open -a Obsidian "$BRAIN_ROOT" 2>/dev/null || \
    echo "  — Could not auto-open vault. Please open manually (see instructions below)."
else
    echo "  ⚠ Obsidian not found at /Applications/Obsidian.app"
    echo "    Download from: https://obsidian.md"
fi

# -----------------------------------------------------------------------------
# Done
# -----------------------------------------------------------------------------
echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  ✓ Obsidian setup complete!                      ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "  To open the Brain vault in Obsidian manually:"
echo "  1. Open Obsidian"
echo "  2. Click 'Open folder as vault'"
echo "  3. Select: $BRAIN_ROOT"
echo ""
echo "  Recommended Community Plugins (install via Settings → Community plugins):"
echo "  • Templater    — Template support with scripting"
echo "  • Dataview     — Query vault like a database (tables, lists)"
echo "  • Calendar     — Calendar view for daily notes"
echo "  • Git          — Auto-commit/push vault changes"
echo ""
