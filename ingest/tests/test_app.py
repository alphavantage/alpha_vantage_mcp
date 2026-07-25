import base64
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app  # noqa: E402


class FakeS3Client:
    def __init__(self, raise_on_put=None):
        self.calls = []
        self._raise_on_put = raise_on_put

    def put_object(self, **kwargs):
        if self._raise_on_put is not None:
            raise self._raise_on_put
        self.calls.append(kwargs)


@pytest.fixture(autouse=True)
def _reset_s3_client(monkeypatch):
    monkeypatch.setattr(app, "_s3_client", None)
    yield
    monkeypatch.setattr(app, "_s3_client", None)


def _event(method="POST", headers=None, body="", is_base64=False):
    return {
        "httpMethod": method,
        "headers": headers or {},
        "body": body,
        "isBase64Encoded": is_base64,
    }


def _configure(
    monkeypatch,
    secret="unit-secret",
    analytics_bucket="unit-analytics",
    cdn_bucket="unit-cdn",
    cdn_domain="cdn.example.test",
):
    monkeypatch.setenv("S3_INGEST_SECRET", secret)
    monkeypatch.setenv("ANALYTICS_LOGS_BUCKET", analytics_bucket)
    monkeypatch.setenv("CDN_BUCKET_NAME", cdn_bucket)
    monkeypatch.setenv("CDN_DOMAIN", cdn_domain)


def test_rejects_non_post_with_405(monkeypatch):
    _configure(monkeypatch)
    result = app.lambda_handler(_event(method="GET"), None)
    assert result["statusCode"] == 405


def test_rejects_when_secret_not_configured_with_503(monkeypatch):
    monkeypatch.delenv("S3_INGEST_SECRET", raising=False)
    result = app.lambda_handler(_event(headers={"X-Ingest-Secret": "anything"}), None)
    assert result["statusCode"] == 503


def test_rejects_bad_secret_with_401(monkeypatch):
    _configure(monkeypatch)
    result = app.lambda_handler(
        _event(headers={"X-Ingest-Secret": "wrong", "X-Ingest-Target": "analytics"}),
        None,
    )
    assert result["statusCode"] == 401


def test_rejects_non_ascii_secret_with_401_not_500(monkeypatch):
    # hmac.compare_digest raises TypeError on a str argument with non-ASCII
    # characters; a correct fix compares encoded bytes so this still yields a
    # clean 401 instead of an unhandled exception.
    _configure(monkeypatch)
    result = app.lambda_handler(
        _event(headers={"X-Ingest-Secret": "héllo", "X-Ingest-Target": "analytics"}),
        None,
    )
    assert result["statusCode"] == 401


def test_rejects_unknown_target_with_400(monkeypatch):
    _configure(monkeypatch)
    result = app.lambda_handler(
        _event(headers={"X-Ingest-Secret": "unit-secret", "X-Ingest-Target": "bogus"}),
        None,
    )
    assert result["statusCode"] == 400


@pytest.mark.parametrize("suffix", ["../etc/passwd", "/leading", "a//b", "x" * 300, ""])
def test_rejects_bad_suffix_with_400(monkeypatch, suffix):
    _configure(monkeypatch)
    result = app.lambda_handler(
        _event(
            headers={
                "X-Ingest-Secret": "unit-secret",
                "X-Ingest-Target": "analytics",
                "X-Ingest-Key": suffix,
            }
        ),
        None,
    )
    assert result["statusCode"] == 400


def test_rejects_bad_content_type_with_400(monkeypatch):
    _configure(monkeypatch)
    result = app.lambda_handler(
        _event(
            headers={
                "X-Ingest-Secret": "unit-secret",
                "X-Ingest-Target": "analytics",
                "X-Ingest-Key": "2026/07/25/10/x.jsonl",
                "Content-Type": "text/plain",
            }
        ),
        None,
    )
    assert result["statusCode"] == 400


