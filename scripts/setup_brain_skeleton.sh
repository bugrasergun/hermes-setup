#!/usr/bin/env bash
# =============================================================================
# setup_brain_skeleton.sh
# OKF Brain Vault — Idempotent Setup Script
#
# Creates the ~/brain/ directory skeleton, copies custom scripts,
# installs git hooks, and configures environment variables.
#
# Safe to re-run: will not overwrite existing files.
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
BRAIN_ROOT="$HOME/brain"
ZSH_CONFIG="$HOME/.zshrc"

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║        OKF Brain Vault — Setup Script            ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# -----------------------------------------------------------------------------
# 1. Create directory structure
# -----------------------------------------------------------------------------
echo "► Creating Brain directory structure..."

DIRS=(
    "$BRAIN_ROOT"
    "$BRAIN_ROOT/agents"
    "$BRAIN_ROOT/finance"
    "$BRAIN_ROOT/growth"
    "$BRAIN_ROOT/health"
    "$BRAIN_ROOT/learning"
    "$BRAIN_ROOT/network"
    "$BRAIN_ROOT/playbooks"
    "$BRAIN_ROOT/projects"
    "$BRAIN_ROOT/references"
    "$BRAIN_ROOT/references/sources"
    "$BRAIN_ROOT/reports"
    "$BRAIN_ROOT/reports/daily"
    "$BRAIN_ROOT/scripts"
    "$BRAIN_ROOT/self"
    "$BRAIN_ROOT/tech"
)

for dir in "${DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo "  ✓ Created: $dir"
    else
        echo "  — Already exists: $dir"
    fi
done

# -----------------------------------------------------------------------------
# 2. Copy template files (only if they don't exist)
# -----------------------------------------------------------------------------
echo ""
echo "► Copying base template files..."

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

# Base vault files
copy_if_missing "$REPO_ROOT/templates/brain/AGENTS.md"      "$BRAIN_ROOT/AGENTS.md"
copy_if_missing "$REPO_ROOT/templates/brain/index.md"       "$BRAIN_ROOT/index.md"
copy_if_missing "$REPO_ROOT/templates/brain/timeline.json"  "$BRAIN_ROOT/timeline.json"
copy_if_missing "$REPO_ROOT/templates/brain/.gitignore"     "$BRAIN_ROOT/.gitignore"
copy_if_missing "$REPO_ROOT/templates/brain/.stignore"      "$BRAIN_ROOT/.stignore"

# Brain scripts
copy_if_missing "$REPO_ROOT/templates/brain_scripts/validate.py"    "$BRAIN_ROOT/scripts/validate.py"
copy_if_missing "$REPO_ROOT/templates/brain_scripts/validate.sh"    "$BRAIN_ROOT/scripts/validate.sh"
copy_if_missing "$REPO_ROOT/templates/brain_scripts/index_brain.py" "$BRAIN_ROOT/scripts/index_brain.py"

# Make scripts executable
chmod +x "$BRAIN_ROOT/scripts/validate.sh" 2>/dev/null || true

# -----------------------------------------------------------------------------
# 3. Initialize git repository
# -----------------------------------------------------------------------------
echo ""
echo "► Setting up Git repository..."

if [ ! -d "$BRAIN_ROOT/.git" ]; then
    git -C "$BRAIN_ROOT" init
    git -C "$BRAIN_ROOT" checkout -b main 2>/dev/null || true
    echo "  ✓ Git repository initialized"
else
    echo "  — Git repository already exists"
fi

# -----------------------------------------------------------------------------
# 4. Install git post-commit hook
# -----------------------------------------------------------------------------
echo ""
echo "► Installing git post-commit hook..."

HOOK_SRC="$REPO_ROOT/templates/brain_scripts/post-commit"
HOOK_DST="$BRAIN_ROOT/.git/hooks/post-commit"

if [ ! -f "$HOOK_DST" ]; then
    cp "$HOOK_SRC" "$HOOK_DST"
    chmod +x "$HOOK_DST"
    echo "  ✓ Installed post-commit hook"
else
    echo "  — post-commit hook already exists (not overwriting)"
fi

# -----------------------------------------------------------------------------
# 5. Configure environment variable
# -----------------------------------------------------------------------------
echo ""
echo "► Configuring environment variables..."

if ! grep -q "export BRAIN_PATH=" "$ZSH_CONFIG" 2>/dev/null; then
    echo "" >> "$ZSH_CONFIG"
    echo "# OKF Brain Root Directory" >> "$ZSH_CONFIG"
    echo "export BRAIN_PATH=\"\$HOME/brain\"" >> "$ZSH_CONFIG"
    echo "  ✓ Added BRAIN_PATH to $ZSH_CONFIG"
else
    echo "  — BRAIN_PATH already configured"
fi

# -----------------------------------------------------------------------------
# 6. Create starter Obsidian config
# -----------------------------------------------------------------------------
echo ""
echo "► Creating starter Obsidian config..."

OBSIDIAN_DIR="$BRAIN_ROOT/.obsidian"
mkdir -p "$OBSIDIAN_DIR"

if [ ! -f "$OBSIDIAN_DIR/appearance.json" ]; then
    cat > "$OBSIDIAN_DIR/appearance.json" <<'EOF'
{
  "theme": "obsidian",
  "baseFontSize": 16
}
EOF
    echo "  ✓ Created .obsidian/appearance.json"
else
    echo "  — .obsidian/appearance.json already exists"
fi

if [ ! -f "$OBSIDIAN_DIR/app.json" ]; then
    cat > "$OBSIDIAN_DIR/app.json" <<'EOF'
{
  "legacyEditor": false,
  "livePreview": true,
  "defaultViewMode": "source",
  "foldHeading": true,
  "strictLineBreaks": false
}
EOF
    echo "  ✓ Created .obsidian/app.json"
fi

# -----------------------------------------------------------------------------
# 7. Install post-update hook for Hermes
# -----------------------------------------------------------------------------
echo ""
echo "► Setting up Hermes integration..."

if [ -d "$HOME/.hermes" ]; then
    HERMES_HOOKS="$HOME/.hermes/hooks"
    mkdir -p "$HERMES_HOOKS"

    cat > "$HERMES_HOOKS/post-update-brain.sh" <<'EOF'
#!/bin/zsh
# Post-update hook for Hermes
# Agent identity comes from each profile's SOUL.md.
# The main SOUL.md at ~/.hermes/SOUL.md is the canonical identity file.
echo "✓ SOUL.md is the canonical identity source."
EOF
    chmod +x "$HERMES_HOOKS/post-update-brain.sh"
    echo "  ✓ Installed post-update hook in $HERMES_HOOKS"
else
    echo "  ⚠ Hermes not found at ~/.hermes — skipping Hermes hooks"
fi

# -----------------------------------------------------------------------------
# Done
# -----------------------------------------------------------------------------
echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  ✓ Brain vault setup complete!                   ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "  Brain vault:  ~/brain/"
echo "  Scripts:      ~/brain/scripts/"
echo ""
echo "  Next step: run source ~/.zshrc to load BRAIN_PATH"
echo "  Then:      Open Obsidian → 'Open folder as vault' → select ~/brain/"
echo ""
