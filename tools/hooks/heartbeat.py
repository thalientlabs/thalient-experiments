#!/usr/bin/env python3
"""PostToolUse hook: Update agent heartbeat after every tool use."""
import json
import sys
import os
from datetime import datetime, timezone

def main():
    hook_input = json.load(sys.stdin)

    agent_name = os.environ.get("AGENT_NAME", "unknown")
    status_dir = "status"
    os.makedirs(status_dir, exist_ok=True)
    status_file = os.path.join(status_dir, f"{agent_name}.json")

    # Read existing status or create new
    try:
        with open(status_file) as f:
            status = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        status = {"agent": agent_name, "status": "running"}

    status["last_heartbeat"] = datetime.now(timezone.utc).isoformat()
    status["tool_count"] = status.get("tool_count", 0) + 1

    with open(status_file, "w") as f:
        json.dump(status, f, indent=2)

    sys.exit(0)

if __name__ == "__main__":
    main()
