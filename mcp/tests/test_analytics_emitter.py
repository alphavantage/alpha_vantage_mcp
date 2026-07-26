import json
import sys
import threading
from contextlib import contextmanager

import httpx

from av_mcp.analytics_emitter import AnalyticsEmitter, IngestProxyWriter, S3DirectWriter
from loguru import logger


class RecordingS3Client:
    def __init__(self):
        self.calls = []
        self.put_event = threading.Event()

    def put_object(self, **kwargs):
        self.calls.append(kwargs)
        self.put_event.set()


class FailingS3Client:
    def put_object(self, **_kwargs):
        raise RuntimeError("synthetic upload failure")


def _direct_emitter(s3_client, bucket="unit-analytics-bucket", **kwargs):
    return AnalyticsEmitter(S3DirectWriter(bucket, s3_client), **kwargs)


def _record(index: int) -> dict[str, str]:
    return {
        "created_at": f"2026-07-25 10:00:0{index}.000000",
        "method": "tools/call",
        "api_key": f"unit-token-{index}",
        "platform": "test",
        "tool_name": f"TOOL_{index}",
        "arguments": "{}",
    }


@contextmanager
def _capture_log_messages():
    messages = []
    sink_id = logger.add(messages.append, format="{message}")
    try:
        yield messages
    finally:
        logger.remove(sink_id)


def test_emitter_writes_schema_compatible_jsonl():
    s3_client = RecordingS3Client()
    emitter = _direct_emitter(s3_client, start_thread=False)

    with _capture_log_messages() as messages:
        emitter.emit_mcp_request(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {"name": "GLOBAL_QUOTE", "arguments": {"symbol": "IBM"}},
                }
            ),
            "unit-token",
            "cursor",
        )
        emitter.flush()

    assert len(s3_client.calls) == 1
    call = s3_client.calls[0]
    assert call["Bucket"] == "unit-analytics-bucket"
    assert call["Key"].startswith("jsonl/")
    assert call["Key"].endswith(".jsonl")
    assert call["ContentType"] == "application/jsonlines"
    records = [json.loads(line) for line in call["Body"].decode().splitlines()]
    assert records == [
        {
            "created_at": records[0]["created_at"],
            "method": "tools/call",
            "api_key": "unit-token",
            "platform": "cursor",
            "tool_name": "GLOBAL_QUOTE",
            "arguments": '{"symbol": "IBM"}',
        }
    ]
    joined = "\n".join(messages)
    assert f"MCP_ANALYTICS: flush=success, events=1, key={call['Key']}" in joined


def test_emit_mcp_request_strips_identifier_fields():
    """Padded api_key / method / platform / tool_name land clean (todo 2892)."""
    s3_client = RecordingS3Client()
    emitter = _direct_emitter(s3_client, start_thread=False)

    emitter.emit_mcp_request(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "method": " tools/call ",
                "params": {
                    "name": " GLOBAL_QUOTE ",
                    "arguments": {"symbol": "IBM"},
                },
            }
        ),
        "\xa0unit-token\xa0",
        " cursor ",
    )
    emitter.flush()

    records = [json.loads(line) for line in s3_client.calls[0]["Body"].decode().splitlines()]
    assert len(records) == 1
    record = records[0]
    assert record["api_key"] == "unit-token"
    assert record["method"] == "tools/call"
    assert record["platform"] == "cursor"
    assert record["tool_name"] == "GLOBAL_QUOTE"
    assert record["arguments"] == '{"symbol": "IBM"}'


def test_emitter_drops_oldest_event_when_queue_is_full():
    s3_client = RecordingS3Client()
    emitter = _direct_emitter(s3_client, max_queue_size=2, start_thread=False)

    with _capture_log_messages() as messages:
        emitter.emit(_record(1))
        emitter.emit(_record(2))
        emitter.emit(_record(3))
        emitter.close()

    records = [
        json.loads(line) for line in s3_client.calls[0]["Body"].decode().splitlines()
    ]
    assert [record["tool_name"] for record in records] == ["TOOL_2", "TOOL_3"]
    assert any(
        "MCP_ANALYTICS: queue_overflow, dropped=1, max_queue_size=2" in msg
        for msg in messages
    )


def test_emitter_flushes_when_batch_size_is_reached():
    s3_client = RecordingS3Client()
    emitter = _direct_emitter(s3_client, flush_interval_seconds=60, batch_size=2)

    emitter.emit(_record(1))
    emitter.emit(_record(2))

    assert s3_client.put_event.wait(timeout=1)
    emitter.close()
    assert len(s3_client.calls) == 1


