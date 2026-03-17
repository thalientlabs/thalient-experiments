#!/usr/bin/env python3
"""Stop hook: Write session summary for continuity across sessions."""
import json
import sys
import os
import subprocess
from datetime import datetime, timezone

def main():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, Exception):
        hook_input = {}

    agent_name = os.environ.get("AGENT_NAME", "unknown")
    session_dir = "sessions"
    os.makedirs(session_dir, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")

    # Get recent git activity
    try:
        git_log = subprocess.run(
            ["git", "log", "--oneline", "-20"],
            capture_output=True, text=True, timeout=10
        ).stdout.strip()
    except Exception:
        git_log = "Could not read git log"

    # Get git diff stat
    try:
        git_diff = subprocess.run(
            ["git", "diff", "--stat", "HEAD~5..HEAD"],
            capture_output=True, text=True, timeout=10
        ).stdout.strip()
    except Exception:
        git_diff = ""

    # Read status file
    status = {}
    status_file = f"status/{agent_name}.json"
    if os.path.exists(status_file):
        try:
            with open(status_file) as f:
                status = json.load(f)
        except Exception:
            pass

    # Read task file
    task_content = ""
    task_file = f"tasks/{agent_name}.md"
    if os.path.exists(task_file):
        try:
            with open(task_file) as f:
                task_content = f.read()[:1000]
        except Exception:
            pass

    # Write markdown summary
    summary_file = os.path.join(session_dir, f"{agent_name}-{timestamp}.md")
    with open(summary_file, "w") as f:
        f.write(f"# Session Summary: {agent_name}\n\n")
        f.write(f"**Ended:** {datetime.now(timezone.utc).isoformat()}\n")
        f.write(f"**Tool calls:** {status.get('tool_count', 'unknown')}\n\n")
        if task_content:
            f.write(f"## Task\n\n{task_content}\n\n")
        f.write(f"## Recent Commits\n\n```\n{git_log}\n```\n\n")
        if git_diff:
            f.write(f"## Files Changed\n\n```\n{git_diff}\n```\n\n")

    # Update status to stopped
    status["status"] = "stopped"
    status["stopped_at"] = datetime.now(timezone.utc).isoformat()
    with open(status_file, "w") as f:
        json.dump(status, f, indent=2)

    sys.exit(0)

if __name__ == "__main__":
    main()
