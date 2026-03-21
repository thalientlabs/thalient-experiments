#!/usr/bin/env python3
"""PreCompact hook: Save checkpoint before context compaction."""
import json
import sys
import os
import glob
from datetime import datetime, timezone

def main():
    # Read any input (PreCompact may provide context)
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, Exception):
        hook_input = {}

    agent_name = os.environ.get("AGENT_NAME", "unknown")
    repo_root = os.environ.get("REPO_PATH", "/home/researcher/research-repo")

    checkpoint_dir = os.path.join(".agent", "checkpoints")
    os.makedirs(checkpoint_dir, exist_ok=True)

    # Gather current state
    checkpoint = {
        "agent": agent_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "reason": "pre-compact",
    }

    # Read current task (at repo root, since orchestrator writes them there)
    task_file = os.path.join(repo_root, "tasks", f"{agent_name}.md")
    if os.path.exists(task_file):
        with open(task_file) as f:
            checkpoint["current_task"] = f.read()[:2000]

    # Read current status (agent-local)
    status_file = os.path.join(".agent", f"{agent_name}.json")
    if os.path.exists(status_file):
        with open(status_file) as f:
            checkpoint["last_status"] = json.load(f)

    # Read pending proposals (at repo root)
    proposals = glob.glob(os.path.join(repo_root, "proposals", "*.md"))
    pending = []
    for p in proposals:
        try:
            with open(p) as f:
                content = f.read()
                if "status: approved" not in content and "status: rejected" not in content:
                    pending.append({"file": os.path.basename(p), "preview": content[:500]})
        except Exception:
            pass
    checkpoint["pending_proposals"] = pending

    # Read recent results (look in Experiments dirs under cwd which is the topic root)
    results = glob.glob("Experiments/*/Results/*-manifest.json")
    recent_results = []
    for r in sorted(results, key=os.path.getmtime, reverse=True)[:5]:
        try:
            with open(r) as f:
                recent_results.append(json.load(f))
        except Exception:
            pass
    checkpoint["recent_results"] = recent_results

    # Write checkpoint (agent-local)
    checkpoint_file = os.path.join(checkpoint_dir, f"{agent_name}-latest.md")
    with open(checkpoint_file, "w") as f:
        f.write(f"# Checkpoint for {agent_name}\n\n")
        f.write(f"_Saved at {checkpoint['timestamp']} before context compaction._\n\n")
        if checkpoint.get("current_task"):
            f.write(f"## Current Task\n\n{checkpoint['current_task']}\n\n")
        if pending:
            f.write(f"## Pending Proposals ({len(pending)})\n\n")
            for p in pending:
                f.write(f"- {p['file']}\n")
            f.write("\n")
        if recent_results:
            f.write(f"## Recent Results\n\n")
            for r in recent_results:
                f.write(f"- {r.get('experiment', 'unknown')}: {r.get('status', 'unknown')}\n")
            f.write("\n")
        f.write("---\n\n_Read this file first after compaction to recover your context._\n")

    # Also write raw JSON for programmatic access
    checkpoint_json = os.path.join(checkpoint_dir, f"{agent_name}-latest.json")
    with open(checkpoint_json, "w") as f:
        json.dump(checkpoint, f, indent=2)

    sys.exit(0)

if __name__ == "__main__":
    main()
