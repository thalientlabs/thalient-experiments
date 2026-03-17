#!/usr/bin/env python3
"""Poll a proposal file for approval status.

Usage:
    python tools/check_proposal.py learning-rate-sweep
    python tools/check_proposal.py learning-rate-sweep --wait --interval 10
"""
import argparse
import os
import sys
import time


def check_status(filepath):
    """Read proposal file and extract status from frontmatter."""
    if not os.path.exists(filepath):
        return None

    with open(filepath) as f:
        content = f.read()

    # Parse frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = parts[1]
            for line in frontmatter.strip().split("\n"):
                if line.startswith("status:"):
                    return line.split(":", 1)[1].strip()

    return "pending"


def main():
    parser = argparse.ArgumentParser(description="Check proposal approval status")
    parser.add_argument("name", help="Proposal name")
    parser.add_argument("--wait", action="store_true", help="Wait until approved/rejected")
    parser.add_argument("--interval", type=int, default=10, help="Poll interval in seconds")
    parser.add_argument("--timeout", type=int, default=3600, help="Max wait time in seconds")
    args = parser.parse_args()

    filepath = f"proposals/{args.name}.md"

    if not os.path.exists(filepath):
        print(f"Error: Proposal not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    if not args.wait:
        status = check_status(filepath)
        print(f"Proposal '{args.name}': {status}")
        if status == "approved":
            sys.exit(0)
        elif status == "rejected":
            sys.exit(2)
        else:
            sys.exit(1)  # still pending

    # Polling mode
    start = time.time()
    while time.time() - start < args.timeout:
        status = check_status(filepath)
        if status == "approved":
            print(f"Proposal '{args.name}' APPROVED")

            # Read any comments
            with open(filepath) as f:
                content = f.read()
            if "## Comments" in content or "## PI Comments" in content:
                idx = content.find("## Comments") if "## Comments" in content else content.find("## PI Comments")
                print(f"\nPI feedback:\n{content[idx:]}")

            sys.exit(0)
        elif status == "rejected":
            print(f"Proposal '{args.name}' REJECTED")
            with open(filepath) as f:
                content = f.read()
            if "## Comments" in content or "## PI Comments" in content:
                idx = content.find("## Comments") if "## Comments" in content else content.find("## PI Comments")
                print(f"\nPI feedback:\n{content[idx:]}")
            sys.exit(2)

        print(f"  Status: {status} (waiting...)")
        time.sleep(args.interval)

    print(f"Timeout: proposal still pending after {args.timeout}s", file=sys.stderr)
    sys.exit(3)


if __name__ == "__main__":
    main()
