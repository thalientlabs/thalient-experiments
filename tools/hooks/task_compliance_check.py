#!/usr/bin/env python3
"""Stop hook: Check that agent stayed on task by reviewing changes vs assignment."""
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
    repo_root = os.environ.get("REPO_PATH", "/home/researcher/research-repo")

    monitoring_dir = os.path.join(".agent", "monitoring")
    os.makedirs(monitoring_dir, exist_ok=True)

    # Read the task assignment (at repo root)
    task_content = ""
    task_file = os.path.join(repo_root, "tasks", f"{agent_name}.md")
    if os.path.exists(task_file):
        try:
            with open(task_file) as f:
                task_content = f.read()
        except Exception:
            pass

    # Get the diff of all changes
    try:
        diff_stat = subprocess.run(
            ["git", "diff", "--stat", "main...HEAD"],
            capture_output=True, text=True, timeout=10
        ).stdout.strip()
    except Exception:
        diff_stat = "Could not compute diff"

    # Get changed files list
    try:
        changed_files = subprocess.run(
            ["git", "diff", "--name-only", "main...HEAD"],
            capture_output=True, text=True, timeout=10
        ).stdout.strip()
    except Exception:
        changed_files = ""

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    report_file = os.path.join(monitoring_dir, f"compliance-{agent_name}-{timestamp}.md")

    with open(report_file, "w") as f:
        f.write(f"# Task Compliance Report: {agent_name}\n\n")
        f.write(f"**Generated:** {datetime.now(timezone.utc).isoformat()}\n\n")
        f.write(f"## Assigned Task\n\n{task_content or 'No task file found'}\n\n")
        f.write(f"## Files Changed\n\n```\n{diff_stat}\n```\n\n")
        if changed_files:
            f.write(f"## Changed File List\n\n")
            for cf in changed_files.split("\n"):
                f.write(f"- `{cf}`\n")
            f.write("\n")
        f.write("## Assessment\n\n_Review manually: did the changes align with the assigned task?_\n")

    sys.exit(0)

if __name__ == "__main__":
    main()
