#!/usr/bin/env python3
"""Send a notification to the orchestrator dashboard.

Usage:
    python tools/notify.py "Proposal: learning-rate-sweep"
    python tools/notify.py --level warning "Budget threshold exceeded"
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error


def main():
    parser = argparse.ArgumentParser(description="Send notification to dashboard")
    parser.add_argument("message", help="Notification message")
    parser.add_argument("--level", choices=["info", "warning", "error"], default="info")
    parser.add_argument("--agent", default=os.environ.get("AGENT_NAME", "unknown"))
    args = parser.parse_args()

    orchestrator_url = os.environ.get("ORCHESTRATOR_URL", "http://localhost:8000")

    payload = {
        "agent": args.agent,
        "message": args.message,
        "level": args.level,
    }

    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{orchestrator_url}/internal/notification",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req, timeout=10)
        print(f"Notification sent: {args.message}")
    except urllib.error.URLError as e:
        print(f"Warning: Could not reach orchestrator: {e}", file=sys.stderr)
        # Don't fail — notifications are best-effort
    except Exception as e:
        print(f"Warning: Notification failed: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
