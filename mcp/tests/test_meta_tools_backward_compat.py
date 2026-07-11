"""Regression guard for todo 2764: TOOL_LIST/TOOL_GET/TOOL_CALL meta-tools are additively
restored alongside the flat tool catalog (both transports), for backward compatibility
with historical clients that still have the meta-tools cached.
"""
import json
import sys
from pathlib import Path

import jsonschema
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import av_api.client as client  # noqa: E402
from av_api.registry import call_tool as api_call_tool, get_tool_schema  # noqa: E402
from av_mcp.decorators import setup_custom_tool_decorator  # noqa: E402
from av_mcp.stdio_server import META_TOOLS, StdioMCPServer, build_tools  # noqa: E402
from av_mcp.tools.meta_tools import (  # noqa: E402
    META_TOOL_OPEN_WORLD_HINT,
    META_TOOL_OUTPUT_SCHEMA,
    build_structured_content,
    tool_call,
    tool_get,
    tool_list,
)
from av_mcp.tools.registry import register_all_tools, register_meta_tools  # noqa: E402
from lambda_function import _meta_tool_structured  # noqa: E402


class _FakeResponse:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        pass


class _FakeClient:
    """Returns a fixed GLOBAL_QUOTE payload, no real network calls."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, url, params):
        payload = {
            "Global Quote": {"01. symbol": params["symbol"], "05. price": "261.05"}
        }
        return _FakeResponse(json.dumps(payload))


class _FakeMCP:
    def __init__(self):
        self.tools = {}
        self.tool_implementations = {}


def _register_lambda_tools_with_meta():
    mcp = _FakeMCP()
    setup_custom_tool_decorator(mcp)
    register_all_tools(mcp)
    register_meta_tools(mcp)
    return mcp


# --- Both transports list flat tools AND meta-tools together --------------------------


def test_stdio_lists_flat_tools_and_meta_tools_together():
    server = StdioMCPServer(api_key="demo")
    names = {tool.name for tool in server.tools}

    assert {"TOOL_LIST", "TOOL_GET", "TOOL_CALL"} <= names
    assert "TIME_SERIES_DAILY" in names
    assert "GLOBAL_QUOTE" in names
    # Flat catalog is unchanged: still the full ~100+ real tools, plus exactly 3 meta-tools.
    assert len(server.tools) == len(build_tools()) + 3


def test_lambda_registers_flat_tools_and_meta_tools_together():
    mcp = _register_lambda_tools_with_meta()

    assert {"TOOL_LIST", "TOOL_GET", "TOOL_CALL"} <= set(mcp.tools)
    assert "TIME_SERIES_DAILY" in mcp.tools
    assert "GLOBAL_QUOTE" in mcp.tools
    assert callable(mcp.tool_implementations["TOOL_LIST"])
    assert callable(mcp.tool_implementations["TIME_SERIES_DAILY"])


# --- Meta-tool annotations --------------------------------------------------------------


@pytest.mark.parametrize("name", ["TOOL_LIST", "TOOL_GET", "TOOL_CALL"])
def test_stdio_meta_tool_annotations(name):
    tool = next(t for t in META_TOOLS if t.name == name)
    ann = tool.annotations.model_dump()
    assert ann["readOnlyHint"] is True
    assert ann["destructiveHint"] is False
    assert ann["openWorldHint"] is META_TOOL_OPEN_WORLD_HINT[name]
    jsonschema.Draft7Validator.check_schema(tool.outputSchema)


@pytest.mark.parametrize("name", ["TOOL_LIST", "TOOL_GET", "TOOL_CALL"])
def test_lambda_meta_tool_annotations(name):
    mcp = _register_lambda_tools_with_meta()
    schema = mcp.tools[name]
    ann = schema["annotations"]
    assert ann["readOnlyHint"] is True
    assert ann["destructiveHint"] is False
    assert ann["openWorldHint"] is META_TOOL_OPEN_WORLD_HINT[name]
    jsonschema.Draft7Validator.check_schema(schema["outputSchema"])


# --- Meta-tool functional behavior: proxy to the same underlying registry -------------


def test_tool_list_matches_flat_catalog():
    listed = tool_list()
    names = {entry["name"] for entry in listed}
    assert "TIME_SERIES_DAILY" in names
    assert len(listed) == len(build_tools())


def test_tool_get_single_name_matches_registry_schema():
    result = tool_get("TIME_SERIES_DAILY")
    assert result == get_tool_schema("TIME_SERIES_DAILY")


def test_tool_get_list_of_names_returns_multiple_schemas():
    result = tool_get(["TIME_SERIES_DAILY", "GLOBAL_QUOTE"])
    assert [r["name"] for r in result] == ["TIME_SERIES_DAILY", "GLOBAL_QUOTE"]


def test_tool_call_proxies_to_same_underlying_tool(monkeypatch):
    monkeypatch.setattr(client.httpx, "Client", _FakeClient)

    direct = api_call_tool("GLOBAL_QUOTE", {"symbol": "AAPL"})
    proxied = tool_call("GLOBAL_QUOTE", {"symbol": "AAPL"})
    # tool_call JSON-serializes dict results to avoid Python repr output.
    expected = json.dumps(direct, indent=2) if isinstance(direct, dict) else direct
    assert proxied == expected


def test_tool_call_unknown_tool_raises():
    with pytest.raises(ValueError):
        tool_call("NOT_A_REAL_TOOL", {})


# --- structuredContent shape matches each meta-tool's declared outputSchema -----------


def test_build_structured_content_tool_list_validates():
    structured = build_structured_content("TOOL_LIST", tool_list())
    jsonschema.validate(instance=structured, schema=META_TOOL_OUTPUT_SCHEMA["TOOL_LIST"])


def test_build_structured_content_tool_get_validates():
    structured = build_structured_content("TOOL_GET", tool_get("GLOBAL_QUOTE"))
    jsonschema.validate(instance=structured, schema=META_TOOL_OUTPUT_SCHEMA["TOOL_GET"])


def test_build_structured_content_tool_call_validates():
    structured = build_structured_content("TOOL_CALL", '{"Global Quote": {"price": "1.0"}}')
    jsonschema.validate(instance=structured, schema=META_TOOL_OUTPUT_SCHEMA["TOOL_CALL"])
    assert structured == {"result": {"Global Quote": {"price": "1.0"}}}


# --- Lambda structuredContent injector dispatches meta-tools by name ------------------


def test_lambda_meta_tool_structured_tool_list():
    structured = _meta_tool_structured("TOOL_LIST", {}, [])
    jsonschema.validate(instance=structured, schema=META_TOOL_OUTPUT_SCHEMA["TOOL_LIST"])


def test_lambda_meta_tool_structured_tool_get():
    structured = _meta_tool_structured("TOOL_GET", {"tool_name": "GLOBAL_QUOTE"}, [])
    jsonschema.validate(instance=structured, schema=META_TOOL_OUTPUT_SCHEMA["TOOL_GET"])
    assert structured["tools"][0]["name"] == "GLOBAL_QUOTE"


def test_lambda_meta_tool_structured_tool_get_missing_arg_returns_none():
    assert _meta_tool_structured("TOOL_GET", {}, []) is None


def test_lambda_meta_tool_structured_tool_call_reads_text_content():
    content = [{"type": "text", "text": '{"Global Quote": {"price": "1.0"}}'}]
    structured = _meta_tool_structured("TOOL_CALL", {}, content)
    jsonschema.validate(instance=structured, schema=META_TOOL_OUTPUT_SCHEMA["TOOL_CALL"])
    assert structured == {"result": {"Global Quote": {"price": "1.0"}}}
