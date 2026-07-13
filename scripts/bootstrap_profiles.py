#!/usr/bin/env python3
"""
bootstrap_profiles.py
=====================
Discovers active Hermes agent profiles at ~/.hermes/profiles/*/SOUL.md
and optionally appends the Session Initialization Protocol block to each one.
Also patches ~/.hermes/config.yaml with the Vault Custodian Protocol
in the environment_hint field.

The Session Initialization Protocol instructs the agent to:
  1. Read ~/brain/AGENTS.md at the start of every new session
  2. Read ~/brain/timeline.json to understand recent context
  3. Navigate to the relevant brain domain directory

The Vault Custodian Protocol (environment_hint) instructs the agent to:
  1. Read ~/brain/timeline.json to restore cross-session context
  2. Load the 'brain' skill for vault operations
  3. Load the 'brain-search' skill for semantic discovery queries

Run this after Hermes is set up and profiles are created.
Usage: python3 scripts/bootstrap_profiles.py
"""

import os
import re
import sys
from pathlib import Path

HERMES_DIR = Path.home() / ".hermes"
PROFILES_DIR = HERMES_DIR / "profiles"
MAIN_SOUL = HERMES_DIR / "SOUL.md"
CONFIG_YAML = HERMES_DIR / "config.yaml"

SESSION_PROTOCOL_MARKER = "<!-- session-init-protocol -->"
SESSION_PROTOCOL = """
<!-- session-init-protocol -->
## Session Initialization Protocol

At the start of every new session, before responding to any user message:

1. **Read brain context**: Check `~/brain/AGENTS.md` for vault rules and directory map.
2. **Load timeline**: Read `~/brain/timeline.json` to understand recent decisions and context from past sessions.
3. **Navigate your domain**: Based on your role, navigate to your relevant brain directory.
4. **Acknowledge silently**: Do not announce this initialization to the user unless asked.

This protocol ensures continuity across sessions. The timeline is written by the Librarian daemon — you are a reader, not a writer.
"""

ENVIRONMENT_HINT_MARKER = "# vault-custodian-protocol-v2"
ENVIRONMENT_HINT_VALUE = (
    "Vault Custodian Protocol: You are the custodian of the ~/brain/ "
    "OKF vault. At the start of every session: (1) Read ~/brain/timeline.json to restore "
    "cross-session context — it contains the last session ID, active topics, and recent "
    "decisions. (2) Load the 'brain' skill using `skill_view(name='brain')` to fetch "
    "vault traversal, validation, and git-sync rules. (3) For discovery queries (finding "
    "what the vault contains about a topic), load the 'brain-search' skill using "
    "`skill_view(name='brain-search')` and run a semantic vector search instead of "
    "manually traversing directories. brain = vault operations; brain-search = semantic "
    "discovery. Never guess — always read first."
)


def check_soul_file(soul_path: Path) -> tuple[bool, str]:
    """Check if a SOUL.md file already has the session protocol."""
    if not soul_path.exists():
        return False, "not_found"
    content = soul_path.read_text(encoding="utf-8")
    if SESSION_PROTOCOL_MARKER in content:
        return True, "already_has_protocol"
    return False, "missing_protocol"


def bootstrap_soul(soul_path: Path, dry_run: bool = False) -> bool:
    """Append the session initialization protocol to a SOUL.md file."""
    has_protocol, status = check_soul_file(soul_path)

    if status == "not_found":
        print(f"  ⚠  SOUL.md not found: {soul_path}")
        return False

    if has_protocol:
        print(f"  — Already has protocol: {soul_path.parent.name}/SOUL.md")
        return True

    if dry_run:
        print(f"  [DRY RUN] Would append protocol to: {soul_path.parent.name}/SOUL.md")
        return True

    with open(soul_path, "a", encoding="utf-8") as f:
        f.write(SESSION_PROTOCOL)
    print(f"  ✓ Appended protocol to: {soul_path.parent.name}/SOUL.md")
    return True


