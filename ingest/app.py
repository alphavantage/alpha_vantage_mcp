"""Standalone S3 PutObject proxy for containers with no AWS credentials of their own.

Self-contained (stdlib + the boto3 already bundled in the Lambda runtime): it never
imports av_mcp/av_api, so it gets a fast cold start and its own log group, which keeps
its logs structurally outside the MCP function's "MCP_ANALYTICS" subscription filter.

Wire contract: POST with X-Ingest-Secret / X-Ingest-Target / X-Ingest-Key headers and
the object bytes as the raw request body. The bucket and key prefix are resolved
server-side from the target (never supplied by the caller), so a request can only ever
reach the two allowlisted prefixes below.
"""

import base64
import hmac
import json
import logging
import os
import re
import time

import boto3

logger = logging.getLogger("mcp_s3_ingest")
logger.setLevel(logging.INFO)

MAX_BODY_BYTES = (
    5 * 1024 * 1024
)  # 5 MiB, comfortably under the 6 MB Lambda proxy ceiling

# Suffix is appended verbatim to the target's forced prefix, so it must stay a plain
# relative path: no leading slash, no "..", no doubled slashes.
_SUFFIX_RE = re.compile(r"^[A-Za-z0-9._/-]{1,256}$")

TARGETS = {
    "analytics": {
        "bucket_env": "ANALYTICS_LOGS_BUCKET",
        "prefix": "jsonl/",
        "content_types": {"application/jsonlines"},
    },
    "cdn": {
        "bucket_env": "CDN_BUCKET_NAME",
        "prefix": "mcp-responses/",
        "content_types": {"application/json", "text/csv"},
    },
}

_s3_client = None


def _s3():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3", region_name=os.getenv("AWS_REGION", "us-east-1")
        )
    return _s3_client


def _response(status: int, payload: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload),
    }


def _valid_suffix(suffix: str) -> bool:
    if not suffix or not _SUFFIX_RE.match(suffix):
        return False
    if suffix.startswith("/") or "//" in suffix or ".." in suffix:
        return False
    return True


def _extra_put_kwargs(target: str) -> dict:
    if target == "cdn":
        return {
            "Tagging": "AutoDelete=true",
            "CacheControl": "public, max-age=3600",
            "Metadata": {"created": str(int(time.time()))},
        }
    return {}


def lambda_handler(event: dict, _context) -> dict:
    if event.get("httpMethod", "UNKNOWN") != "POST":
        return _response(405, {"error": "method_not_allowed"})

    configured_secret = os.getenv("S3_INGEST_SECRET", "")
    if not configured_secret:
        logger.warning("mcp-s3-ingest: rejected, reason=secret not configured")
        return _response(503, {"error": "not_configured"})

    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}

    provided_secret = headers.get("x-ingest-secret", "")
    # Compare UTF-8 bytes, not str: hmac.compare_digest raises TypeError on a str
    # argument containing non-ASCII characters, which would otherwise let an
    # unauthenticated caller reach an unhandled exception instead of a clean 401.
    if not hmac.compare_digest(configured_secret.encode(), provided_secret.encode()):
        logger.warning("mcp-s3-ingest: rejected, reason=bad secret")
        return _response(401, {"error": "unauthorized"})

    target = headers.get("x-ingest-target", "")
    target_config = TARGETS.get(target)
    if target_config is None:
        return _response(400, {"error": "unknown_target"})

    suffix = headers.get("x-ingest-key", "")
    if not _valid_suffix(suffix):
        return _response(400, {"error": "bad_key"})

    content_type = headers.get("content-type", "")
    if content_type not in target_config["content_types"]:
        return _response(400, {"error": "bad_content_type"})

    body = event.get("body") or ""
    body_bytes = (
        base64.b64decode(body) if event.get("isBase64Encoded") else body.encode("utf-8")
    )
    if len(body_bytes) > MAX_BODY_BYTES:
        return _response(413, {"error": "payload_too_large"})

    bucket = os.getenv(target_config["bucket_env"], "")
    if not bucket:
        logger.warning(
            "mcp-s3-ingest: rejected, target=%s, reason=bucket not configured", target
        )
        return _response(503, {"error": "not_configured"})

    key = target_config["prefix"] + suffix

    try:
        _s3().put_object(
            Bucket=bucket,
            Key=key,
            Body=body_bytes,
            ContentType=content_type,
            **_extra_put_kwargs(target),
        )
    except Exception as e:
        logger.error(
            "mcp-s3-ingest: put_object failed, target=%s, key=%s, error=%s",
            target,
            key,
            e,
        )
        return _response(500, {"error": "upload_failed"})

    logger.info(
        "mcp-s3-ingest: put_object ok, target=%s, key=%s, bytes=%d",
        target,
        key,
        len(body_bytes),
    )

    result = {"ok": True, "bucket": bucket, "key": key}
    if target == "cdn":
        cdn_domain = os.getenv("CDN_DOMAIN", "")
        if cdn_domain:
            result["public_url"] = f"https://{cdn_domain}/{key}"

    return _response(200, result)
