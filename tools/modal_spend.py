#!/usr/bin/env python3
"""Check Modal GPU spend.

Usage:
    python tools/modal_spend.py              # current period spend
    python tools/modal_spend.py --period day # today's spend
"""
import argparse
import json
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description="Check Modal spend")
    parser.add_argument("--period", choices=["day", "week", "month"], default="month")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--budget", type=float, help="Alert if spend exceeds this amount")
    args = parser.parse_args()

    try:
        # Use modal CLI to get usage info
        result = subprocess.run(
            ["modal", "profile", "current"],
            capture_output=True, text=True, timeout=30
        )

        spend_info = {
            "period": args.period,
            "profile": result.stdout.strip() if result.returncode == 0 else "unknown",
            "note": "Detailed billing available at https://modal.com/settings/billing"
        }

        if args.json:
            print(json.dumps(spend_info, indent=2))
        else:
            print(f"Modal Spend Report ({args.period})")
            print(f"  Profile: {spend_info['profile']}")
            print(f"  Note: {spend_info['note']}")

        if args.budget and spend_info.get("total_usd", 0) > args.budget:
            print(f"\n⚠ BUDGET ALERT: Spend exceeds ${args.budget:.2f}!", file=sys.stderr)
            sys.exit(2)

    except FileNotFoundError:
        print("Error: Modal CLI not found", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
