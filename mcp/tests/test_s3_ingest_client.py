import httpx

from av_mcp import s3_ingest_client
from loguru import logger


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_is_configured_requires_url_and_secret(monkeypatch):
    monkeypatch.delenv("S3_INGEST_URL", raising=False)
    monkeypatch.delenv("S3_INGEST_SECRET", raising=False)
    assert s3_ingest_client.is_configured() is False

    monkeypatch.setenv("S3_INGEST_URL", "https://ingest.example.test/internal/s3-put")
    assert s3_ingest_client.is_configured() is False

    monkeypatch.setenv("S3_INGEST_SECRET", "unit-secret")
    assert s3_ingest_client.is_configured() is True


def test_put_object_sends_expected_headers_and_body(monkeypatch):
    monkeypatch.setenv("S3_INGEST_URL", "https://ingest.example.test/internal/s3-put")
    monkeypatch.setenv("S3_INGEST_SECRET", "unit-secret")

    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["headers"] = request.headers
        captured["body"] = request.content
        return httpx.Response(
            200, json={"ok": True, "bucket": "b", "key": "jsonl/x.jsonl"}
        )

    result = s3_ingest_client.put_object(
        "analytics",
        "2026/07/25/10/x.jsonl",
        b'{"a":1}\n',
        "application/jsonlines",
        client=_client(handler),
    )

    assert result == {"ok": True, "bucket": "b", "key": "jsonl/x.jsonl"}
    assert captured["headers"]["x-ingest-secret"] == "unit-secret"
    assert captured["headers"]["x-ingest-target"] == "analytics"
    assert captured["headers"]["x-ingest-key"] == "2026/07/25/10/x.jsonl"
    assert captured["headers"]["content-type"] == "application/jsonlines"
    assert captured["body"] == b'{"a":1}\n'


def test_put_object_returns_none_without_configuration(monkeypatch):
    monkeypatch.delenv("S3_INGEST_URL", raising=False)
    monkeypatch.delenv("S3_INGEST_SECRET", raising=False)
    assert (
        s3_ingest_client.put_object(
            "analytics", "x.jsonl", b"{}", "application/jsonlines"
        )
        is None
    )


def test_put_object_retries_once_on_5xx_then_succeeds(monkeypatch):
    monkeypatch.setenv("S3_INGEST_URL", "https://ingest.example.test/internal/s3-put")
    monkeypatch.setenv("S3_INGEST_SECRET", "unit-secret")

    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(503)
        return httpx.Response(200, json={"ok": True})

    result = s3_ingest_client.put_object(
        "analytics", "x.jsonl", b"{}", "application/jsonlines", client=_client(handler)
    )

    assert result == {"ok": True}
    assert len(calls) == 2


def test_put_object_returns_none_after_two_5xx_and_never_logs_secret(monkeypatch):
    monkeypatch.setenv("S3_INGEST_URL", "https://ingest.example.test/internal/s3-put")
    monkeypatch.setenv("S3_INGEST_SECRET", "unit-super-secret")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    messages = []
    sink_id = logger.add(messages.append, format="{message}")
    try:
        result = s3_ingest_client.put_object(
            "analytics",
            "x.jsonl",
            b"{}",
            "application/jsonlines",
            client=_client(handler),
        )
    finally:
        logger.remove(sink_id)

    assert result is None
    joined = "\n".join(messages)
    assert "unit-super-secret" not in joined


def test_put_object_returns_none_on_4xx_without_retry(monkeypatch):
    monkeypatch.setenv("S3_INGEST_URL", "https://ingest.example.test/internal/s3-put")
    monkeypatch.setenv("S3_INGEST_SECRET", "unit-secret")

    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(401)

    result = s3_ingest_client.put_object(
        "analytics", "x.jsonl", b"{}", "application/jsonlines", client=_client(handler)
    )

    assert result is None
    assert len(calls) == 1
