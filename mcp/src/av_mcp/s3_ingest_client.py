"""HTTP client for the mcp-s3-ingest proxy Lambda.

Manufact containers hold no AWS credentials and cannot be given any (todo 2842,
round 6), so both analytics delivery and the large-response CDN upload route
through this shared-secret protected endpoint instead of a direct boto3 PutObject.
"""

import json
import os

import httpx
from loguru import logger

DEFAULT_TIMEOUT_SECONDS = 10.0


def is_configured() -> bool:
    """True when both the ingest URL and shared secret are set."""
    return bool(os.getenv("S3_INGEST_URL")) and bool(os.getenv("S3_INGEST_SECRET"))


def put_object(
    target: str,
    key_suffix: str,
    body: bytes,
    content_type: str,
    *,
    client: httpx.Client | None = None,
) -> dict | None:
    """PUT an object through the ingest proxy.

    Returns the parsed JSON response on a 200, or ``None`` on any failure. Retries
    exactly once on a connection error or 5xx response: boto3 clients retry by
    default, and a plain httpx call does not, so this keeps the proxy transport's
    reliability on par with the direct-S3 transport it replaces. Never logs the
    secret.
    """
    url = os.getenv("S3_INGEST_URL")
    secret = os.getenv("S3_INGEST_SECRET")
    if not url or not secret:
        return None

    headers = {
        "X-Ingest-Secret": secret,
        "X-Ingest-Target": target,
        "X-Ingest-Key": key_suffix,
        "Content-Type": content_type,
    }

    owns_client = client is None
    if owns_client:
        client = httpx.Client(timeout=DEFAULT_TIMEOUT_SECONDS)

    try:
        response = None
        last_error = None
        for _attempt in range(2):
            try:
                response = client.post(url, headers=headers, content=body)
            except httpx.HTTPError as e:
                last_error = e
                response = None
                continue
            if response.status_code < 500:
                break

        if response is None:
            logger.warning(
                "s3_ingest_client: request failed, target={}, error={}",
                target,
                last_error,
            )
            return None

        if response.status_code != 200:
            logger.warning(
                "s3_ingest_client: rejected, target={}, status={}",
                target,
                response.status_code,
            )
            return None

        try:
            return response.json()
        except json.JSONDecodeError:
            logger.warning("s3_ingest_client: non-JSON 200 response, target={}", target)
            return None
    finally:
        if owns_client:
            client.close()
