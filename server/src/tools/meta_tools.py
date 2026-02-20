"""Meta-tools for progressive tool discovery.

These tools allow LLMs to discover available tools without flooding
the context window with full schemas upfront.
"""
import json
from av_api.registry import get_tool_list, get_tool_schema, get_tool_schemas, call_tool


def tool_list() -> list[dict]:
    """
    List all available Alpha Vantage API tools with their names and descriptions.

    IMPORTANT: This returns only tool names and descriptions, NOT parameter schemas.
    You MUST call TOOL_GET(tool_name) to retrieve the full inputSchema (required
    parameters, types, descriptions) before calling TOOL_CALL. Calling TOOL_CALL
    without first calling TOOL_GET will fail because you won't know the required
    parameters.

    Workflow: TOOL_LIST -> TOOL_GET(tool_name) -> TOOL_CALL(tool_name, arguments)

    Returns:
        List of tools with 'name' and 'description' fields only (no parameter schemas).
    """
    return get_tool_list()


def tool_get(tool_name: str | list[str]) -> dict | list[dict]:
    """
    Get the full schema for one or more tools including all parameters.

    After discovering tools via TOOL_LIST, use this to get the complete
    parameter schema before calling the tool. You can provide either a single
    tool name or a list of tool names if you're unsure which one to use.

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
    Execute a tool by name with the provided arguments.

    IMPORTANT: You MUST call TOOL_GET(tool_name) first to retrieve the full parameter
    schema before calling this tool. The arguments must match the schema returned by
    TOOL_GET, including all required parameters. Calling without the correct arguments
    will result in errors.

    Workflow: TOOL_LIST -> TOOL_GET(tool_name) -> TOOL_CALL(tool_name, arguments)

    Args:
        tool_name: The name of the tool to call (e.g., "TIME_SERIES_DAILY")
        arguments: Dictionary of arguments matching the tool's parameter schema from TOOL_GET

    Returns:
        The result from the tool execution.
    """
    # Parse arguments if passed as JSON string
    if isinstance(arguments, str):
        arguments = json.loads(arguments)
    return call_tool(tool_name, arguments)
