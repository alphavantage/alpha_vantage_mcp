"""Regression guard for Anthropic MCP Connector tool-description compliance.

The connector compliance rule requires that tool descriptions contain no instructions
about model behavior, no references to other tools, and no external-instruction-source
references. These tests assert the forbidden substrings are absent from every description
surfaced to the model: the 3 meta-tool descriptions, the META_TOOLS schemas, and a sample
of data-tool schemas.

Scope is the ``description`` fields only. Example argument VALUES (e.g. "TIME_SERIES_DAILY")
are allowed in parameter descriptions and are intentionally not matched by the forbidden set.
"""
import re

import pytest

from av_api.registry import extract_description, get_tool_schema
from av_mcp.stdio_server import META_TOOLS
from av_mcp.tools.meta_tools import tool_call, tool_get, tool_list

# Case-insensitive forbidden patterns. Note: the META_TOOLS *name* fields are
# "TOOL_LIST"/"TOOL_GET"/"TOOL_CALL"; only the description fields are checked here.
FORBIDDEN_PATTERNS = [
    re.compile(r"important", re.IGNORECASE),
    re.compile(r"you must", re.IGNORECASE),
    re.compile(r"must call", re.IGNORECASE),
    re.compile(r"\bTOOL_(LIST|GET|CALL)\b", re.IGNORECASE),
    re.compile(r"workflow:", re.IGNORECASE),
]

# Sample of data tools whose schema descriptions must also stay compliant.
DATA_TOOL_SAMPLE = [
    "TIME_SERIES_DAILY",
    "TIME_SERIES_INTRADAY",
    "GLOBAL_QUOTE",
    "EARNINGS",
    "COMPANY_OVERVIEW",
    "SMA",
]


def _assert_clean(label: str, text: str):
    for pattern in FORBIDDEN_PATTERNS:
        match = pattern.search(text)
        assert match is None, (
            f"{label} contains forbidden substring {match.group(0)!r}: {text!r}"
        )


def _collect_descriptions(schema: dict) -> list[tuple[str, str]]:
    """Return (label, description) pairs from a tool schema's description fields."""
    descriptions = [(schema["name"], schema["description"])]
    params = schema.get("parameters") or schema.get("inputSchema") or {}
    for prop_name, prop in (params.get("properties") or {}).items():
        if "description" in prop:
            descriptions.append((f"{schema['name']}.{prop_name}", prop["description"]))
        # oneOf / anyOf branches carry their own descriptions
        for branch in prop.get("oneOf", []) + prop.get("anyOf", []):
            if "description" in branch:
                descriptions.append((f"{schema['name']}.{prop_name}", branch["description"]))
    return descriptions


@pytest.mark.parametrize(
    "func", [tool_list, tool_get, tool_call], ids=lambda f: f.__name__
)
def test_meta_tool_extracted_description_is_clean(func):
    _assert_clean(func.__name__, extract_description(func))


def test_meta_tool_schemas_are_clean():
    for tool in META_TOOLS:
        schema = {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.inputSchema,
        }
        for label, text in _collect_descriptions(schema):
            _assert_clean(label, text)


@pytest.mark.parametrize("tool_name", DATA_TOOL_SAMPLE)
def test_data_tool_schema_descriptions_are_clean(tool_name):
    schema = get_tool_schema(tool_name)
    for label, text in _collect_descriptions(schema):
        _assert_clean(label, text)
