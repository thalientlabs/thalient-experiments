#!/usr/bin/env python3
"""PreToolUse hook: Rate limit Modal training launches to prevent cost explosion."""
import json
import sys
import os

def main():
    hook_input = json.load(sys.stdin)
    command = hook_input.get("tool_input", {}).get("command", "")

    if "modal run" not in command:
        sys.exit(0)

    session_id = os.environ.get("CLAUDE_SESSION_ID", "default")
    count_file = f"/tmp/modal-launch-count-{session_id}"

    try:
        with open(count_file) as f:
            count = int(f.read().strip())
    except (FileNotFoundError, ValueError):
        count = 0

    count += 1

    with open(count_file, "w") as f:
        f.write(str(count))

    if count > 10:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": "Modal launch limit reached (10 per session). Write a proposal to request more."
            }
        }
        json.dump(output, sys.stdout)

    sys.exit(0)

if __name__ == "__main__":
    main()
