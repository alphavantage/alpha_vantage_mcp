"""MCP tool registry - thin wrapper around av_api.registry."""

import functools
import json

from av_api.registry import (  # noqa: F401
    DATA_TOOL_ANNOTATIONS,
    DATA_TOOL_OUTPUT_SCHEMA,
    _all_tools_registry,
    _tools_by_name,
    derive_tool_title,
    ensure_tools_loaded,
    extract_description,
    call_tool,
    get_tool_list,
    get_tool_schema,
    get_tool_schemas,
)


def _json_serialize_result(func):
    """Wrap a tool func so dict / non-(str|bytes) returns are JSON-serialized.

    The awslabs MCPLambdaHandler serializes a non-bytes tool result with ``str(result)``
    (Python repr, e.g. single quotes / ``True`` / ``None``) — not JSON. Data tools return
    raw dicts (datatype=json payloads, AV error dicts, and large-response preview dicts), so
    without this the Lambda text content would be invalid JSON. Mirror the stdio path (which
    json.dumps dicts itself) so awslabs emits valid JSON text and the structuredContent
    injector can recover the real object via json.loads. Bytes pass through untouched so
    awslabs' image handling still works.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if isinstance(result, (str, bytes)):
            return result
        return json.dumps(result, indent=2)

    return wrapper


def register_all_tools(mcp):
    """Register the full catalog of Alpha Vantage data tools as normal MCP tools.

    Loops every registered tool function through the custom mcp.tool decorator (which
    builds the inputSchema from the wrapped func's signature). Each tool carries the
    shared behavior hints, a derived human-readable title, and the permissive
    outputSchema. The stored implementation is wrapped to JSON-serialize dict returns
    (see _json_serialize_result) so the awslabs handler emits valid JSON text content.
    """
    from mcp.types import ToolAnnotations

    ensure_tools_loaded()
    for func in _all_tools_registry:
        tool_name = func.__name__.upper()
        annotations = ToolAnnotations(
            title=derive_tool_title(tool_name),
            **DATA_TOOL_ANNOTATIONS,
        )
        mcp.tool(
            annotations=annotations,
            output_schema=DATA_TOOL_OUTPUT_SCHEMA,
        )(func)
        # The decorator stores the raw func as the implementation; swap in the
        # JSON-serializing wrapper for dispatch (schema was already built from the raw func).
        mcp.tool_implementations[tool_name] = _json_serialize_result(func)


def register_meta_tools(mcp):
    """Register the legacy meta-tools (TOOL_LIST, TOOL_GET, TOOL_CALL) as normal MCP tools.

    Additive, back-compat registration alongside register_all_tools(): some historical
    clients still have these cached from the old progressive-discovery mode and call them
    directly, so they must keep working even though the full flat tool catalog is also
    registered (todo 2764).
    """
    from mcp.types import ToolAnnotations
    from av_mcp.tools.meta_tools import (
        META_TOOL_OPEN_WORLD_HINT,
        META_TOOL_OUTPUT_SCHEMA,
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
        tool_name = func.__name__.upper()
        annotations = ToolAnnotations(
            title=title,
            readOnlyHint=True,
            destructiveHint=False,
            openWorldHint=META_TOOL_OPEN_WORLD_HINT[tool_name],
        )
        mcp.tool(
            annotations=annotations,
            output_schema=META_TOOL_OUTPUT_SCHEMA[tool_name],
        )(func)
