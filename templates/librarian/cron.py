import json
import os
import subprocess
import sys
import time
import datetime
import requests
import timeline as tl
from config import OLLAMA_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT, REPORTS_DIR, BRAIN_DIR, VALIDATE_SCRIPT

CRON_SYSTEM_PROMPT = """You are an expert technical writer and analyst. Your task is to generate a comprehensive Daily Report based on the provided atomic timeline entries recorded over the past 24 hours.

Input format: A JSON array of timeline entries (decisions, discoveries, problems, patterns, tasks).
Output format: A well-structured Markdown document starting with a YAML frontmatter block.

The YAML frontmatter MUST be enclosed in '---' (three dashes) and NOT backticks. Example:
---
type: Daily Report
title: Günlük Rapor — YYYY-MM-DD
date: YYYY-MM-DD
tags: [report, daily]
description: A short one-line summary
timestamp: 'YYYY-MM-DDT23:59:59+03:00'
---

The report body MUST include:
1. An executive summary of the day's activities (in Turkish).
2. Categorized sections (e.g., Important Decisions, Key Discoveries, Ongoing Problems, Tasks/Next Steps).
3. Group related entries logically by project or agent.
4. Use clear, professional language (Output language must be Turkish, even though instructions are in English).

Do not invent information. Rely strictly on the provided timeline entries. If there are no entries, state that the day was inactive."""

def git_commit_and_push(report_date_str):
    """Validate brain bundle, then commit and push to GitHub if no errors."""
    import logging
    logging.info("Running brain validator...")

    # 1. Validate
    result = subprocess.run(
        [sys.executable, VALIDATE_SCRIPT],
        capture_output=True, text=True, cwd=BRAIN_DIR
    )
    output = result.stdout + result.stderr

    if "Errors found: 0" not in output:
        logging.error(f"Brain validation FAILED. Aborting git push.\n{output}")
        return

    logging.info("Validation passed (0 errors). Proceeding with git commit & push.")

    # 2. Git add — only the files cron touches
    files_to_add = [
        "reports/daily/",
        "timeline.json",
    ]
    env = os.environ.copy()
    env.pop("GITHUB_TOKEN", None)  # IDE injected dummy token — must remove

    add_result = subprocess.run(
        ["git", "add"] + files_to_add,
        capture_output=True, text=True, cwd=BRAIN_DIR, env=env
    )
    if add_result.returncode != 0:
        logging.error(f"git add failed:\n{add_result.stderr}")
        return

    # 3. Git commit
    commit_msg = f"chore(daily): auto-report {report_date_str} [librarian]"
    commit_result = subprocess.run(
        ["git", "commit", "-m", commit_msg],
        capture_output=True, text=True, cwd=BRAIN_DIR, env=env
    )
    if commit_result.returncode != 0:
        # Nothing new to commit is not a failure
        if "nothing to commit" in commit_result.stdout:
            logging.info("Nothing to commit — already up to date.")
            return
        logging.error(f"git commit failed:\n{commit_result.stderr}")
        return

    logging.info(f"git commit OK: {commit_msg}")

    # 4. Git push
    push_result = subprocess.run(
        ["git", "push"],
        capture_output=True, text=True, cwd=BRAIN_DIR, env=env
    )
    if push_result.returncode != 0:
        logging.error(f"git push failed:\n{push_result.stderr}")
        return

    logging.info(f"git push OK — brain/{report_date_str} report is live on GitHub.")


def generate_daily_report():
    import logging
    timeline = tl.get_timeline()
    entries = timeline.get("entries", [])
    
    if not entries:
        logging.info("No entries to report. Updating timeline date to today.")
        timeline["date"] = datetime.date.today().isoformat()
        tl.save_timeline(timeline)
        return

    # Rapor sabah 06:00'da çalıştığı için bir önceki günün faaliyetlerini kapsar.
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    report_date_str = yesterday.isoformat()
    
    prompt = f"TIMELINE ENTRIES FOR {report_date_str}:\n{json.dumps(entries, indent=2)}\n\nPlease generate the Daily Report in Turkish."

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": CRON_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "options": {
            "temperature": 0.2
        },
        "stream": False
    }

    try:
        logging.info(f"Generating daily report for {report_date_str} with {len(entries)} entries...")
        response = requests.post(OLLAMA_URL, json=payload, timeout=OLLAMA_TIMEOUT)
        response.raise_for_status()
        
        result_json = response.json()
        report_content = result_json.get('message', {}).get('content', '')
        
        # Ek istatistikler eklenebilir
        stats = f"\n\n---\n*Otomatik Librarian Raporu. İşlenen entry sayısı: {len(entries)}*"
        final_report = report_content + stats
        
        os.makedirs(REPORTS_DIR, exist_ok=True)
        report_path = os.path.join(REPORTS_DIR, f"{report_date_str}.md")
        
        # If a report already exists for that day (e.g. manual trigger), append instead of overwriting
        if os.path.exists(report_path):
            logging.info(f"Report for {report_date_str} already exists. Appending as supplementary section.")
            with open(report_path, "a", encoding="utf-8") as f:
                f.write(f"\n\n---\n\n## Ek Rapor (Supplementary)\n\n")
                f.write(final_report)
        else:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(final_report)
            
        logging.info(f"Report generated successfully: {report_path}")
        
        # Otomatik olarak index.md dosyasını güncelle
        index_path = os.path.join(REPORTS_DIR, "index.md")
        if os.path.exists(index_path):
            with open(index_path, "a", encoding="utf-8") as f:
                f.write(f"* [{report_date_str}]({report_date_str}.md) - {len(entries)} adet aktiviteyi içeren otomatik günlük özet.\n")
        
        # Agent snapshot güncellemesi
        snapshots = timeline.get("agent_snapshots", {})
        for entry in entries:
            agent = entry.get("agent_id")
            if agent:
                if agent not in snapshots:
                    snapshots[agent] = {}
                snapshots[agent]["last_daily_report"] = f"brain/reports/daily/{report_date_str}.md"
                
        timeline["agent_snapshots"] = snapshots
        timeline["entries"] = []
        timeline["date"] = datetime.date.today().isoformat() # Bugünün tarihiyle yeni güne başlıyoruz
        
        tl.save_timeline(timeline)

        # Validate brain bundle ve GitHub'a push
        git_commit_and_push(report_date_str)
        
    except Exception as e:
        logging.error(f"Failed to generate daily report: {e}", exc_info=True)

if __name__ == "__main__":
    generate_daily_report()
