#!/usr/bin/env python3
"""PreToolUse hook: Ensure agents only write to their designated directories."""
import json
import sys
import os

ALLOWED_PREFIXES = [
    "experiments/", "results/", "proposals/", "status/",
    "tasks/", "tools/", "monitoring/", "checkpoints/",
    "sessions/", "logs/", "RESEARCH_LOG.md",
]

def main():
    hook_input = json.load(sys.stdin)
    tool_input = hook_input.get("tool_input", {})

    file_path = tool_input.get("file_path", "") or tool_input.get("filePath", "")
    if not file_path:
        sys.exit(0)

    # Normalize path - make relative to repo root
    repo_root = os.environ.get("REPO_ROOT", "/home/daytona/research-repo")
    if file_path.startswith(repo_root):
        file_path = file_path[len(repo_root):].lstrip("/")

    # Check if file is in an allowed location
    allowed = any(file_path.startswith(prefix) for prefix in ALLOWED_PREFIXES)

    if not allowed:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"Write to '{file_path}' blocked. Agents may only write to: {', '.join(ALLOWED_PREFIXES)}"
            }
        }
        json.dump(output, sys.stdout)

    sys.exit(0)

if __name__ == "__main__":
    main()
