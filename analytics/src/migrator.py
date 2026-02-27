import asyncio
import os
import re
import json
import logging
import time
from aiobotocore.session import get_session

logger = logging.getLogger()
logger.setLevel(logging.INFO)

LOG_PATTERN = re.compile(
    r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+).*MCP_ANALYTICS: '
    r'method=([^,]+), api_key=([^,]+), platform=([^,]+), tool_name=([^,]+), arguments=(.*)$'
)

BATCH_SIZE = 200
PROGRESS_KEY = 'jsonl/_migration_progress.json'
LOCK_KEY = 'jsonl/_migration_lock.json'
LOCK_TTL_SECONDS = 960  # lock expires after 16 min (timeout is 15 min)
MAX_CONCURRENCY = 20
TIME_BUFFER_MS = 30000  # stop 30s before timeout


def lambda_handler(event, context):
    """
    Migrate old .txt files from logs/ to jsonl/.

    Loops through hours until near timeout, saving progress to S3.
    Cron (EventBridge) re-triggers to continue where it left off.
    Uses asyncio + aiobotocore for concurrent S3 reads within each batch.
    """
    return asyncio.get_event_loop().run_until_complete(_handler(event, context))


async def _handler(event, context):
    bucket = os.environ['S3_BUCKET']

    session = get_session()
    async with session.create_client('s3') as s3:
        # Acquire lock — skip if another instance is running
        if not await acquire_lock(s3, bucket):
            logger.info("Another instance is running, skipping")
            return {'status': 'skipped', 'reason': 'locked'}

        try:
            progress = await load_progress(s3, bucket)
            if event.get('reset'):
                progress = {}

            continuation_token = progress.get('continuation_token')
            migrated_hours = progress.get('migrated_hours', 0)
            total_records = progress.get('total_records', 0)

            # Resume in-progress hour if any
            hour_prefix = progress.get('hour_prefix')
            file_marker = progress.get('file_marker')
            part_num = progress.get('part_num', 0)

            while context.get_remaining_time_in_millis() > TIME_BUFFER_MS:
                # Find next hour if not resuming one
                if not hour_prefix:
                    hour_prefix, continuation_token = await find_next_hour(s3, bucket, continuation_token)
                    if not hour_prefix:
                        logger.info(f"Migration complete. {migrated_hours} hours, {total_records} records.")
                        await save_progress(s3, bucket, {'status': 'complete', 'migrated_hours': migrated_hours, 'total_records': total_records})
                        return {'status': 'complete', 'migrated_hours': migrated_hours, 'total_records': total_records}
                    part_num = 0
                    file_marker = None

                jsonl_prefix = hour_prefix.replace('logs/', 'jsonl/', 1)

                # Process one batch
                result = await process_batch(s3, bucket, hour_prefix, jsonl_prefix, part_num, file_marker)
                total_records += result['records']

                if result['has_more']:
                    file_marker = result['last_key']
                    part_num += 1
                    logger.info(f"{hour_prefix} part {part_num}: {result['records']} records, more remaining")
                else:
                    # Hour done
                    await s3.put_object(Bucket=bucket, Key=f"{jsonl_prefix}_DONE", Body=b'')
                    migrated_hours += 1
                    logger.info(f"Completed {hour_prefix} (hour #{migrated_hours}, {total_records} total records)")
                    hour_prefix = None
                    file_marker = None
                    part_num = 0

            # Save progress for next cron invocation
            progress = {
                'continuation_token': continuation_token,
                'migrated_hours': migrated_hours,
                'total_records': total_records,
            }
            if hour_prefix:
                progress['hour_prefix'] = hour_prefix
                progress['file_marker'] = file_marker
                progress['part_num'] = part_num

            await save_progress(s3, bucket, progress)
        finally:
            await release_lock(s3, bucket)

    return {'status': 'continuing', 'migrated_hours': migrated_hours, 'total_records': total_records}


async def acquire_lock(s3, bucket):
    """Try to acquire lock. Returns True if acquired, False if held by another."""
    try:
        resp = await s3.get_object(Bucket=bucket, Key=LOCK_KEY)
        body = await resp['Body'].read()
        lock = json.loads(body.decode('utf-8'))
        if time.time() < lock.get('expires_at', 0):
            return False  # lock is still valid
    except s3.exceptions.ClientError:
        pass  # no lock exists

    lock = {'acquired_at': time.time(), 'expires_at': time.time() + LOCK_TTL_SECONDS}
    await s3.put_object(
        Bucket=bucket, Key=LOCK_KEY,
        Body=json.dumps(lock).encode('utf-8'),
        ContentType='application/json',
    )
    return True


