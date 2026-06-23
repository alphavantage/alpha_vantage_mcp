"""Regression guard for Anthropic MCP Connector tool-description compliance.

The connector compliance rule requires that tool descriptions contain no instructions
about model behavior, no references to other tools, and no external-instruction-source
references. These tests assert the forbidden substrings are absent from every description
surfaced to the model: the real Alpha Vantage tool list (stdio build_tools) and a sample of
data-tool schemas.

Scope is the ``description`` fields only. Example argument VALUES (e.g. "TIME_SERIES_DAILY")
are allowed in parameter descriptions and are intentionally not matched by the forbidden set.
"""
import re

import pytest

from av_api.registry import get_tool_schema
from av_mcp.stdio_server import build_tools

# Case-insensitive forbidden patterns.
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


def test_listed_tool_descriptions_are_clean():
    """Every real tool surfaced over stdio has compliant descriptions."""
    tools = build_tools()
    assert len(tools) > 50
    for tool in tools:
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
