import json

from av_mcp import common


def test_none_upload_sets_a_non_empty_error_instead_of_looking_healthy(monkeypatch):
    monkeypatch.setattr(common, "is_upload_configured", lambda: True)
    monkeypatch.setattr(common, "upload_to_object_storage", lambda *_a, **_k: None)

    preview = common._server_response_processor(
        json.dumps({"a": 1}), "json", estimated_tokens=100_000
    )

    assert preview.get("data_url") is None
    assert preview.get("error")


def test_raising_upload_still_sets_error(monkeypatch):
    def _raise(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(common, "is_upload_configured", lambda: True)
    monkeypatch.setattr(common, "upload_to_object_storage", _raise)

    preview = common._server_response_processor(
        json.dumps({"a": 1}), "json", estimated_tokens=100_000
    )

    assert preview.get("data_url") is None
    assert "boom" in preview.get("error", "")


def test_successful_upload_sets_data_url_without_error(monkeypatch):
    monkeypatch.setattr(common, "is_upload_configured", lambda: True)
    monkeypatch.setattr(
        common,
        "upload_to_object_storage",
        lambda *_a, **_k: "https://cdn.example.test/x.json",
    )

    preview = common._server_response_processor(
        json.dumps({"a": 1}), "json", estimated_tokens=100_000
    )

    assert preview["data_url"] == "https://cdn.example.test/x.json"
    assert "error" not in preview


def test_unconfigured_upload_returns_friendly_preview_without_error(monkeypatch):
    """Pins the stdio / no-CDN path (stdio_server.py imports av_mcp.common, and
    CDN_BUCKET_NAME/CDN_DOMAIN are never set there): a null data_url is the normal,
    expected outcome, not a failure, and return_full_data still works, so the
    original friendly message must survive (todo 2842)."""
    monkeypatch.setattr(common, "is_upload_configured", lambda: False)

    def _fail_if_called(*_a, **_k):
        raise AssertionError(
            "upload_to_object_storage should not be called when unconfigured"
        )

    monkeypatch.setattr(common, "upload_to_object_storage", _fail_if_called)

    preview = common._server_response_processor(
        json.dumps({"a": 1}), "json", estimated_tokens=100_000
    )

    assert preview["data_url"] is None
    assert "error" not in preview
    assert "return_full_data=true" in preview["message"]
