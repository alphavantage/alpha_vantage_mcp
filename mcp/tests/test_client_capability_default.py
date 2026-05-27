import json

import av_api.client as client
import av_mcp.common as common
from av_api.context import set_client_name
from av_api.registry import call_tool, ensure_tools_loaded


class FakeResponse:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        pass


class FakeClient:
    """Returns a TIME_SERIES_DAILY payload large enough to trigger the preview path."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, url, params):
        payload = {
            "Meta Data": {"2. Symbol": params["symbol"]},
            "Time Series (Daily)": {
                f"2026-01-{(index % 28) + 1:02d}-{index}": {
                    "1. open": "1",
                    "2. high": "2",
                    "3. low": "0",
                    "4. close": "1",
                    "5. volume": "100",
                }
                for index in range(5000)
            },
        }
        return FakeResponse(json.dumps(payload))


def _install_stubs(monkeypatch):
    monkeypatch.setattr(client.httpx, "Client", FakeClient)
    monkeypatch.setattr(
        common,
        "upload_to_object_storage",
        lambda text, datatype: "data:application/json;base64,stub",
    )
    ensure_tools_loaded()


def _reset_client_name():
    set_client_name(None)


def test_capable_client_default_returns_full_data(monkeypatch):
    _install_stubs(monkeypatch)
    set_client_name("claude-code")
    try:
        result = call_tool(
            "TIME_SERIES_DAILY",
            {"symbol": "MSFT", "outputsize": "full", "datatype": "json"},
        )
        assert "Time Series (Daily)" in result
        assert len(result["Time Series (Daily)"]) == 5000
        assert result.get("preview") is None
    finally:
        _reset_client_name()
        assert client._current_return_full_data is False


def test_capable_client_explicit_false_forces_preview(monkeypatch):
    _install_stubs(monkeypatch)
    set_client_name("claude-code")
    try:
        result = call_tool(
            "TIME_SERIES_DAILY",
            {
                "symbol": "MSFT",
                "outputsize": "full",
                "datatype": "json",
                "return_full_data": False,
            },
        )
        assert result["preview"] is True
    finally:
        _reset_client_name()
        assert client._current_return_full_data is False


def test_unknown_client_default_returns_preview(monkeypatch):
    _install_stubs(monkeypatch)
    set_client_name("cursor")
    try:
        result = call_tool(
            "TIME_SERIES_DAILY",
            {"symbol": "MSFT", "outputsize": "full", "datatype": "json"},
        )
        assert result["preview"] is True
    finally:
        _reset_client_name()


def test_unknown_client_explicit_true_returns_full_data(monkeypatch):
    _install_stubs(monkeypatch)
    set_client_name("cursor")
    try:
        result = call_tool(
            "TIME_SERIES_DAILY",
            {
                "symbol": "MSFT",
                "outputsize": "full",
                "datatype": "json",
                "return_full_data": True,
            },
        )
        assert "Time Series (Daily)" in result
        assert len(result["Time Series (Daily)"]) == 5000
        assert result.get("preview") is None
    finally:
        _reset_client_name()
        assert client._current_return_full_data is False


def test_no_client_name_defaults_to_preview(monkeypatch):
    _install_stubs(monkeypatch)
    _reset_client_name()
    result = call_tool(
        "TIME_SERIES_DAILY",
        {"symbol": "MSFT", "outputsize": "full", "datatype": "json"},
    )
    assert result["preview"] is True


def test_clientinfo_name_with_space_matches_claude_substring(monkeypatch):
    _install_stubs(monkeypatch)
    set_client_name("Claude Code")
    try:
        result = call_tool(
            "TIME_SERIES_DAILY",
            {"symbol": "MSFT", "outputsize": "full", "datatype": "json"},
        )
        assert result.get("preview") is None
        assert len(result["Time Series (Daily)"]) == 5000
    finally:
        _reset_client_name()


def test_unknown_claude_variant_still_treated_as_capable(monkeypatch):
    _install_stubs(monkeypatch)
    set_client_name("claude-desktop-v3.1")
    try:
        result = call_tool(
            "TIME_SERIES_DAILY",
            {"symbol": "MSFT", "outputsize": "full", "datatype": "json"},
        )
        assert result.get("preview") is None
        assert len(result["Time Series (Daily)"]) == 5000
    finally:
        _reset_client_name()
