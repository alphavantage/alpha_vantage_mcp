import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import av_api.client as client  # noqa: E402
import av_mcp.common as common  # noqa: E402
from awslabs.mcp_lambda_handler import MCPLambdaHandler  # noqa: E402
from av_mcp.decorators import setup_custom_tool_decorator  # noqa: E402
from av_mcp.tools.registry import register_all_tools  # noqa: E402
import lambda_function  # noqa: E402
from lambda_function import (  # noqa: E402
    add_data_tool_structured_content,
    normalize_content_type_header,
    lambda_handler,
)
from av_mcp.utils import cors_headers  # noqa: E402


def test_normalize_content_type_strips_charset_parameter():
    event = {"headers": {"content-type": "application/json; charset=utf-8"}}

    normalize_content_type_header(event)

    assert event["headers"]["content-type"] == "application/json"


def test_normalize_content_type_strips_parameter_without_space():
    event = {"headers": {"content-type": "application/json;charset=utf-8"}}

    normalize_content_type_header(event)

    assert event["headers"]["content-type"] == "application/json"


def test_normalize_content_type_leaves_application_json_unchanged():
    event = {"headers": {"content-type": "application/json"}}

    normalize_content_type_header(event)

    assert event["headers"]["content-type"] == "application/json"


def test_normalize_content_type_handles_case_insensitive_header_key():
    event = {"headers": {"Content-Type": "application/json; charset=utf-8"}}

    normalize_content_type_header(event)

    assert event["headers"]["Content-Type"] == "application/json"
    assert event["headers"]["content-type"] == "application/json"


# --- Lambda dict-result serialization regression (todo 2575) -------------------------
# Data tools return raw dicts. The awslabs handler renders non-bytes results with
# str(result) (Python repr, NOT JSON), so register_all_tools wraps each impl to json.dumps
# dict returns. These tests drive a dict-returning tool through the REAL awslabs render path
# (_convert_result_to_content) + the structuredContent injector — the path _FakeMCP misses.


class _FakeResponse:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        pass


class _FakeClient:
    """Returns a small dict for GLOBAL_QUOTE and a large dict for TIME_SERIES_DAILY."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, url, params):
        if params["function"] == "GLOBAL_QUOTE":
            payload = {
                "Global Quote": {"01. symbol": params["symbol"], "05. price": "261.05", "ok": True}
            }
        else:
            payload = {
                "Meta Data": {"2. Symbol": params["symbol"]},
                "Time Series (Daily)": {
                    f"2026-01-{(index % 28) + 1:02d}-{index}": {
                        "1. open": "1",
                        "4. close": "1",
                        "5. volume": "100",
                    }
                    for index in range(5000)
                },
            }
        return _FakeResponse(json.dumps(payload))


def _run_tool_through_lambda(handler, tool_name, arguments):
    """Invoke a registered impl exactly as the Lambda runtime does, then inject structuredContent."""
    result = handler.tool_implementations[tool_name](**arguments)
    content = handler._convert_result_to_content(result)
    response = {
        "body": json.dumps(
            {"jsonrpc": "2.0", "id": 1, "result": {"content": content}}
        )
    }
    request = {
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }
    add_data_tool_structured_content(request, response)
    return json.loads(response["body"])["result"]


def _build_handler():
    handler = MCPLambdaHandler(name="alphavantage-mcp-server", version="1.0.0")
    setup_custom_tool_decorator(handler)
    register_all_tools(handler)
    return handler


def test_lambda_dict_result_is_valid_json_and_structured(monkeypatch):
    monkeypatch.setattr(client, "_http_client", _FakeClient())
    handler = _build_handler()

    result = _run_tool_through_lambda(handler, "GLOBAL_QUOTE", {"symbol": "AAPL"})

    text = result["content"][0]["text"]
    parsed = json.loads(text)  # must not raise: valid JSON, not Python repr
    expected = {"Global Quote": {"01. symbol": "AAPL", "05. price": "261.05", "ok": True}}
    assert parsed == expected
    assert result["structuredContent"] == expected


def test_lambda_large_preview_result_is_valid_json_and_structured(monkeypatch):
    monkeypatch.setattr(client, "_http_client", _FakeClient())
    monkeypatch.setattr(
        common, "upload_to_object_storage", lambda text, datatype: "data:application/json;base64,stub"
    )
    handler = _build_handler()

    result = _run_tool_through_lambda(
        handler,
        "TIME_SERIES_DAILY",
        {"symbol": "MSFT", "outputsize": "full", "datatype": "json"},
    )

    text = result["content"][0]["text"]
    parsed = json.loads(text)  # the large-response preview dict must serialize as valid JSON
    assert parsed.get("preview") is True
    assert result["structuredContent"] == parsed


# --- CORS at the Lambda boundary (todo 2583) -----------------------------------------
# Browser MCP clients attach `mcp-protocol-version` to every fetch and rely on preflight
# OPTIONS + Access-Control-Allow-Origin on real responses. These cover the central helper,
# the OPTIONS short-circuit, and the per-response CORS merge.


def test_cors_headers_allows_mcp_protocol_version():
    headers = cors_headers()

    assert "mcp-protocol-version" in headers["Access-Control-Allow-Headers"]
    assert headers["Access-Control-Allow-Origin"] == "*"
    assert headers["Access-Control-Allow-Methods"] == "GET, POST, OPTIONS"
    assert headers["Access-Control-Max-Age"] == "86400"


def test_options_preflight_short_circuits_before_handlers(monkeypatch):
    def _boom(event):
        raise AssertionError("OPTIONS must not reach the token handler")

    monkeypatch.setattr(lambda_function, "handle_token_request", _boom)

    response = lambda_handler({"httpMethod": "OPTIONS", "path": "/token"}, None)

    assert response["statusCode"] == 204
    assert response["headers"] == cors_headers()


def test_token_response_carries_cors_headers(monkeypatch):
    monkeypatch.setattr(
        lambda_function,
        "handle_token_request",
        lambda event: {"statusCode": 200, "headers": {}, "body": "{}"},
    )

    response = lambda_handler({"httpMethod": "POST", "path": "/token"}, None)

    assert response["statusCode"] == 200
    assert response["headers"]["Access-Control-Allow-Origin"] == "*"
    assert "mcp-protocol-version" in response["headers"]["Access-Control-Allow-Headers"]


def test_mcp_post_response_carries_cors_headers(monkeypatch):
    class _FakeMCP:
        def handle_request(self, event, context):
            return {"statusCode": 200, "headers": {}, "body": "{}"}

    monkeypatch.setattr(lambda_function, "_mcp_handler", _FakeMCP())

    event = {
        "httpMethod": "POST",
        "path": "/mcp",
        "queryStringParameters": {"apikey": "demo"},
        "body": "{}",
    }
    response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    assert response["headers"]["Access-Control-Allow-Origin"] == "*"


def test_cors_merge_does_not_clobber_stricter_origin(monkeypatch):
    monkeypatch.setattr(
        lambda_function,
        "handle_metadata_discovery",
        lambda event: {
            "statusCode": 200,
            "headers": {"Access-Control-Allow-Origin": "https://example.com"},
            "body": "{}",
        },
    )

    response = lambda_handler(
        {"httpMethod": "GET", "path": "/.well-known/oauth-authorization-server"}, None
    )

    # setdefault keeps the handler's stricter value, still fills the rest.
    assert response["headers"]["Access-Control-Allow-Origin"] == "https://example.com"
    assert "mcp-protocol-version" in response["headers"]["Access-Control-Allow-Headers"]
