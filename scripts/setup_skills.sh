#!/usr/bin/env bash
# =============================================================================
# setup_skills.sh
# Hermes Custom Skills — Setup Script
#
# Copies the 'brain' and 'brain-search' custom skills to ~/.hermes/skills/
# and sets up symlinks under ~/.gemini/config/skills/ for IDE access.
#
# Safe to re-run: will not overwrite existing directories.
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
HERMES_SKILLS_DIR="$HOME/.hermes/skills"
GEMINI_SKILLS_DIR="$HOME/.gemini/config/skills"

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║       Hermes Custom Skills — Setup Script        ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# -----------------------------------------------------------------------------
# 1. Verify Hermes is installed
# -----------------------------------------------------------------------------
echo "► Verifying Hermes skills directory..."

if [ ! -d "$HERMES_SKILLS_DIR" ]; then
    mkdir -p "$HERMES_SKILLS_DIR"
    echo "  ✓ Created Hermes skills directory: $HERMES_SKILLS_DIR"
else
    echo "  — Hermes skills directory exists: $HERMES_SKILLS_DIR"
fi

# -----------------------------------------------------------------------------
# 2. Copy skill templates
# -----------------------------------------------------------------------------
echo ""
echo "► Installing custom skills..."

install_skill() {
    local name="$1"
    local src="$REPO_ROOT/templates/skills/$name"
    local dst="$HERMES_SKILLS_DIR/$name"

    if [ ! -d "$dst" ]; then
        cp -r "$src" "$dst"
        # Sanitize references of USERNAME in destination files
        find "$dst" -type f -name "*.md" -exec sed -i '' "s/USERNAME/$(whoami)/g" {} + 2>/dev/null || true
        echo "  ✓ Installed skill: $name"
    else
        echo "  — Skill already exists (skipping): $name"
    fi
}

install_skill "brain"
install_skill "brain-search"
install_skill "honcho-management"

# -----------------------------------------------------------------------------
# 3. Create Gemini IDE Symlinks
# -----------------------------------------------------------------------------
echo ""
echo "► Configuring Gemini IDE symlinks..."

if [ -d "$GEMINI_SKILLS_DIR" ]; then
    link_skill() {
        local name="$1"
        local target="$HERMES_SKILLS_DIR/$name"
        local symlink="$GEMINI_SKILLS_DIR/$name"

        if [ ! -e "$symlink" ]; then
            ln -s "$target" "$symlink"
            echo "  ✓ Linked $name → $target"
        else
            echo "  — Symlink already exists (skipping): $name"
        fi
    }

    link_skill "brain"
    link_skill "brain-search"
    link_skill "honcho-management"
else
    echo "  — Gemini configuration directory (~/.gemini/config/skills) not found."
    echo "    Skipping IDE symlinks. (This is normal if you only use CLI/Hermes without Antigravity IDE)."
fi


# -----------------------------------------------------------------------------
# Done
# -----------------------------------------------------------------------------
echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  ✓ Custom skills setup complete!                 ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "  Skills location: ~/.hermes/skills/"
echo "  • brain"
echo "  • brain-search"
echo ""
