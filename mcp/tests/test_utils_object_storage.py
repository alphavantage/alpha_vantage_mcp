import sys

import httpx

from av_mcp import utils


def _clear_env(monkeypatch):
    monkeypatch.delenv("S3_INGEST_URL", raising=False)
    monkeypatch.delenv("S3_INGEST_SECRET", raising=False)
    monkeypatch.delenv("CDN_BUCKET_NAME", raising=False)
    monkeypatch.delenv("CDN_DOMAIN", raising=False)


def test_upload_via_proxy_returns_server_public_url_and_never_touches_boto3(
    monkeypatch,
):
    _clear_env(monkeypatch)
    monkeypatch.setenv("S3_INGEST_URL", "https://ingest.example.test/internal/s3-put")
    monkeypatch.setenv("S3_INGEST_SECRET", "unit-secret")
    monkeypatch.setitem(sys.modules, "boto3", None)  # importing boto3 would now raise

    captured = {}
    real_client_class = httpx.Client

    def handler(request: httpx.Request) -> httpx.Response:
        captured["headers"] = request.headers
        captured["body"] = request.content
        return httpx.Response(
            200,
            json={
                "ok": True,
                "bucket": "cdn-bucket",
                "key": "mcp-responses/123-abcd.json",
                "public_url": "https://cdn.example.test/mcp-responses/123-abcd.json",
            },
        )

    monkeypatch.setattr(
        "av_mcp.s3_ingest_client.httpx.Client",
        lambda **_kwargs: real_client_class(transport=httpx.MockTransport(handler)),
    )

    url = utils.upload_to_object_storage('{"a": 1}', datatype="json")

    assert url == "https://cdn.example.test/mcp-responses/123-abcd.json"
    assert captured["headers"]["x-ingest-target"] == "cdn"
    assert captured["headers"]["x-ingest-key"].endswith(".json")
    assert not captured["headers"]["x-ingest-key"].startswith("mcp-responses/")
    assert captured["body"] == b'{"a": 1}'


def test_upload_via_proxy_returns_none_when_proxy_fails(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("S3_INGEST_URL", "https://ingest.example.test/internal/s3-put")
    monkeypatch.setenv("S3_INGEST_SECRET", "unit-secret")

    real_client_class = httpx.Client

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    monkeypatch.setattr(
        "av_mcp.s3_ingest_client.httpx.Client",
        lambda **_kwargs: real_client_class(transport=httpx.MockTransport(handler)),
    )

    assert utils.upload_to_object_storage('{"a": 1}', datatype="json") is None


def test_upload_direct_produces_expected_key_and_url(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("CDN_BUCKET_NAME", "unit-cdn-bucket")
    monkeypatch.setenv("CDN_DOMAIN", "cdn.example.test")

    calls = []

    class FakeS3Client:
        def put_object(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setattr("boto3.client", lambda *a, **k: FakeS3Client())

    url = utils.upload_to_object_storage('{"a": 1}', datatype="json")

    assert len(calls) == 1
    call = calls[0]
    assert call["Bucket"] == "unit-cdn-bucket"
    assert call["Key"].startswith("mcp-responses/")
    assert call["Key"].endswith(".json")
    assert call["Tagging"] == "AutoDelete=true"
    assert url == f"https://cdn.example.test/{call['Key']}"


def test_upload_direct_returns_none_without_configuration(monkeypatch):
    _clear_env(monkeypatch)
    assert utils.upload_to_object_storage('{"a": 1}', datatype="json") is None


def test_is_upload_configured_false_with_nothing_set(monkeypatch):
    _clear_env(monkeypatch)
    assert utils.is_upload_configured() is False


def test_is_upload_configured_true_via_proxy(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("S3_INGEST_URL", "https://ingest.example.test/internal/s3-put")
    monkeypatch.setenv("S3_INGEST_SECRET", "unit-secret")
    assert utils.is_upload_configured() is True


def test_is_upload_configured_true_via_direct_cdn_vars(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("CDN_BUCKET_NAME", "unit-cdn-bucket")
    monkeypatch.setenv("CDN_DOMAIN", "cdn.example.test")
    assert utils.is_upload_configured() is True
