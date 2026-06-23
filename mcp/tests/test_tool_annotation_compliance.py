"""Regression guard for Anthropic MCP Connector tool-annotation (behavior hint) compliance.

The connector compliance rule requires every surfaced tool to carry the three behavior
hints: readOnlyHint, destructiveHint, openWorldHint. These tests assert the hints are
present and correct on the meta-tools that the server lists (TOOL_LIST/TOOL_GET/TOOL_CALL,
both the stdio META_TOOLS and the Lambda registration path) and on the data-tool catalog
surfaced via TOOL_GET.

Semantics:
- readOnlyHint=True / destructiveHint=False for all tools here (none modify data).
- openWorldHint=False for TOOL_LIST/TOOL_GET (in-process registry reads only).
- openWorldHint=True for TOOL_CALL and every data tool (fetch over the public internet).
"""
import pytest

from av_api.registry import DATA_TOOL_ANNOTATIONS, get_tool_schema, get_tool_schemas
from av_mcp.stdio_server import META_TOOLS
from av_mcp.tools.meta_tools import META_TOOL_OPEN_WORLD_HINT
from av_mcp.tools.registry import register_meta_tools

DATA_TOOL_SAMPLE = [
    "TIME_SERIES_DAILY",
    "TIME_SERIES_INTRADAY",
    "GLOBAL_QUOTE",
    "EARNINGS",
    "COMPANY_OVERVIEW",
    "SMA",
]


def _assert_hints(label, annotations, *, open_world):
    for field in ("readOnlyHint", "destructiveHint", "openWorldHint"):
        assert field in annotations, f"{label} missing {field}"
    assert annotations["readOnlyHint"] is True, f"{label} readOnlyHint should be True"
    assert annotations["destructiveHint"] is False, f"{label} destructiveHint should be False"
    assert annotations["openWorldHint"] is open_world, (
        f"{label} openWorldHint should be {open_world}"
    )


@pytest.mark.parametrize("tool", META_TOOLS, ids=lambda t: t.name)
def test_stdio_meta_tool_annotations(tool):
    ann = tool.annotations
    assert ann is not None, f"{tool.name} has no annotations"
    _assert_hints(
        tool.name,
        ann.model_dump(),
        open_world=META_TOOL_OPEN_WORLD_HINT[tool.name],
    )


def test_lambda_meta_tool_annotations():
    class _FakeMCP:
        def __init__(self):
            self.tools = {}
            self.tool_implementations = {}

    from av_mcp.decorators import setup_custom_tool_decorator

    mcp = _FakeMCP()
    setup_custom_tool_decorator(mcp)
    register_meta_tools(mcp)

    for name in ("TOOL_LIST", "TOOL_GET", "TOOL_CALL"):
        schema = mcp.tools[name]
        assert "annotations" in schema, f"{name} missing annotations"
        _assert_hints(
            name,
            schema["annotations"],
            open_world=META_TOOL_OPEN_WORLD_HINT[name],
        )


@pytest.mark.parametrize("tool_name", DATA_TOOL_SAMPLE)
def test_data_tool_schema_annotations(tool_name):
    schema = get_tool_schema(tool_name)
    assert "annotations" in schema, f"{tool_name} missing annotations"
    _assert_hints(tool_name, schema["annotations"], open_world=True)


def test_data_tool_schemas_batch_annotations():
    for schema in get_tool_schemas(DATA_TOOL_SAMPLE):
        _assert_hints(schema["name"], schema["annotations"], open_world=True)


def test_data_tool_annotations_constant():
    _assert_hints("DATA_TOOL_ANNOTATIONS", DATA_TOOL_ANNOTATIONS, open_world=True)
