#!/usr/bin/env python3
"""
bootstrap_profiles.py
=====================
Discovers active Hermes agent profiles at ~/.hermes/profiles/*/SOUL.md
and optionally appends the Session Initialization Protocol block to each one.

The Session Initialization Protocol instructs the agent to:
  1. Read ~/brain/AGENTS.md at the start of every new session
  2. Read ~/brain/timeline.json to understand recent context
  3. Navigate to the relevant brain domain directory

Run this after Hermes is set up and profiles are created.
Usage: python3 scripts/bootstrap_profiles.py
"""

import os
import sys
from pathlib import Path

HERMES_DIR = Path.home() / ".hermes"
PROFILES_DIR = HERMES_DIR / "profiles"
MAIN_SOUL = HERMES_DIR / "SOUL.md"

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
