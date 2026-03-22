#!/usr/bin/env python3
"""PostToolUse hook: No-op. Heartbeats tracked by the orchestrator streaming task."""
import json
import sys
json.load(sys.stdin)  # consume stdin
sys.exit(0)
