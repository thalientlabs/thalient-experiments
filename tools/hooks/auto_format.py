#!/usr/bin/env python3
"""PostToolUse hook: Auto-format Python files after edits."""
import json
import sys
import os
import subprocess

def main():
    hook_input = json.load(sys.stdin)
    tool_input = hook_input.get("tool_input", {})

    file_path = tool_input.get("file_path", "") or tool_input.get("filePath", "")
    if not file_path or not file_path.endswith(".py"):
        sys.exit(0)

    # Try to run ruff format if available
    try:
        subprocess.run(
            ["ruff", "format", file_path],
            capture_output=True, timeout=10
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass  # ruff not available, skip formatting

    sys.exit(0)

if __name__ == "__main__":
    main()
