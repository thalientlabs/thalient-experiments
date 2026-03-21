#!/usr/bin/env python3
"""PreToolUse hook: Ensure agents only write to their designated directories."""
import json
import sys
import os

ALLOWED_PREFIXES = [
    "Topics/", "Experiments/", ".agent/", "proposals/",
    "RESEARCH_LOG.md", "tools/", "Readme.md",
]

def main():
    hook_input = json.load(sys.stdin)
    tool_input = hook_input.get("tool_input", {})

    file_path = tool_input.get("file_path", "") or tool_input.get("filePath", "")
    if not file_path:
        sys.exit(0)

    # Normalize path - make relative to repo root
    repo_root = os.environ.get("REPO_ROOT", "/home/researcher/research-repo")
    if file_path.startswith(repo_root):
        file_path = file_path[len(repo_root):].lstrip("/")

    # Also handle paths relative to the topic cwd
    # If the path doesn't start with a known repo-level prefix, it's relative to cwd
    # which is Topics/{topic}/, so those are fine as long as they're in allowed areas

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
