#!/usr/bin/env python3
"""Launch a Modal training job with experiment tracking.

Usage:
    python tools/modal_run.py --app-name sweep-lr-001 --gpu A100-80GB \
        --script experiments/sweep_lr.py --config '{"lr": 3e-4, "epochs": 10}'
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone


def main():
    parser = argparse.ArgumentParser(description="Launch a Modal training job")
    parser.add_argument("--app-name", required=True, help="Modal app name for this run")
    parser.add_argument("--gpu", default="A100-80GB", help="GPU type (default: A100-80GB)")
    parser.add_argument("--script", required=True, help="Path to the training script")
    parser.add_argument("--config", default="{}", help="JSON config to pass to the script")
    parser.add_argument("--timeout", type=int, default=14400, help="Timeout in seconds (default: 4h)")
    parser.add_argument("--dry-run", action="store_true", help="Print command without executing")
    args = parser.parse_args()

    config = json.loads(args.config)

    # Build modal run command
    cmd = [
        "modal", "run", args.script,
        "--app-name", args.app_name,
    ]

    # Pass config as environment variables
    env = os.environ.copy()
    env["EXPERIMENT_CONFIG"] = json.dumps(config)
    env["EXPERIMENT_APP_NAME"] = args.app_name
    env["EXPERIMENT_GPU"] = args.gpu

    if args.dry_run:
        print(f"[DRY RUN] Would execute: {' '.join(cmd)}")
        print(f"[DRY RUN] Config: {json.dumps(config, indent=2)}")
        return

    print(f"[{datetime.now(timezone.utc).isoformat()}] Launching Modal app: {args.app_name}")
    print(f"  GPU: {args.gpu}")
    print(f"  Script: {args.script}")
    print(f"  Config: {json.dumps(config)}")

    # Write launch record
    os.makedirs("logs", exist_ok=True)
    launch_record = {
        "app_name": args.app_name,
        "gpu": args.gpu,
        "script": args.script,
        "config": config,
        "launched_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(f"logs/modal-launch-{args.app_name}.json", "w") as f:
        json.dump(launch_record, f, indent=2)

    result = subprocess.run(cmd, env=env, timeout=args.timeout)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
