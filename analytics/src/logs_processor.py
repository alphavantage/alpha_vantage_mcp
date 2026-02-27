import json
import base64
import gzip
import boto3
import os
import re
from datetime import datetime
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')

# Regex to parse MCP_ANALYTICS log lines
LOG_PATTERN = re.compile(
    r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+).*MCP_ANALYTICS: '
    r'method=([^,]+), api_key=([^,]+), platform=([^,]+), tool_name=([^,]+), arguments=(.*)$'
)

def lambda_handler(event, context):
    """
    Lambda function to consume CloudWatch Logs via Subscription Filter
    and write structured JSON lines to S3.
    """
    s3_bucket = os.environ['S3_BUCKET']
    processed_records = 0
    failed_records = 0

    records = []

    try:
        # Decode CloudWatch Logs data from Subscription Filter
        compressed_data = base64.b64decode(event['awslogs']['data'])
        log_data = gzip.decompress(compressed_data).decode('utf-8')
        log_json = json.loads(log_data)

        # Process CloudWatch log events
        if 'logEvents' in log_json:
            for log_event in log_json['logEvents']:
                try:
                    record = parse_log_event(log_event)
                    if record:
                        records.append(record)
                        processed_records += 1
                except Exception as e:
                    logger.error(f"Error processing log event: {str(e)}")
                    failed_records += 1

        # Write batched JSON lines to S3
        if records:
            write_logs_to_s3(records, s3_bucket)

        logger.info(f"Processed {processed_records} records successfully, {failed_records} failed")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'processed': processed_records,
                'failed': failed_records
            })
        }

    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def parse_log_event(log_event):
    """Parse a single log event into a structured dict."""
    message = log_event.get('message', '').strip()

    if 'MCP_ANALYTICS' not in message:
        return None

    match = LOG_PATTERN.match(message)
    if not match:
        logger.warning(f"Failed to parse log line: {message[:200]}")
        return None

    timestamp_str, method, api_key, platform, tool_name, arguments = match.groups()

    return {
        'created_at': timestamp_str,
        'method': method,
        'api_key': api_key,
        'platform': platform,
        'tool_name': tool_name,
        'arguments': arguments,
    }

def write_logs_to_s3(records, s3_bucket):
    """Write JSON lines to S3 with the expected key format: logs/YYYY/MM/DD/HH/xxx.jsonl"""
    try:
        content = '\n'.join(json.dumps(r) for r in records)

        now = datetime.utcnow()
        s3_key = f"jsonl/{now.year}/{now.month:02d}/{now.day:02d}/{now.hour:02d}/{now.strftime('%Y%m%d_%H%M%S_%f')}.jsonl"

        s3_client.put_object(
            Bucket=s3_bucket,
            Key=s3_key,
            Body=content.encode('utf-8'),
            ContentType='application/jsonlines',
        )

        logger.info(f"Wrote {len(records)} records to s3://{s3_bucket}/{s3_key}")

    except Exception as e:
        logger.error(f"Error writing logs to S3: {str(e)}")
        raise