def test_rejects_oversize_body_with_413(monkeypatch):
    _configure(monkeypatch)
    oversized = "a" * (app.MAX_BODY_BYTES + 1)
    result = app.lambda_handler(
        _event(
            headers={
                "X-Ingest-Secret": "unit-secret",
                "X-Ingest-Target": "analytics",
                "X-Ingest-Key": "2026/07/25/10/x.jsonl",
                "Content-Type": "application/jsonlines",
            },
            body=oversized,
        ),
        None,
    )
    assert result["statusCode"] == 413


def test_rejects_when_target_bucket_not_configured_with_503(monkeypatch):
    _configure(monkeypatch, analytics_bucket="")
    result = app.lambda_handler(
        _event(
            headers={
                "X-Ingest-Secret": "unit-secret",
                "X-Ingest-Target": "analytics",
                "X-Ingest-Key": "2026/07/25/10/x.jsonl",
                "Content-Type": "application/jsonlines",
            },
            body="{}\n",
        ),
        None,
    )
    assert result["statusCode"] == 503


def test_analytics_happy_path_puts_object_without_tagging(monkeypatch):
    _configure(monkeypatch)
    fake_client = FakeS3Client()
    monkeypatch.setattr(app, "_s3", lambda: fake_client)

    result = app.lambda_handler(
        _event(
            headers={
                "X-Ingest-Secret": "unit-secret",
                "X-Ingest-Target": "analytics",
                "X-Ingest-Key": "2026/07/25/10/x.jsonl",
                "Content-Type": "application/jsonlines",
            },
            body='{"method": "tools/call"}\n',
        ),
        None,
    )

    assert result["statusCode"] == 200
    payload = json.loads(result["body"])
    assert payload["ok"] is True
    assert payload["bucket"] == "unit-analytics"
    assert payload["key"] == "jsonl/2026/07/25/10/x.jsonl"
    assert "public_url" not in payload

    assert len(fake_client.calls) == 1
    call = fake_client.calls[0]
    assert call["Bucket"] == "unit-analytics"
    assert call["Key"] == "jsonl/2026/07/25/10/x.jsonl"
    assert call["Body"] == b'{"method": "tools/call"}\n'
    assert call["ContentType"] == "application/jsonlines"
    assert "Tagging" not in call


def test_cdn_happy_path_puts_object_with_tagging_and_returns_public_url(monkeypatch):
    _configure(monkeypatch)
    fake_client = FakeS3Client()
    monkeypatch.setattr(app, "_s3", lambda: fake_client)

    body_bytes = b'{"preview": true}'
    result = app.lambda_handler(
        _event(
            headers={
                "X-Ingest-Secret": "unit-secret",
                "X-Ingest-Target": "cdn",
                "X-Ingest-Key": "1234-abcd.json",
                "Content-Type": "application/json",
            },
            body=base64.b64encode(body_bytes).decode(),
            is_base64=True,
        ),
        None,
    )

    assert result["statusCode"] == 200
    payload = json.loads(result["body"])
    assert payload["ok"] is True
    assert payload["bucket"] == "unit-cdn"
    assert payload["key"] == "mcp-responses/1234-abcd.json"
    assert (
        payload["public_url"] == "https://cdn.example.test/mcp-responses/1234-abcd.json"
    )

    assert len(fake_client.calls) == 1
    call = fake_client.calls[0]
    assert call["Bucket"] == "unit-cdn"
    assert call["Key"] == "mcp-responses/1234-abcd.json"
    assert call["Body"] == body_bytes
    assert call["ContentType"] == "application/json"
    assert call["Tagging"] == "AutoDelete=true"
    assert call["CacheControl"] == "public, max-age=3600"
    assert "created" in call["Metadata"]


def test_put_object_failure_returns_500(monkeypatch):
    _configure(monkeypatch)
    fake_client = FakeS3Client(raise_on_put=RuntimeError("boom"))
    monkeypatch.setattr(app, "_s3", lambda: fake_client)

    result = app.lambda_handler(
        _event(
            headers={
                "X-Ingest-Secret": "unit-secret",
                "X-Ingest-Target": "analytics",
                "X-Ingest-Key": "2026/07/25/10/x.jsonl",
                "Content-Type": "application/jsonlines",
            },
            body="{}\n",
        ),
        None,
    )
    assert result["statusCode"] == 500
