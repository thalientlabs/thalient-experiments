#!/usr/bin/env python3
"""PostToolUse hook: Warn if Modal training launched without experiment manifest."""
import json
import sys
import glob

def main():
    hook_input = json.load(sys.stdin)
    command = hook_input.get("tool_input", {}).get("command", "")

    if "modal run" not in command:
        sys.exit(0)

    manifests = glob.glob("results/*-manifest.json")
    recent = []
    for m in manifests:
        try:
            with open(m) as f:
                content = f.read()
                if '"running"' in content:
                    recent.append(m)
        except Exception:
            pass

    if not recent:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": (
                    "WARNING: You just launched a Modal training run but no experiment "
                    "manifest exists in results/ with status 'running'. Run "
                    "`python tools/manifest.py create {experiment}` NOW to ensure "
                    "this experiment is reproducible. Record the git commit, config, "
                    "dataset hash, and Modal image ID."
                )
            }
        }
        json.dump(output, sys.stdout)

    sys.exit(0)

if __name__ == "__main__":
    main()
