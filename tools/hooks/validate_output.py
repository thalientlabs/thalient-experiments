#!/usr/bin/env python3
"""Stop hook: Force a sub-agent validation pass on the agent's output.

On first fire (stop_hook_active=false), injects a prompt that makes Claude
spawn a validation sub-agent to review its work. On second fire
(stop_hook_active=true), exits cleanly to prevent infinite loops.
"""
import json
import sys


def main():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, Exception):
        hook_input = {}

    # Prevent infinite loop: if we already triggered validation, exit
    if hook_input.get("stop_hook_active"):
        sys.exit(0)

    last_message = hook_input.get("last_assistant_message", "")

    # Skip validation for very short responses (greetings, acknowledgments)
    if len(last_message) < 200:
        sys.exit(0)

    validation_prompt = """MANDATORY VALIDATION STEP â€” Before finishing, you MUST launch a sub-agent to validate your work.

Use the Agent tool with subagent_type="general-purpose" to spawn a validator with this prompt:

"You are a critical reviewer. The research agent just produced the following output. Your job is to:

1. CHECK COMPLETENESS â€” Did it actually do what was asked? Are there gaps, missing steps, or hand-waved sections?
2. CHECK REASONING â€” Are the claims supported? Are there logical errors or unsupported assumptions?
3. CHECK VALUE â€” Is this output actually useful, or is it generic/boilerplate that adds no real insight?
4. CHECK FOLLOW-THROUGH â€” Did it commit files, update Status.md, and leave the repo in a clean state?

If you find issues, list them concisely. If the work is solid, say so briefly.

Here is the output to validate:

---
""" + last_message[:3000] + """
---

Review this critically. Be specific about any problems."

After the validator responds, address any issues it raises before finishing."""

    output = {
        "hookSpecificOutput": {
            "hookEventName": "Stop",
            "additionalContext": validation_prompt,
        }
    }
    json.dump(output, sys.stdout)
    sys.exit(0)


if __name__ == "__main__":
    main()
