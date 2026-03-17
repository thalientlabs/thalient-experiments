#!/usr/bin/env python3
"""Notification hook: Forward agent notifications to the orchestrator dashboard."""
import json
import sys
import os
import urllib.request
import urllib.error

def main():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, Exception):
        hook_input = {}

    agent_name = os.environ.get("AGENT_NAME", "unknown")
    orchestrator_url = os.environ.get("ORCHESTRATOR_URL", "http://localhost:8000")

    notification = {
        "agent": agent_name,
        "message": hook_input.get("message", ""),
        "level": hook_input.get("level", "info"),
    }

    try:
        data = json.dumps(notification).encode()
        req = urllib.request.Request(
            f"{orchestrator_url}/internal/notification",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(req, timeout=5)
    except (urllib.error.URLError, Exception):
        pass  # Don't fail the agent if notification fails

    sys.exit(0)

if __name__ == "__main__":
    main()
