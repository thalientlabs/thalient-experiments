#!/usr/bin/env python3
"""Check Modal job status.

Usage:
    python tools/modal_status.py                  # list all recent apps
    python tools/modal_status.py --app sweep-lr   # status of specific app
"""
import argparse
import json
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description="Check Modal job status")
    parser.add_argument("--app", help="Specific app name to check")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    try:
        if args.app:
            result = subprocess.run(
                ["modal", "app", "list", "--json"],
                capture_output=True, text=True, timeout=30
            )
        else:
            result = subprocess.run(
                ["modal", "app", "list", "--json"],
                capture_output=True, text=True, timeout=30
            )

        if result.returncode != 0:
            print(f"Error querying Modal: {result.stderr}", file=sys.stderr)
            sys.exit(1)

        apps = json.loads(result.stdout) if result.stdout.strip() else []

        if args.app:
            apps = [a for a in apps if args.app in a.get("name", "")]

        if args.json:
            print(json.dumps(apps, indent=2))
        else:
            if not apps:
                print("No Modal apps found.")
                return
            print(f"{'Name':<30} {'Status':<15} {'Created':<25}")
            print("-" * 70)
            for app in apps:
                print(f"{app.get('name', 'unknown'):<30} {app.get('state', 'unknown'):<15} {app.get('created_at', ''):<25}")

    except subprocess.TimeoutExpired:
        print("Error: Modal CLI timed out", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: Modal CLI not found. Install with: pip install modal", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
