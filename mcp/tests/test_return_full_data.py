import json

import av_api.client as client
import av_mcp.common as common
from av_api.registry import call_tool, ensure_tools_loaded, get_tool_schema


class FakeResponse:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        pass


class FakeClient:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, url, params):
        if params["function"] == "EARNINGS":
            payload = {
                "symbol": params["symbol"],
                "quarterlyEarnings": [
                    {"fiscalDateEnding": f"2026-{index:02d}-01", "reportedEPS": "1.23"}
                    for index in range(1, 122)
                ],
            }
        else:
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


def test_return_full_data_is_added_to_tool_schema():
    ensure_tools_loaded()

    parameters = get_tool_schema("EARNINGS")["parameters"]

    assert parameters["properties"]["return_full_data"]["type"] == "boolean"
    assert "return_full_data" not in parameters["required"]


def test_default_cap_allows_earnings_without_preview(monkeypatch):
    monkeypatch.setattr(client, "_http_client", FakeClient())
    ensure_tools_loaded()

    result = call_tool("EARNINGS", {"symbol": "AAPL"})

    assert result.get("preview") is None
    assert len(result["quarterlyEarnings"]) == 121


def test_large_response_previews_unless_return_full_data(monkeypatch):
    monkeypatch.setattr(client, "_http_client", FakeClient())
    monkeypatch.setattr(common, "upload_to_object_storage", lambda text, datatype: "data:application/json;base64,stub")
    ensure_tools_loaded()

    preview = call_tool(
        "TIME_SERIES_DAILY",
        {"symbol": "MSFT", "outputsize": "full", "datatype": "json"},
    )
    full_data = call_tool(
        "TIME_SERIES_DAILY",
        {"symbol": "MSFT", "outputsize": "full", "datatype": "json", "return_full_data": True},
    )

    assert preview["preview"] is True
    assert preview["data_url"] == "data:application/json;base64,stub"
    assert len(full_data["Time Series (Daily)"]) == 5000
    assert client._current_return_full_data is False