async def release_lock(s3, bucket):
    """Release the lock."""
    try:
        await s3.delete_object(Bucket=bucket, Key=LOCK_KEY)
    except s3.exceptions.ClientError:
        pass


async def load_progress(s3, bucket):
    try:
        resp = await s3.get_object(Bucket=bucket, Key=PROGRESS_KEY)
        body = await resp['Body'].read()
        return json.loads(body.decode('utf-8'))
    except s3.exceptions.ClientError:
        return {}


async def save_progress(s3, bucket, progress):
    await s3.put_object(
        Bucket=bucket,
        Key=PROGRESS_KEY,
        Body=json.dumps(progress, indent=2).encode('utf-8'),
        ContentType='application/json',
    )


async def find_next_hour(s3, bucket, continuation_token=None):
    """Find next hour prefix under logs/ that hasn't been fully migrated."""
    kwargs = {'Bucket': bucket, 'Prefix': 'logs/', 'MaxKeys': 1000}
    if continuation_token:
        kwargs['ContinuationToken'] = continuation_token

    resp = await s3.list_objects_v2(**kwargs)
    contents = resp.get('Contents', [])

    hour_set = set()
    for obj in contents:
        parts = obj['Key'].split('/')
        if len(parts) >= 5:
            hour_set.add('/'.join(parts[:5]) + '/')

    next_token = resp.get('NextContinuationToken') if resp.get('IsTruncated') else None

    for prefix in sorted(hour_set):
        done_key = prefix.replace('logs/', 'jsonl/', 1) + '_DONE'
        try:
            await s3.head_object(Bucket=bucket, Key=done_key)
            continue
        except s3.exceptions.ClientError:
            return prefix, next_token

    if next_token:
        return await find_next_hour(s3, bucket, next_token)

    return None, None


async def read_and_parse(s3, bucket, key, semaphore):
    """Read a single S3 object and parse MCP_ANALYTICS lines."""
    async with semaphore:
        resp = await s3.get_object(Bucket=bucket, Key=key)
        body = await resp['Body'].read()
        text = body.decode('utf-8')

    parsed = []
    for line in text.strip().split('\n'):
        line = line.strip()
        if not line or 'MCP_ANALYTICS' not in line:
            continue
        match = LOG_PATTERN.match(line)
        if not match:
            continue
        ts, method, api_key, platform, tool_name, arguments = match.groups()
        parsed.append({
            'created_at': ts,
            'method': method,
            'api_key': api_key,
            'platform': platform,
            'tool_name': tool_name,
            'arguments': arguments,
        })
    return parsed


async def process_batch(s3, bucket, hour_prefix, jsonl_prefix, part_num, start_after=None):
    """Process up to BATCH_SIZE .txt files with concurrent S3 reads."""
    kwargs = {'Bucket': bucket, 'Prefix': hour_prefix, 'MaxKeys': BATCH_SIZE}
    if start_after:
        kwargs['StartAfter'] = start_after

    resp = await s3.list_objects_v2(**kwargs)
    contents = resp.get('Contents', [])
    keys = [obj['Key'] for obj in contents if obj['Key'].endswith('.txt')]

    if not keys:
        return {'records': 0, 'has_more': False, 'last_key': None}

    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
    tasks = [read_and_parse(s3, bucket, key, semaphore) for key in keys]
    results = await asyncio.gather(*tasks)

    records = []
    for parsed in results:
        records.extend(parsed)

    if records:
        part_key = f"{jsonl_prefix}part-{part_num:04d}.jsonl"
        content = '\n'.join(json.dumps(r) for r in records)
        await s3.put_object(
            Bucket=bucket, Key=part_key,
            Body=content.encode('utf-8'),
            ContentType='application/jsonlines',
        )
        logger.info(f"Wrote {len(records)} records to {part_key}")

    has_more = resp.get('IsTruncated', False) or len(contents) == BATCH_SIZE

    return {
        'records': len(records),
        'has_more': has_more,
        'last_key': keys[-1] if keys else None,
    }
