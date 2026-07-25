"""Bounded, asynchronous S3 delivery for Manufact MCP analytics events."""

import atexit
from collections import deque
from datetime import datetime, timezone
import json
import os
import signal
import threading
from typing import Any, Protocol
from uuid import uuid4

from loguru import logger

from av_mcp import s3_ingest_client


DEFAULT_FLUSH_INTERVAL_SECONDS = 30
DEFAULT_BATCH_SIZE = 100
DEFAULT_QUEUE_SIZE = 1_000

# Forced by the emitter regardless of transport; the ingest proxy's server-side
# "analytics" target composes the identical prefix on its own, so the resulting S3
# key is the same whether written directly or through the proxy.
ANALYTICS_KEY_PREFIX = "jsonl/"


class AnalyticsWriter(Protocol):
    """Delivers one flushed JSONL batch somewhere; never raises."""

    def write(self, key_suffix: str, body: bytes) -> tuple[bool, str | None]:
        """Return (success, key-on-success | error-message-on-failure)."""
        ...


class S3DirectWriter:
    """Write objects straight to S3 via boto3 (local/dev, or any deployment that
    still holds AWS credentials of its own)."""

    def __init__(self, bucket: str, s3_client: Any) -> None:
        self.bucket = bucket
        self.s3_client = s3_client

    def write(self, key_suffix: str, body: bytes) -> tuple[bool, str | None]:
        key = ANALYTICS_KEY_PREFIX + key_suffix
        try:
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=body,
                ContentType="application/jsonlines",
            )
        except Exception as e:
            return False, str(e)
        return True, key


class IngestProxyWriter:
    """Write objects through the mcp-s3-ingest proxy Lambda (no AWS credentials
    needed in the container)."""

    def write(self, key_suffix: str, body: bytes) -> tuple[bool, str | None]:
        result = s3_ingest_client.put_object(
            "analytics", key_suffix, body, "application/jsonlines"
        )
        if result is None:
            return False, "ingest proxy request failed"
        return True, ANALYTICS_KEY_PREFIX + key_suffix


