#!/usr/bin/env python3
"""Stop hook: Call the Arbiter to validate the agent's output before finishing.

On first fire (stop_hook_active=false), injects a prompt that makes Claude
spawn the Arbiter agent to review its work. On second fire
(stop_hook_active=true), exits cleanly to prevent infinite loops.
"""
import json
import sys
import os


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

    # Build context about what the agent was doing
    agent_name = os.environ.get("AGENT_NAME", "unknown")
    cwd = hook_input.get("cwd", os.getcwd())

    # Try to read current Status.md and Readme.md for context
    status_context = ""
    readme_context = ""
    lessons_context = ""
    decisions_context = ""

    for status_path in ["Status.md", "Experiments/*/Status.md"]:
        import glob
        for f in glob.glob(os.path.join(cwd, status_path)):
            try:
                with open(f) as fh:
                    status_context += fh.read()[:1000] + "\n---\n"
            except Exception:
                pass

    for name in ["Readme.md", "LESSONS_LEARNED.md", "DECISIONS.md"]:
        path = os.path.join(cwd, name)
        if os.path.exists(path):
            try:
                with open(path) as fh:
                    content = fh.read()[:1000]
                    if name == "Readme.md":
                        readme_context = content
                    elif name == "LESSONS_LEARNED.md":
                        lessons_context = content
                    elif name == "DECISIONS.md":
                        decisions_context = content
            except Exception:
                pass

    context_block = f"""## Agent Context
Agent: {agent_name}
Working directory: {cwd}

## Current Readme
{readme_context[:800] if readme_context else '(empty)'}

## Experiment Status
{status_context[:800] if status_context else '(no experiments)'}

## Lessons Learned
{lessons_context[:500] if lessons_context else '(none yet)'}

## Recent Decisions
{decisions_context[:500] if decisions_context else '(none yet)'}

## Agent's Last Output
{last_message[:3000]}"""

    validation_prompt = f"""MANDATORY REVIEW â€” Before finishing, you MUST call the Arbiter.

Use the Agent tool with subagent_type="arbiter" and this prompt:

"You are being called to review the work of agent '{agent_name}'. Here is the full context:

{context_block}

---

Evaluate this against your mandate: Is it novel? Is it cost-efficient? Is the methodology sound? Give your verdict: APPROVE, REDIRECT, REJECT, or ESCALATE."

After the Arbiter responds:
- If APPROVE: proceed to finish. Update LESSONS_LEARNED.md and DECISIONS.md.
- If REDIRECT: address the Arbiter's feedback before finishing.
- If REJECT: stop what you're doing and explain the situation to the PI.
- If ESCALATE: notify the PI via `python tools/notify.py "Arbiter escalation: [summary]"`.

Also update LESSONS_LEARNED.md and DECISIONS.md before you fully finish."""

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
