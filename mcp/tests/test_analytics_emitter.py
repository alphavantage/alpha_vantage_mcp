import json
import threading
from contextlib import contextmanager

from av_mcp.analytics_emitter import AnalyticsEmitter
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
    emitter = AnalyticsEmitter("unit-analytics-bucket", s3_client, start_thread=False)

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
    assert (
        f"MCP_ANALYTICS: flush=success, events=1, key={call['Key']}" in joined
    )


def test_emitter_drops_oldest_event_when_queue_is_full():
    s3_client = RecordingS3Client()
    emitter = AnalyticsEmitter(
        "unit-analytics-bucket", s3_client, max_queue_size=2, start_thread=False
    )

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
    emitter = AnalyticsEmitter(
        "unit-analytics-bucket",
        s3_client,
        flush_interval_seconds=60,
        batch_size=2,
    )

    emitter.emit(_record(1))
    emitter.emit(_record(2))

    assert s3_client.put_event.wait(timeout=1)
    emitter.close()
    assert len(s3_client.calls) == 1


def test_from_environment_gates_on_analytics_logs_bucket(monkeypatch):
    monkeypatch.delenv("ANALYTICS_LOGS_BUCKET", raising=False)
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
        assert emitter.bucket == "unit-analytics-bucket"
        assert any(
            "MCP_ANALYTICS: emitter=ENABLED, bucket=unit-analytics-bucket" in msg
            for msg in messages
        )
    finally:
        emitter.close()


def test_emitter_never_logs_raw_api_key_on_upload_failure():
    with _capture_log_messages() as messages:
        emitter = AnalyticsEmitter(
            "unit-analytics-bucket", FailingS3Client(), start_thread=False
        )
        emitter.emit_mcp_request(
            json.dumps({"method": "tools/list"}), "unit-secret-token", "test"
        )
        emitter.flush()

    joined = "\n".join(messages)
    assert "unit-secret-token" not in joined
    assert "MCP_ANALYTICS: flush=failed, events=1, error=" in joined
    assert "synthetic upload failure" in joined
