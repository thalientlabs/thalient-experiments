#!/usr/bin/env python3
"""Check R2 bucket storage usage and estimated cost.

Usage:
    python tools/r2_usage.py
    python tools/r2_usage.py --prefix checkpoints/
"""
import argparse
import json
import os
import sys

import boto3
from botocore.config import Config

R2_COST_PER_GB_MONTH = 0.015  # $0.015/GB/month


def get_r2_client():
    return boto3.client(
        "s3",
        endpoint_url=os.environ["R2_ENDPOINT_URL"],
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def main():
    parser = argparse.ArgumentParser(description="Check R2 storage usage")
    parser.add_argument("--prefix", default="", help="Filter by key prefix")
    parser.add_argument("--bucket", default=os.environ.get("R2_BUCKET_NAME", "thalient-research"))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--budget-gb", type=float, help="Alert if usage exceeds this many GB")
    args = parser.parse_args()

    client = get_r2_client()
    paginator = client.get_paginator("list_objects_v2")

    total_size = 0
    total_objects = 0
    prefix_sizes = {}

    for page in paginator.paginate(Bucket=args.bucket, Prefix=args.prefix):
        for obj in page.get("Contents", []):
            size = obj["Size"]
            total_size += size
            total_objects += 1

            # Track top-level prefix sizes
            key = obj["Key"]
            top_prefix = key.split("/")[0] if "/" in key else "(root)"
            prefix_sizes[top_prefix] = prefix_sizes.get(top_prefix, 0) + size

    total_gb = total_size / (1024 ** 3)
    monthly_cost = total_gb * R2_COST_PER_GB_MONTH

    result = {
        "bucket": args.bucket,
        "prefix": args.prefix or "(all)",
        "total_objects": total_objects,
        "total_bytes": total_size,
        "total_gb": round(total_gb, 3),
        "estimated_monthly_cost_usd": round(monthly_cost, 2),
        "breakdown": {k: round(v / (1024**3), 3) for k, v in sorted(prefix_sizes.items(), key=lambda x: -x[1])},
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"R2 Storage: {args.bucket}")
        print(f"  Objects: {total_objects:,}")
        print(f"  Total: {total_gb:.3f} GB")
        print(f"  Est. monthly cost: ${monthly_cost:.2f}")
        if prefix_sizes:
            print(f"\n  Breakdown:")
            for prefix, size_gb in sorted(prefix_sizes.items(), key=lambda x: -x[1]):
                print(f"    {prefix}/: {size_gb / (1024**3):.3f} GB")

    if args.budget_gb and total_gb > args.budget_gb:
        print(f"\n⚠ STORAGE ALERT: {total_gb:.1f} GB exceeds budget of {args.budget_gb:.1f} GB!", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
