"""Regression guard for Anthropic MCP Connector tool-annotation (behavior hint) compliance.

The connector compliance rule requires every surfaced tool to carry the three behavior
hints: readOnlyHint, destructiveHint, openWorldHint. These tests assert the hints (plus a
valid outputSchema and a human-readable title) are present and correct on the real Alpha
Vantage data tools that the server lists, in both the stdio (build_tools / handle_list_tools)
and Lambda (register_all_tools) registration paths.

Semantics for every data tool: readOnlyHint=True, destructiveHint=False, openWorldHint=False
(they are read-only and never modify user data).
"""
import jsonschema
import pytest

from av_api.registry import (
    DATA_TOOL_ANNOTATIONS,
    DATA_TOOL_OUTPUT_SCHEMA,
    build_data_structured_content,
    derive_tool_title,
)
from av_mcp.decorators import setup_custom_tool_decorator
from av_mcp.stdio_server import build_tools
from av_mcp.tools.registry import register_all_tools

# A representative sample that must appear in the listed tools.
DATA_TOOL_SAMPLE = [
    "TIME_SERIES_DAILY",
    "TIME_SERIES_INTRADAY",
    "GLOBAL_QUOTE",
    "EARNINGS",
    "COMPANY_OVERVIEW",
    "SMA",
]


class _FakeMCP:
    def __init__(self):
        self.tools = {}
        self.tool_implementations = {}


def _register_lambda_tools():
    mcp = _FakeMCP()
    setup_custom_tool_decorator(mcp)
    register_all_tools(mcp)
    return mcp.tools


STDIO_TOOLS = {tool.name: tool for tool in build_tools()}
LAMBDA_TOOLS = _register_lambda_tools()


def _assert_hints(label, annotations):
    for field in ("readOnlyHint", "destructiveHint", "openWorldHint"):
        assert field in annotations, f"{label} missing {field}"
    assert annotations["readOnlyHint"] is True, f"{label} readOnlyHint should be True"
    assert annotations["destructiveHint"] is False, f"{label} destructiveHint should be False"
    assert annotations["openWorldHint"] is False, f"{label} openWorldHint should be False"


def test_data_tool_annotations_constant():
    _assert_hints("DATA_TOOL_ANNOTATIONS", DATA_TOOL_ANNOTATIONS)


def test_full_catalog_is_listed():
    """Both transports surface the same real-tool catalog (well past the 3 old meta-tools)."""
    assert len(STDIO_TOOLS) > 50
    assert set(STDIO_TOOLS) == set(LAMBDA_TOOLS)
    for name in DATA_TOOL_SAMPLE:
        assert name in STDIO_TOOLS, f"{name} missing from stdio tools"
        assert name in LAMBDA_TOOLS, f"{name} missing from lambda tools"


@pytest.mark.parametrize("name", DATA_TOOL_SAMPLE)
def test_stdio_data_tool_annotations(name):
    tool = STDIO_TOOLS[name]
    assert tool.annotations is not None, f"{name} has no annotations"
    ann = tool.annotations.model_dump()
    _assert_hints(name, ann)
    assert ann["title"] == derive_tool_title(name), f"{name} title mismatch"


@pytest.mark.parametrize("name", DATA_TOOL_SAMPLE)
def test_lambda_data_tool_annotations(name):
    schema = LAMBDA_TOOLS[name]
    assert "annotations" in schema, f"{name} missing annotations"
    _assert_hints(name, schema["annotations"])
    assert schema["annotations"]["title"] == derive_tool_title(name), f"{name} title mismatch"


def test_every_stdio_tool_has_hints_and_output_schema():
    for name, tool in STDIO_TOOLS.items():
        assert tool.annotations is not None, f"{name} has no annotations"
        _assert_hints(name, tool.annotations.model_dump())
        assert tool.outputSchema == DATA_TOOL_OUTPUT_SCHEMA, f"{name} wrong outputSchema"
        jsonschema.Draft7Validator.check_schema(tool.outputSchema)


def test_every_lambda_tool_has_hints_and_output_schema():
    for name, schema in LAMBDA_TOOLS.items():
        assert "annotations" in schema, f"{name} missing annotations"
        _assert_hints(name, schema["annotations"])
        assert schema.get("outputSchema") == DATA_TOOL_OUTPUT_SCHEMA, f"{name} wrong outputSchema"
        jsonschema.Draft7Validator.check_schema(schema["outputSchema"])


@pytest.mark.parametrize(
    "raw",
    [
        {"Global Quote": {"price": "1.0"}},
        '{"Global Quote": {"price": "1.0"}}',
        "plain non-json csv,preview",
        ["a", "b"],
        42,
        {"preview": True, "data_url": "data:..."},
    ],
)
def test_structured_content_validates_against_output_schema(raw):
    """structuredContent built from any data-tool result validates against the schema."""
    structured = build_data_structured_content(raw)
    jsonschema.validate(instance=structured, schema=DATA_TOOL_OUTPUT_SCHEMA)
