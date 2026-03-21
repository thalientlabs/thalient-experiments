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
    repo_root = os.environ.get("REPO_PATH", "/home/researcher/research-repo")

    # Read latest checkpoint if it exists (agent-local, relative to cwd)
    checkpoint_file = os.path.join(".agent", "checkpoints", f"{agent_name}-latest.md")
    checkpoint_content = ""
    if os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file) as f:
                checkpoint_content = f.read()
        except Exception:
            pass

    # Read latest 3 session summaries (agent-local, relative to cwd)
    summaries = sorted(
        glob.glob(os.path.join(".agent", "sessions", f"{agent_name}-*.md")),
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

    # Read current task (at repo root, since orchestrator writes them there)
    task_content = ""
    task_file = os.path.join(repo_root, "tasks", f"{agent_name}.md")
    if os.path.exists(task_file):
        try:
            with open(task_file) as f:
                task_content = f.read()
        except Exception:
            pass

    # Read LESSONS_LEARNED.md (cwd-relative, in topic dir)
    lessons_content = ""
    if os.path.exists("LESSONS_LEARNED.md"):
        try:
            with open("LESSONS_LEARNED.md") as f:
                content = f.read()
                # Only inject if there's actual content beyond the template
                if "##" in content and len(content) > 200:
                    lessons_content = content[:2000]
        except Exception:
            pass

    # Read DECISIONS.md (cwd-relative, in topic dir)
    decisions_content = ""
    if os.path.exists("DECISIONS.md"):
        try:
            with open("DECISIONS.md") as f:
                content = f.read()
                if "##" in content and len(content) > 200:
                    decisions_content = content[:2000]
        except Exception:
            pass

    context_parts = []
    if lessons_content:
        context_parts.append(f"## Lessons Learned (from past experiments)\n\n{lessons_content}")
    if decisions_content:
        context_parts.append(f"## Decision Log\n\n{decisions_content}")
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
