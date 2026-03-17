#!/usr/bin/env python3
"""Write a well-formatted proposal file.

Usage:
    python tools/propose.py "learning-rate-sweep" \
        --title "Switch to cosine scheduler" \
        --body "Based on sweep results, cosine outperforms step decay..." \
        --agent researcher-a
"""
import argparse
import os
import sys
from datetime import datetime, timezone


def main():
    parser = argparse.ArgumentParser(description="Create a proposal file")
    parser.add_argument("name", help="Proposal name (becomes filename)")
    parser.add_argument("--title", required=True, help="Proposal title")
    parser.add_argument("--body", required=True, help="Proposal body (markdown)")
    parser.add_argument("--agent", default=os.environ.get("AGENT_NAME", "unknown"))
    parser.add_argument("--alternatives", help="Alternative approaches considered")
    args = parser.parse_args()

    os.makedirs("proposals", exist_ok=True)

    timestamp = datetime.now(timezone.utc).isoformat()
    filename = f"proposals/{args.name}.md"

    content = f"""---
title: {args.title}
agent: {args.agent}
created: {timestamp}
status: pending
---

# {args.title}

**Agent:** {args.agent}
**Date:** {timestamp}

## Summary

{args.body}
"""

    if args.alternatives:
        content += f"""
## Alternatives Considered

{args.alternatives}
"""

    content += """
## Decision

_Awaiting PI review. Approve or reject from the dashboard._
"""

    with open(filename, "w") as f:
        f.write(content)

    print(f"Proposal written: {filename}")
    print(f"Waiting for approval...")


if __name__ == "__main__":
    main()