class AnalyticsEmitter:
    """Queue MCP analytics events and deliver them to S3 without blocking requests."""

    def __init__(
        self,
        writer: AnalyticsWriter,
        *,
        flush_interval_seconds: float = DEFAULT_FLUSH_INTERVAL_SECONDS,
        batch_size: int = DEFAULT_BATCH_SIZE,
        max_queue_size: int = DEFAULT_QUEUE_SIZE,
        start_thread: bool = True,
    ) -> None:
        self.writer = writer
        self.flush_interval_seconds = flush_interval_seconds
        self.batch_size = batch_size
        self.max_queue_size = max_queue_size
        self._records: deque[dict[str, str]] = deque()
        self._lock = threading.Lock()
        self._flush_lock = threading.Lock()
        self._flush_requested = threading.Event()
        self._stopped = threading.Event()
        self._thread: threading.Thread | None = None
        self._closed = False

        if start_thread:
            self._thread = threading.Thread(
                target=self._run,
                name="mcp-analytics-s3-emitter",
                daemon=True,
            )
            self._thread.start()

    @classmethod
    def from_environment(cls) -> "AnalyticsEmitter | None":
        """Create an emitter using whichever S3 write path this deployment can reach.

        ``S3_INGEST_URL`` set -> proxy through mcp-s3-ingest (Manufact has no AWS
        credentials); else ``ANALYTICS_LOGS_BUCKET`` set -> direct boto3 write
        (local/dev, or a deployment that does hold credentials); neither set ->
        disabled.
        """
        ingest_url = os.getenv("S3_INGEST_URL")
        bucket = os.getenv("ANALYTICS_LOGS_BUCKET")
        kwargs = dict(
            flush_interval_seconds=_positive_float_env(
                "ANALYTICS_S3_FLUSH_INTERVAL_SECONDS",
                DEFAULT_FLUSH_INTERVAL_SECONDS,
            ),
            batch_size=_positive_int_env("ANALYTICS_S3_BATCH_SIZE", DEFAULT_BATCH_SIZE),
            max_queue_size=_positive_int_env(
                "ANALYTICS_S3_MAX_QUEUE_SIZE", DEFAULT_QUEUE_SIZE
            ),
        )

        if ingest_url:
            if not os.getenv("S3_INGEST_SECRET"):
                logger.info(
                    "MCP_ANALYTICS: emitter=DISABLED, "
                    "reason=S3_INGEST_URL set without S3_INGEST_SECRET"
                )
                return None
            logger.info("MCP_ANALYTICS: emitter=ENABLED, transport=proxy")
            return cls(IngestProxyWriter(), **kwargs)

        if not bucket:
            logger.info(
                "MCP_ANALYTICS: emitter=DISABLED, reason=ANALYTICS_LOGS_BUCKET not set"
            )
            return None

        try:
            import boto3

            s3_client = boto3.client(
                "s3", region_name=os.getenv("AWS_REGION", "us-east-1")
            )
        except Exception as e:
            logger.error(
                "MCP_ANALYTICS: emitter=DISABLED, reason=unable to create S3 client, error={}",
                e,
            )
            return None

        logger.info(
            "MCP_ANALYTICS: emitter=ENABLED, transport=s3direct, bucket={}", bucket
        )
        return cls(S3DirectWriter(bucket, s3_client), **kwargs)

    def emit_mcp_request(
        self, body: str | dict[str, Any], api_key: str, platform: str
    ) -> None:
        """Enqueue a schema-compatible analytics event for an MCP JSON-RPC request."""
        if not body:
            return

        try:
            parsed_body = json.loads(body) if isinstance(body, str) else body
        except (json.JSONDecodeError, TypeError):
            return

        if not isinstance(parsed_body, dict) or "method" not in parsed_body:
            return

        mcp_params = parsed_body.get("params", {})
        if not isinstance(mcp_params, dict):
            mcp_params = {}
        tool_args = mcp_params.get("arguments", {})

        self.emit(
            {
                "created_at": datetime.now(timezone.utc).strftime(
                    "%Y-%m-%d %H:%M:%S.%f"
                ),
                "method": str(parsed_body["method"]),
                "api_key": api_key,
                "platform": platform,
                "tool_name": str(mcp_params.get("name", "unknown")),
                "arguments": json.dumps(tool_args),
            }
        )

    def emit(self, record: dict[str, str]) -> None:
        """Append an event without waiting on S3; overflow drops the oldest event."""
        with self._lock:
            if len(self._records) >= self.max_queue_size:
                self._records.popleft()
                logger.warning(
                    "MCP_ANALYTICS: queue_overflow, dropped=1, max_queue_size={}",
                    self.max_queue_size,
                )
            self._records.append(record)
            if len(self._records) >= self.batch_size:
                self._flush_requested.set()

    def flush(self) -> None:
        """Upload all queued events in one JSONL object, without exposing credentials."""
        with self._flush_lock:
            with self._lock:
                if not self._records:
                    return
                records = list(self._records)
                self._records.clear()

            now = datetime.now(timezone.utc)
            key_suffix = (
                f"{now.year}/{now.month:02d}/{now.day:02d}/{now.hour:02d}/"
                f"{now.strftime('%Y%m%d_%H%M%S_%f')}_{uuid4().hex}.jsonl"
            )
            content = "\n".join(json.dumps(record) for record in records) + "\n"

            success, key_or_error = self.writer.write(
                key_suffix, content.encode("utf-8")
            )
            if not success:
                logger.warning(
                    "MCP_ANALYTICS: flush=failed, events={}, error={}",
                    len(records),
                    key_or_error,
                )
                return

            logger.info(
                "MCP_ANALYTICS: flush=success, events={}, key={}",
                len(records),
                key_or_error,
            )

    def close(self) -> None:
        """Stop the worker and synchronously flush events left in memory."""
        if self._closed:
            return
        self._closed = True
        self._stopped.set()
        self._flush_requested.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=self.flush_interval_seconds + 5)
        self.flush()

    def install_shutdown_hooks(self) -> None:
        """Flush on normal interpreter exit and Manufact/Docker SIGTERM shutdown."""
        atexit.register(self.close)

        def handle_sigterm(_signum: int, _frame: Any) -> None:
            self.close()
            raise SystemExit(0)

        signal.signal(signal.SIGTERM, handle_sigterm)

    def _run(self) -> None:
        while not self._stopped.is_set():
            self._flush_requested.wait(self.flush_interval_seconds)
            self._flush_requested.clear()
            self.flush()


def _positive_float_env(name: str, default: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except ValueError:
        return default
    return value if value > 0 else default


def _positive_int_env(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return value if value > 0 else default
