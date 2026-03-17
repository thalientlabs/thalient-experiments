#!/usr/bin/env python3
"""Download files from Cloudflare R2.

Usage:
    python tools/r2_download.py checkpoints/model.pt ./local_model.pt
    python tools/r2_download.py results/experiment/ ./results/ --recursive
"""
import argparse
import os
import sys

import boto3
from botocore.config import Config


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
    parser = argparse.ArgumentParser(description="Download from Cloudflare R2")
    parser.add_argument("source", help="R2 key or prefix")
    parser.add_argument("destination", help="Local file or directory")
    parser.add_argument("--recursive", "-r", action="store_true", help="Download prefix recursively")
    parser.add_argument("--bucket", default=os.environ.get("R2_BUCKET_NAME", "thalient-research"))
    args = parser.parse_args()

    client = get_r2_client()

    if args.recursive:
        os.makedirs(args.destination, exist_ok=True)
        paginator = client.get_paginator("list_objects_v2")
        count = 0
        for page in paginator.paginate(Bucket=args.bucket, Prefix=args.source):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                relative = key[len(args.source):].lstrip("/")
                if not relative:
                    continue
                local_path = os.path.join(args.destination, relative)
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                print(f"  Downloading r2://{args.bucket}/{key} -> {local_path}")
                client.download_file(args.bucket, key, local_path)
                count += 1
        print(f"✓ Downloaded {count} files to {args.destination}")
    else:
        dest_dir = os.path.dirname(args.destination)
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)
        print(f"  Downloading r2://{args.bucket}/{args.source} -> {args.destination}")
        client.download_file(args.bucket, args.source, args.destination)
        print(f"✓ Downloaded to {args.destination}")


if __name__ == "__main__":
    main()
