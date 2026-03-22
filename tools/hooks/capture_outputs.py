#!/usr/bin/env python3
"""PostToolUse hook: No-op. Command logging removed â€” status tracked in Status.md."""
import json
import sys
json.load(sys.stdin)  # consume stdin
sys.exit(0)
