#!/bin/zsh
# OKF Brain — Idempotent Setup Script
# Runs initialization for zsh env variables, Hermes post-update hooks, and Obsidian hooks.

BRAIN_ROOT="${0:a:h:h}"
ZSH_CONFIG="$HOME/.zshrc"

echo "Initializing OKF Brain Workspace setup..."
echo "Brain Root is: $BRAIN_ROOT"

# 1. Add BRAIN_PATH env variable if it does not exist
if ! grep -q "export BRAIN_PATH=" "$ZSH_CONFIG"; then
  echo "\n# OKF Brain Root Directory Configuration" >> "$ZSH_CONFIG"
  echo "export BRAIN_PATH=\"\$HOME/brain\"" >> "$ZSH_CONFIG"
  echo "✓ Added BRAIN_PATH env variable to $ZSH_CONFIG"
else
  echo "✓ BRAIN_PATH is already configured in $ZSH_CONFIG"
fi


# 3. Create initial empty Obsidian configs so it is ready
OBSIDIAN_DIR="$BRAIN_ROOT/.obsidian"
mkdir -p "$OBSIDIAN_DIR"
cat > "$OBSIDIAN_DIR/appearance.json" << 'EOF'
{
  "theme": "obsidian",
  "baseFontSize": 16
}
EOF
echo "✓ Created starter Obsidian config at $OBSIDIAN_DIR"

# 4. Verify AGENTS.md exists (Hermes auto-discovery)
if [ -f "$BRAIN_ROOT/AGENTS.md" ]; then
  echo "✓ AGENTS.md exists — Hermes will auto-load on brain directory access"
else
  echo "⚠️ AGENTS.md missing from brain root. Hermes cannot auto-discover context."
  echo "  → Run: create ~/brain/AGENTS.md using the okf skill"
fi

echo "\nInitialization successfully completed! Please run 'source ~/.zshrc' to update your environment variables."
