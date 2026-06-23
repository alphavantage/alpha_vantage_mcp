"""MCP tool registry - thin wrapper around av_api.registry."""

from av_api.registry import (  # noqa: F401
    _all_tools_registry,
    _tools_by_name,
    ensure_tools_loaded,
    extract_description,
    call_tool,
    get_tool_list,
    get_tool_schema,
    get_tool_schemas,
)


def register_meta_tools(mcp):
    """Register only the meta-tools (TOOL_LIST, TOOL_GET, TOOL_CALL) for progressive discovery."""
    from mcp.types import ToolAnnotations
    from av_mcp.tools.meta_tools import tool_list, tool_get, tool_call

    # Each meta-tool gets a human-readable `title` annotation (Software Directory
    # Policy 5.E) in addition to readOnlyHint/destructiveHint.
    meta_tools = [
        (tool_list, "List Alpha Vantage Tools"),
        (tool_get, "Get Alpha Vantage Tool Schema"),
        (tool_call, "Call Alpha Vantage Tool"),
    ]
    for func, title in meta_tools:
        annotations = ToolAnnotations(
            title=title,
            readOnlyHint=True,
            destructiveHint=False,
        )
        mcp.tool(annotations=annotations)(func)
