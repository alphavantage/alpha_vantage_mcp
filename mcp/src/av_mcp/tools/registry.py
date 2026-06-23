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
    from av_mcp.tools.meta_tools import (
        META_TOOL_OPEN_WORLD_HINT,
        tool_list,
        tool_get,
        tool_call,
    )

    # Each meta-tool gets a human-readable `title` annotation (Software Directory
    # Policy 5.E) plus behavior hints. All are read-only and non-destructive;
    # openWorldHint varies per tool (only TOOL_CALL reaches the public internet).
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
            openWorldHint=META_TOOL_OPEN_WORLD_HINT[func.__name__.upper()],
        )
        mcp.tool(annotations=annotations)(func)
