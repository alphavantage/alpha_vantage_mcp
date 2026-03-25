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

    annotations = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        openWorldHint=True,
    )
    for func in [tool_list, tool_get, tool_call]:
        mcp.tool(annotations=annotations)(func)