def patch_environment_hint(dry_run: bool = False) -> bool:
    """
    Patch the environment_hint field in ~/.hermes/config.yaml with the
    Vault Custodian Protocol (includes timeline.json + brain-search references).
    Safe to re-run: checks for the marker comment before patching.
    """
    if not CONFIG_YAML.exists():
        print(f"  ⚠  config.yaml not found at {CONFIG_YAML} — skipping environment_hint patch")
        return False

    content = CONFIG_YAML.read_text(encoding="utf-8")

    # Already patched?
    if ENVIRONMENT_HINT_MARKER in content:
        print("  — environment_hint already contains Vault Custodian Protocol (skipping)")
        return True

    # Build the new environment_hint block (YAML scalar, single-quoted, folded)
    # We replace any existing environment_hint line(s) or insert after environment_probe
    new_hint_yaml = (
        f"  environment_hint: '{ENVIRONMENT_HINT_VALUE}' {ENVIRONMENT_HINT_MARKER}\n"
    )

    # Pattern: match existing environment_hint (may span multiple lines due to YAML folding)
    existing_pattern = re.compile(
        r"^  environment_hint:.*?(?=\n  \S|\Z)", re.MULTILINE | re.DOTALL
    )

    if existing_pattern.search(content):
        # Replace existing environment_hint
        new_content = existing_pattern.sub(new_hint_yaml.rstrip("\n"), content)
        action = "Replaced existing environment_hint"
    else:
        # Insert after environment_probe line
        new_content = re.sub(
            r"(  environment_probe:.*\n)",
            r"\1" + new_hint_yaml,
            content,
        )
        action = "Inserted environment_hint after environment_probe"

    if new_content == content:
        print("  ⚠  Could not locate insertion point in config.yaml — manual edit required")
        print(f"     Add this under agent.environment_hint:\n     {ENVIRONMENT_HINT_VALUE}")
        return False

    if dry_run:
        print(f"  [DRY RUN] Would patch config.yaml: {action}")
        return True

    CONFIG_YAML.write_text(new_content, encoding="utf-8")
    print(f"  ✓ config.yaml patched: {action}")
    return True


def main():
    print()
    print("╔══════════════════════════════════════════════════╗")
    print("║  Hermes Profile Bootstrap — Session Protocol     ║")
    print("╚══════════════════════════════════════════════════╝")
    print()

    # Check Hermes exists
    if not HERMES_DIR.exists():
        print("✗ Hermes not found at ~/.hermes")
        print("  Please install Hermes first.")
        sys.exit(1)

    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("  [DRY RUN MODE — no files will be modified]")
        print()

    # -------------------------------------------------------------------------
    # Part 1: Patch environment_hint in config.yaml
    # -------------------------------------------------------------------------
    print("► Patching Hermes config.yaml environment_hint...")
    patch_environment_hint(dry_run=dry_run)
    print()

    # -------------------------------------------------------------------------
    # Part 2: Append Session Protocol to SOUL.md files
    # -------------------------------------------------------------------------
    # Discover profiles
    souls_to_process: list[Path] = []

    # Primary agent (main SOUL.md)
    if MAIN_SOUL.exists():
        souls_to_process.append(MAIN_SOUL)

    # Profile-specific SOUL.md files
    if PROFILES_DIR.exists():
        for profile_dir in sorted(PROFILES_DIR.iterdir()):
            if profile_dir.is_dir():
                soul = profile_dir / "SOUL.md"
                if soul.exists():
                    souls_to_process.append(soul)

    if not souls_to_process:
        print("  ⚠  No SOUL.md files found in ~/.hermes/ or ~/.hermes/profiles/")
        print("     Create your agent profiles first, then re-run this script.")
        sys.exit(0)

    print(f"► Found {len(souls_to_process)} SOUL.md file(s):")
    for soul in souls_to_process:
        rel = soul.relative_to(Path.home())
        print(f"  • ~/{rel}")

    print()
    if not dry_run:
        response = input("  Append Session Initialization Protocol to all? [Y/n]: ").strip()
        if response.lower() == "n":
            print("  Aborted.")
            sys.exit(0)

    print()
    print("► Processing...")
    success_count = 0
    for soul in souls_to_process:
        if bootstrap_soul(soul, dry_run=dry_run):
            success_count += 1

    print()
    print("╔══════════════════════════════════════════════════╗")
    print(f"║  ✓ Done! Processed {success_count}/{len(souls_to_process)} profiles.{'  ' * (8 - len(str(success_count)) - len(str(len(souls_to_process))))}║")
    print("╚══════════════════════════════════════════════════╝")
    print()
    print("  Restart Hermes for changes to take effect.")
    print()


if __name__ == "__main__":
    main()

