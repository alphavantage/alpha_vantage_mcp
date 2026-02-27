import boto3
import os
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')


def lambda_handler(event, context):
    """
    Hourly compaction: merge all small .jsonl files from the previous hour
    into a single file, then delete the originals.
    """
    bucket = os.environ['S3_BUCKET']

    # Compact the previous hour
    now = datetime.now(timezone.utc)
    target = now - timedelta(hours=1)
    prefix = f"jsonl/{target.year}/{target.month:02d}/{target.day:02d}/{target.hour:02d}/"

    logger.info(f"Compacting {prefix} in {bucket}")

    # List all objects under the prefix
    keys = []
    paginator = s3_client.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get('Contents', []):
            keys.append(obj['Key'])

    if len(keys) <= 1:
        logger.info(f"Nothing to compact: {len(keys)} file(s)")
        return {'compacted': 0}

    # Download and concatenate all files
    lines = []
    for key in keys:
        resp = s3_client.get_object(Bucket=bucket, Key=key)
        body = resp['Body'].read().decode('utf-8').strip()
        if body:
            lines.append(body)

    merged = '\n'.join(lines)
    merged_key = f"{prefix}compacted.jsonl"

    # Write merged file
    s3_client.put_object(
        Bucket=bucket,
        Key=merged_key,
        Body=merged.encode('utf-8'),
        ContentType='application/jsonlines',
    )
    logger.info(f"Wrote {merged_key} ({len(lines)} sources, {len(merged)} bytes)")

    # Delete originals (except the merged file)
    for key in keys:
        if key != merged_key:
            s3_client.delete_object(Bucket=bucket, Key=key)

    logger.info(f"Deleted {len(keys)} original files")

    return {'compacted': len(keys), 'merged_key': merged_key}
