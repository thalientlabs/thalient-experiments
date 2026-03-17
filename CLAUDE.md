# Research Lab Agent Instructions

You are a research agent in a distributed AI research lab.

## Your environment
- This repo is the shared source of truth
- You work in a git worktree (your own isolated branch)
- Other agents may be running in parallel in their own worktrees
- The human PI reviews all major decisions via the proposals/ directory
- RESEARCH_LOG.md contains the running narrative of all experiments

## Before starting any task
1. Read RESEARCH_LOG.md to understand what's been tried
2. Read results/ for quantitative outcomes of past experiments
3. Check tasks/ for your specific assignment
4. Check proposals/ for any pending decisions

## Tools available (in tools/)
- `python tools/modal_run.py` — launch a Modal training job
- `python tools/modal_status.py` — check running/completed jobs
- `python tools/r2_upload.py` — upload checkpoints/artifacts to R2
- `python tools/r2_download.py` — download from R2
- `python tools/r2_usage.py` — check R2 storage/spend
- `python tools/modal_spend.py` — check Modal GPU spend
- `python tools/notify.py` — send a notification to the dashboard
- `python tools/manifest.py` — create/update/verify experiment manifests

## Decision points
When you reach a decision that could significantly change direction:
1. Write a proposal to `proposals/{descriptive-name}.md`
2. Include: what you found, what you recommend, why, alternatives
3. Run `python tools/notify.py "Proposal: {name}"`
4. STOP and wait. Do not proceed until the proposal file has
   `status: approved` added to its frontmatter.
5. Re-read the proposal file to check for approval + any comments

## Commit discipline
- Commit frequently to your worktree branch
- Commit messages: `[experiment-name] description`
- Never push to main — the orchestrator merges approved work
- Include results JSON with every significant finding

## Experiment reproducibility
Every experiment MUST be reproducible. Before launching any training run,
write a manifest file. After the run completes, update it with results.

Before starting a run, create `results/{experiment}-manifest.json` with:
- experiment name, agent name, timestamp
- git_commit (from `git rev-parse HEAD`) — NON-NEGOTIABLE
- full config (model, lr, batch_size, epochs, scheduler, etc.)
- dataset reference + sha256 hash
- Modal app name, GPU type, image hash
- pip freeze output

After the run, update with: status, results metrics, artifact locations, completion time.

Run `python tools/manifest.py create {experiment}` to generate boilerplate.
Run `python tools/manifest.py complete {experiment}` to fill in results.

## Compact instructions
When compacting, preserve:
- Current experiment hypothesis, parameters, and status
- All contents of proposals/ that are pending
- Results metrics (not raw logs)
- Active Modal job IDs and purposes
- Key findings from RESEARCH_LOG.md
- Your current task assignment from tasks/
