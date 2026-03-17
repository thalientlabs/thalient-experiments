#!/usr/bin/env python3
"""SessionStart hook: Inject recent session context for continuity."""
import json
import sys
import os
import glob

def main():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, Exception):
        hook_input = {}

    agent_name = os.environ.get("AGENT_NAME", "unknown")

    # Read latest checkpoint if it exists
    checkpoint_file = f"checkpoints/{agent_name}-latest.md"
    checkpoint_content = ""
    if os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file) as f:
                checkpoint_content = f.read()
        except Exception:
            pass

    # Read latest 3 session summaries
    summaries = sorted(
        glob.glob(f"sessions/{agent_name}-*.md"),
        key=os.path.getmtime,
        reverse=True
    )[:3]

    summary_content = ""
    for s in summaries:
        try:
            with open(s) as f:
                summary_content += f"\n---\n{f.read()}\n"
        except Exception:
            pass

    # Read current task
    task_content = ""
    task_file = f"tasks/{agent_name}.md"
    if os.path.exists(task_file):
        try:
            with open(task_file) as f:
                task_content = f.read()
        except Exception:
            pass

    context_parts = []
    if checkpoint_content:
        context_parts.append(f"## Recent Checkpoint\n\n{checkpoint_content}")
    if task_content:
        context_parts.append(f"## Your Current Task\n\n{task_content}")
    if summary_content:
        context_parts.append(f"## Recent Session History\n\n{summary_content}")

    if context_parts:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": "\n\n".join(context_parts)
            }
        }
        json.dump(output, sys.stdout)

    sys.exit(0)

if __name__ == "__main__":
    main()
