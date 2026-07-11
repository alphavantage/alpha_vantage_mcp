"""Meta-tools for progressive tool discovery.

These tools allow LLMs to discover available tools without flooding
the context window with full schemas upfront.
"""
import json
from av_mcp.tools.registry import get_tool_list, get_tool_schema, get_tool_schemas, call_tool


# MCP behavior hints (openWorldHint) per meta-tool, shared by the stdio and Lambda
# registration paths. TOOL_LIST/TOOL_GET only read the in-process tool registry (no
# network); TOOL_CALL proxies to Alpha Vantage data tools that fetch market data over
# the public internet. All three are read-only and non-destructive.
META_TOOL_OPEN_WORLD_HINT = {
    "TOOL_LIST": False,
    "TOOL_GET": False,
    "TOOL_CALL": True,
}


# MCP outputSchema (JSON Schema describing each meta-tool's structuredContent), shared by
# the stdio and Lambda paths. structuredContent must be a JSON *object*, so the list/string
# results are wrapped: TOOL_LIST/TOOL_GET -> {"tools": [...]}, TOOL_CALL -> {"result": ...}.
# A tool may only declare outputSchema if it also returns matching structuredContent, so
# both transports build structuredContent via build_structured_content() below.
#
# TOOL_CALL's payload is dynamic (depends on which Alpha Vantage data tool is proxied), so
# its schema is intentionally permissive: "result" accepts any JSON value.
_TOOL_ENTRY_SCHEMA = {"type": "object", "additionalProperties": True}

META_TOOL_OUTPUT_SCHEMA = {
    "TOOL_LIST": {
        "type": "object",
        "properties": {"tools": {"type": "array", "items": _TOOL_ENTRY_SCHEMA}},
        "required": ["tools"],
        "additionalProperties": False,
    },
    "TOOL_GET": {
        "type": "object",
        "properties": {"tools": {"type": "array", "items": _TOOL_ENTRY_SCHEMA}},
        "required": ["tools"],
        "additionalProperties": False,
    },
    "TOOL_CALL": {
        "type": "object",
        "properties": {"result": {}},
        "required": ["result"],
        "additionalProperties": False,
    },
}


def build_structured_content(tool_name: str, raw) -> dict:
    """Wrap a meta-tool's raw return value into the object shape its outputSchema declares.

    Single source for both transports so the declared outputSchema and the emitted
    structuredContent never drift apart.

    Args:
        tool_name: Meta-tool name ("TOOL_LIST" | "TOOL_GET" | "TOOL_CALL").
        raw: The meta-tool's raw result (list/dict for LIST/GET; for TOOL_CALL a dict or a
             JSON string, which is parsed back to an object when possible).
    """
    if tool_name in ("TOOL_LIST", "TOOL_GET"):
        return {"tools": raw if isinstance(raw, list) else [raw]}
    # TOOL_CALL: parse JSON strings back to objects so structuredContent carries real data.
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            pass
    return {"result": raw}


def tool_list() -> list[dict]:
    """
    Lists the available Alpha Vantage API tools, returning each tool's name and short
    description without parameter schemas.

    Returns:
        List of tools with 'name' and 'description' fields only (no parameter schemas).
    """
    return get_tool_list()


def tool_get(tool_name: str | list[str]) -> dict | list[dict]:
    """
    Returns the full schema for one or more named tools, including each tool's name,
    description, and parameter definitions (JSON schema). Accepts a single tool name or
    a list of tool names.

    Args:
        tool_name: The name of the tool to get schema for (e.g., "TIME_SERIES_DAILY"),
                   or a list of tool names (e.g., ["TIME_SERIES_DAILY", "TIME_SERIES_INTRADAY"])

    Returns:
        Tool schema with 'name', 'description', and 'parameters' (JSON schema).
        If a list of tool names is provided, returns a list of schemas.
    """
    if isinstance(tool_name, list):
        return get_tool_schemas(tool_name)
    return get_tool_schema(tool_name)


def tool_call(tool_name: str, arguments: str) -> dict | str:
    """
    Executes a named Alpha Vantage API tool with the provided arguments and returns its result.

    Args:
        tool_name: The name of the tool to call (e.g., "TIME_SERIES_DAILY")
        arguments: Dictionary of arguments matching the tool's parameter schema

    Returns:
        The result from the tool execution.
    """
    # Parse arguments if passed as JSON string
    if isinstance(arguments, str):
        arguments = json.loads(arguments)
    result = call_tool(tool_name, arguments)
    # Ensure dicts are returned as JSON strings so the MCP framework
    # doesn't str() them into Python repr syntax
    if isinstance(result, dict):
        return json.dumps(result, indent=2)
    return result
