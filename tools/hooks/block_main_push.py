#!/usr/bin/env python3
"""PreToolUse hook: Block agents from pushing to or checking out main branch."""
import json
import sys
import re

def main():
    hook_input = json.load(sys.stdin)
    command = hook_input.get("tool_input", {}).get("command", "")

    if re.search(r'git\s+(push|checkout|merge)\s+.*main', command):
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": "Agents cannot modify main branch. Commit to your worktree branch."
            }
        }
        json.dump(output, sys.stdout)

    sys.exit(0)

if __name__ == "__main__":
    main()
