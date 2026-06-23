"""Meta-tools for progressive tool discovery.

These tools allow LLMs to discover available tools without flooding
the context window with full schemas upfront.
"""
import json
from av_mcp.tools.registry import get_tool_list, get_tool_schema, get_tool_schemas, call_tool


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
