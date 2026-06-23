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
