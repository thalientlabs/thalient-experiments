#!/usr/bin/env python3
"""Experiment manifest management for reproducibility.

Usage:
    python tools/manifest.py create sweep-lr-001
    python tools/manifest.py complete sweep-lr-001
    python tools/manifest.py verify sweep-lr-001
    python tools/manifest.py list
    python tools/manifest.py reproduce sweep-lr-001
"""
import argparse
import glob
import json
import os
import subprocess
import sys
from datetime import datetime, timezone


def git_output(cmd):
    """Run a git command and return stdout."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip()
    except Exception:
        return ""


def pip_freeze():
    """Get pip freeze output."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            capture_output=True, text=True, timeout=30
        )
        return result.stdout.strip()
    except Exception:
        return ""


def create_manifest(experiment):
    """Create a new experiment manifest."""
    os.makedirs("results", exist_ok=True)
    filepath = f"results/{experiment}-manifest.json"

    if os.path.exists(filepath):
        print(f"Warning: Manifest already exists: {filepath}")
        with open(filepath) as f:
            existing = json.load(f)
        if existing.get("status") == "running":
            print("Experiment is currently running. Use 'complete' when done.")
            return

    manifest = {
        "experiment": experiment,
        "agent": os.environ.get("AGENT_NAME", "unknown"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_output(["git", "rev-parse", "HEAD"]),
        "git_branch": git_output(["git", "branch", "--show-current"]),
        "git_dirty": bool(git_output(["git", "status", "--porcelain"])),
        "hypothesis": "",
        "config": {
            "model": "",
            "learning_rate": None,
            "batch_size": None,
            "epochs": None,
            "scheduler": "",
            "warmup_steps": None,
            "weight_decay": None,
            "seed": 42,
            "dataset": "",
            "dataset_sha256": ""
        },
        "modal": {
            "app_name": "",
            "gpu": "A100-80GB",
            "image_hash": ""
        },
        "python_env": pip_freeze(),
        "status": "running"
    }

    with open(filepath, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Created manifest: {filepath}")
    print(f"  Git commit: {manifest['git_commit']}")
    print(f"  Branch: {manifest['git_branch']}")
    print(f"  Fill in config, hypothesis, and modal fields before launching.")


def complete_manifest(experiment):
    """Mark an experiment as completed and fill in results."""
    filepath = f"results/{experiment}-manifest.json"

    if not os.path.exists(filepath):
        print(f"Error: No manifest found: {filepath}", file=sys.stderr)
        sys.exit(1)

    with open(filepath) as f:
        manifest = json.load(f)

    manifest["status"] = "completed"
    manifest["completed_at"] = datetime.now(timezone.utc).isoformat()
    manifest["results"] = manifest.get("results", {
        "final_loss": None,
        "eval_accuracy": None,
        "training_time_hours": None,
        "total_cost_usd": None
    })
    manifest["artifacts"] = manifest.get("artifacts", {
        "checkpoint": "",
        "logs": "",
        "wandb_run": ""
    })

    with open(filepath, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Marked as completed: {filepath}")
    print(f"  Fill in results and artifacts fields.")


def verify_manifest(experiment):
    """Verify an experiment manifest is complete and reproducible."""
    filepath = f"results/{experiment}-manifest.json"

    if not os.path.exists(filepath):
        print(f"FAIL: No manifest found: {filepath}", file=sys.stderr)
        sys.exit(1)

    with open(filepath) as f:
        manifest = json.load(f)

    checks = []

    # Check git commit exists
    git_commit = manifest.get("git_commit", "")
    if git_commit:
        result = subprocess.run(
            ["git", "cat-file", "-t", git_commit],
            capture_output=True, text=True
        )
        checks.append(("git_commit exists", result.returncode == 0))
    else:
        checks.append(("git_commit exists", False))

    # Check required fields
    checks.append(("has hypothesis", bool(manifest.get("hypothesis"))))
    checks.append(("has config", bool(manifest.get("config", {}).get("model"))))
    checks.append(("has dataset ref", bool(manifest.get("config", {}).get("dataset"))))
    checks.append(("has modal app_name", bool(manifest.get("modal", {}).get("app_name"))))
    checks.append(("has python_env", bool(manifest.get("python_env"))))

    if manifest.get("status") == "completed":
        checks.append(("has results", bool(manifest.get("results", {}).get("final_loss") is not None)))
        checks.append(("has artifacts", bool(manifest.get("artifacts", {}).get("checkpoint"))))

    # Print results
    all_passed = True
    for name, passed in checks:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_passed = False
        print(f"  [{status}] {name}")

    if all_passed:
        print(f"\n✓ Manifest verified: {experiment}")
    else:
        print(f"\n✗ Manifest incomplete: {experiment}", file=sys.stderr)
        sys.exit(1)


def list_manifests():
    """List all experiment manifests."""
    manifests = glob.glob("results/*-manifest.json")

    if not manifests:
        print("No experiment manifests found.")
        return

    print(f"{'Experiment':<30} {'Status':<12} {'Date':<25} {'Agent':<15}")
    print("-" * 82)

    for filepath in sorted(manifests):
        try:
            with open(filepath) as f:
                m = json.load(f)
            name = m.get("experiment", os.path.basename(filepath))
            status = m.get("status", "unknown")
            date = m.get("timestamp", "")[:19]
            agent = m.get("agent", "unknown")

            # Add key metrics if completed
            metrics = ""
            if status == "completed" and m.get("results"):
                loss = m["results"].get("final_loss")
                acc = m["results"].get("eval_accuracy")
                if loss is not None:
                    metrics += f" loss={loss:.4f}"
                if acc is not None:
                    metrics += f" acc={acc:.3f}"

            print(f"{name:<30} {status:<12} {date:<25} {agent:<15}{metrics}")
        except Exception as e:
            print(f"{filepath}: Error reading - {e}")


def reproduce_manifest(experiment):
    """Output commands to reproduce an experiment."""
    filepath = f"results/{experiment}-manifest.json"

    if not os.path.exists(filepath):
        print(f"Error: No manifest found: {filepath}", file=sys.stderr)
        sys.exit(1)

    with open(filepath) as f:
        manifest = json.load(f)

    print(f"# Reproduce: {experiment}")
    print(f"# Original date: {manifest.get('timestamp', 'unknown')}")
    print(f"# Original agent: {manifest.get('agent', 'unknown')}")
    print()

    git_commit = manifest.get("git_commit", "")
    if git_commit:
        print(f"# Step 1: Checkout exact code state")
        print(f"git checkout {git_commit}")
        print()

    if manifest.get("python_env"):
        print(f"# Step 2: Install exact Python environment")
        print(f"pip install -r <(cat << 'PIPFREEZE'")
        print(manifest["python_env"])
        print("PIPFREEZE")
        print(f")")
        print()

    config = manifest.get("config", {})
    modal_config = manifest.get("modal", {})

    print(f"# Step 3: Run the experiment")
    print(f"# Config: {json.dumps(config, indent=2)}")
    if modal_config.get("app_name"):
        print(f"modal run experiments/{experiment}.py \\")
        print(f"  --app-name {modal_config['app_name']}")
    print()

    dataset = config.get("dataset", "")
    if dataset:
        print(f"# Dataset: {dataset}")
        if config.get("dataset_sha256"):
            print(f"# SHA256: {config['dataset_sha256']}")


def main():
    parser = argparse.ArgumentParser(description="Experiment manifest management")
    parser.add_argument("action", choices=["create", "complete", "verify", "list", "reproduce"])
    parser.add_argument("experiment", nargs="?", help="Experiment name")
    args = parser.parse_args()

    if args.action == "list":
        list_manifests()
    elif not args.experiment:
        print(f"Error: experiment name required for '{args.action}'", file=sys.stderr)
        sys.exit(1)
    elif args.action == "create":
        create_manifest(args.experiment)
    elif args.action == "complete":
        complete_manifest(args.experiment)
    elif args.action == "verify":
        verify_manifest(args.experiment)
    elif args.action == "reproduce":
        reproduce_manifest(args.experiment)


if __name__ == "__main__":
    main()
