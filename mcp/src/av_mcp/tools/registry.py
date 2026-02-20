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
    from av_mcp.tools.meta_tools import tool_list, tool_get, tool_call

    for func in [tool_list, tool_get, tool_call]:
        mcp.tool()(func)

    # MCPLambdaHandler.tool() only uses the first paragraph of the docstring.
    # Patch descriptions to include the full docstring (before Args:/Returns:).
    for tool_schema in mcp.tools.values():
        name = tool_schema["name"]
        impl = mcp.tool_implementations[name]
        tool_schema["description"] = extract_description(impl)
