#!/usr/bin/env python3
"""PostToolUse hook: Capture all bash commands and outputs for audit trail."""
import json
import sys
import os
from datetime import datetime, timezone

def main():
    hook_input = json.load(sys.stdin)
    tool_input = hook_input.get("tool_input", {})
    tool_result = hook_input.get("tool_result", {})

    agent_name = os.environ.get("AGENT_NAME", "unknown")
    log_dir = os.path.join(".agent", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{agent_name}-commands.jsonl")

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": tool_input.get("command", ""),
        "exit_code": tool_result.get("exitCode"),
        "stdout_preview": str(tool_result.get("stdout", ""))[:500],
        "stderr_preview": str(tool_result.get("stderr", ""))[:500],
    }

    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")

    sys.exit(0)

if __name__ == "__main__":
    main()