def _clear_transport_env(monkeypatch):
    monkeypatch.delenv("S3_INGEST_URL", raising=False)
    monkeypatch.delenv("S3_INGEST_SECRET", raising=False)
    monkeypatch.delenv("ANALYTICS_LOGS_BUCKET", raising=False)


def test_from_environment_gates_on_analytics_logs_bucket(monkeypatch):
    _clear_transport_env(monkeypatch)
    with _capture_log_messages() as messages:
        assert AnalyticsEmitter.from_environment() is None
    assert any(
        "MCP_ANALYTICS: emitter=DISABLED, reason=ANALYTICS_LOGS_BUCKET not set" in msg
        for msg in messages
    )

    monkeypatch.setenv("ANALYTICS_LOGS_BUCKET", "unit-analytics-bucket")
    with _capture_log_messages() as messages:
        emitter = AnalyticsEmitter.from_environment()
    try:
        assert emitter is not None
        assert isinstance(emitter.writer, S3DirectWriter)
        assert emitter.writer.bucket == "unit-analytics-bucket"
        assert any(
            "MCP_ANALYTICS: emitter=ENABLED, transport=s3direct, bucket=unit-analytics-bucket"
            in msg
            for msg in messages
        )
    finally:
        emitter.close()


def test_from_environment_prefers_proxy_transport_when_ingest_url_is_set(monkeypatch):
    _clear_transport_env(monkeypatch)
    monkeypatch.setenv("ANALYTICS_LOGS_BUCKET", "unit-analytics-bucket")
    monkeypatch.setenv("S3_INGEST_URL", "https://ingest.example.test/internal/s3-put")

    with _capture_log_messages() as messages:
        assert AnalyticsEmitter.from_environment() is None
    assert any(
        "MCP_ANALYTICS: emitter=DISABLED, "
        "reason=S3_INGEST_URL set without S3_INGEST_SECRET" in msg
        for msg in messages
    )

    monkeypatch.setenv("S3_INGEST_SECRET", "unit-secret")
    with _capture_log_messages() as messages:
        emitter = AnalyticsEmitter.from_environment()
    try:
        assert emitter is not None
        assert isinstance(emitter.writer, IngestProxyWriter)
        assert any(
            "MCP_ANALYTICS: emitter=ENABLED, transport=proxy" in msg for msg in messages
        )
    finally:
        emitter.close()


def test_emitter_never_logs_raw_api_key_on_upload_failure():
    with _capture_log_messages() as messages:
        emitter = _direct_emitter(FailingS3Client(), start_thread=False)
        emitter.emit_mcp_request(
            json.dumps({"method": "tools/list"}), "unit-secret-token", "test"
        )
        emitter.flush()

    joined = "\n".join(messages)
    assert "unit-secret-token" not in joined
    assert "MCP_ANALYTICS: flush=failed, events=1, error=" in joined
    assert "synthetic upload failure" in joined


def test_proxy_writer_flush_posts_exact_jsonl_body_and_never_touches_boto3(monkeypatch):
    monkeypatch.setenv("S3_INGEST_URL", "https://ingest.example.test/internal/s3-put")
    monkeypatch.setenv("S3_INGEST_SECRET", "unit-secret")
    monkeypatch.setitem(sys.modules, "boto3", None)  # importing boto3 would now raise

    captured = {}
    real_client_class = httpx.Client

    def handler(request: httpx.Request) -> httpx.Response:
        captured["headers"] = request.headers
        captured["body"] = request.content
        return httpx.Response(
            200, json={"ok": True, "bucket": "b", "key": "jsonl/x.jsonl"}
        )

    def fake_client(**_kwargs):
        return real_client_class(transport=httpx.MockTransport(handler))

    monkeypatch.setattr("av_mcp.s3_ingest_client.httpx.Client", fake_client)

    emitter = AnalyticsEmitter(IngestProxyWriter(), start_thread=False)
    with _capture_log_messages() as messages:
        emitter.emit(_record(1))
        emitter.flush()

    assert captured["headers"]["x-ingest-target"] == "analytics"
    assert captured["headers"]["x-ingest-secret"] == "unit-secret"
    assert captured["body"] == (json.dumps(_record(1)) + "\n").encode("utf-8")
    assert any(
        "MCP_ANALYTICS: flush=success, events=1, key=jsonl/" in msg for msg in messages
    )
