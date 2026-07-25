import boto3
import os
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')

DEFAULT_LOOKBACK_HOURS = 24


def compact_hour(bucket, prefix, s3_client):
    """
    Merge all small .jsonl files under an hour prefix into compacted.jsonl,
    then delete the originals. A no-op if the prefix is empty or already
    consists solely of compacted.jsonl.
    """
    merged_key = f"{prefix}compacted.jsonl"

    # List all objects under the prefix
    keys = []
    paginator = s3_client.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get('Contents', []):
            keys.append(obj['Key'])

    if not keys or keys == [merged_key]:
        logger.info(f"Nothing to compact for {prefix}: already compacted or empty")
        return 0

    # Download and concatenate all files
    lines = []
    for key in keys:
        resp = s3_client.get_object(Bucket=bucket, Key=key)
        body = resp['Body'].read().decode('utf-8').strip()
        if body:
            lines.append(body)

    merged = '\n'.join(lines)

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

    return len(keys)


def lambda_handler(event, context):
    """
    Hourly compaction with a lookback sweep: merge the just-closed hour, and
    re-check the previous ~24 hours so a missed schedule tick self-heals
    instead of leaving that hour permanently uncompacted.
    """
    bucket = os.environ['S3_BUCKET']
    lookback_hours = int(os.environ.get('COMPACTOR_LOOKBACK_HOURS', DEFAULT_LOOKBACK_HOURS))

    now = datetime.now(timezone.utc)
    compacted_hours = {}
    for hours_ago in range(1, lookback_hours + 1):
        target = now - timedelta(hours=hours_ago)
        prefix = f"jsonl/{target.year}/{target.month:02d}/{target.day:02d}/{target.hour:02d}/"
        logger.info(f"Checking {prefix} in {bucket}")
        compacted = compact_hour(bucket, prefix, s3_client)
        if compacted:
            compacted_hours[prefix] = compacted

    return {
        'compacted_total': sum(compacted_hours.values()),
        'hours': compacted_hours,
    }
