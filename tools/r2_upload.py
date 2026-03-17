#!/usr/bin/env python3
"""Upload files/directories to Cloudflare R2.

Usage:
    python tools/r2_upload.py local_file.pt checkpoints/experiment-001/
    python tools/r2_upload.py ./results/ results/experiment-001/ --recursive
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


def upload_file(client, bucket, local_path, remote_key):
    file_size = os.path.getsize(local_path)
    print(f"  Uploading {local_path} -> r2://{bucket}/{remote_key} ({file_size / 1024 / 1024:.1f} MB)")
    client.upload_file(local_path, bucket, remote_key)


def main():
    parser = argparse.ArgumentParser(description="Upload to Cloudflare R2")
    parser.add_argument("source", help="Local file or directory")
    parser.add_argument("destination", help="R2 key prefix")
    parser.add_argument("--recursive", "-r", action="store_true", help="Upload directory recursively")
    parser.add_argument("--bucket", default=os.environ.get("R2_BUCKET_NAME", "thalient-research"))
    args = parser.parse_args()

    client = get_r2_client()

    if os.path.isfile(args.source):
        remote_key = args.destination
        if args.destination.endswith("/"):
            remote_key = args.destination + os.path.basename(args.source)
        upload_file(client, args.bucket, args.source, remote_key)
        print(f"✓ Uploaded to r2://{args.bucket}/{remote_key}")

    elif os.path.isdir(args.source) and args.recursive:
        count = 0
        for root, dirs, files in os.walk(args.source):
            for fname in files:
                local_path = os.path.join(root, fname)
                relative = os.path.relpath(local_path, args.source)
                remote_key = os.path.join(args.destination, relative).replace("\\", "/")
                upload_file(client, args.bucket, local_path, remote_key)
                count += 1
        print(f"✓ Uploaded {count} files to r2://{args.bucket}/{args.destination}")

    else:
        print("Error: Source is a directory — use --recursive flag", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
