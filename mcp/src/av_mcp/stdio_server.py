"""
Stdio MCP server for Alpha Vantage API.

This server provides MCP (Model Context Protocol) access to Alpha Vantage financial data
via stdio transport, suitable for use with local MCP clients.

Exposes the full catalog of Alpha Vantage data tools directly as normal MCP tools, with
direct tools/call dispatch (clients do their own discovery over the listed tools). Also
exposes the legacy TOOL_LIST/TOOL_GET/TOOL_CALL meta-tools alongside the flat catalog for
backward compatibility with historical clients that still have them cached.
"""

import json
from typing import Any
from loguru import logger

import mcp.server.stdio
import mcp.types as types
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from av_api.context import set_api_key
from av_api.registry import (
    DATA_TOOL_ANNOTATIONS,
    DATA_TOOL_OUTPUT_SCHEMA,
    _all_tools_registry,
    build_data_structured_content,
    call_tool,
    derive_tool_title,
    ensure_tools_loaded,
    extract_description,
    _build_parameter_schema,
)
import av_mcp.common  # noqa: F401 — registers response processor for large responses
from .tools.meta_tools import (
    META_TOOL_OPEN_WORLD_HINT,
    META_TOOL_OUTPUT_SCHEMA,
    build_structured_content as build_meta_tool_structured_content,
    tool_list,
    tool_get,
    tool_call,
)


# Legacy meta-tools (TOOL_LIST, TOOL_GET, TOOL_CALL), kept alongside the flat tool catalog
# for backward compatibility with historical clients that still have them cached from the
# old progressive-discovery mode (todo 2764). Descriptions are derived from meta_tools.py
# docstrings. All meta-tools are read-only and non-destructive; openWorldHint varies per
# tool (see META_TOOL_OPEN_WORLD_HINT) since only TOOL_CALL reaches the public internet.
def _meta_annotations(tool_name: str) -> types.ToolAnnotations:
    return types.ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        openWorldHint=META_TOOL_OPEN_WORLD_HINT[tool_name],
    )


META_TOOLS = [
    types.Tool(
        name="TOOL_LIST",
        description=extract_description(tool_list),
        inputSchema={
            "type": "object",
            "properties": {},
            "required": []
        },
        outputSchema=META_TOOL_OUTPUT_SCHEMA["TOOL_LIST"],
        annotations=_meta_annotations("TOOL_LIST"),
    ),
    types.Tool(
        name="TOOL_GET",
        description=extract_description(tool_get),
        inputSchema={
            "type": "object",
            "properties": {
                "tool_name": {
                    "oneOf": [
                        {
                            "type": "string",
                            "description": "The name of the tool to get schema for (e.g., 'TIME_SERIES_DAILY')"
                        },
                        {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "A list of tool names to get schemas for (e.g., ['TIME_SERIES_DAILY', 'TIME_SERIES_INTRADAY'])"
                        }
                    ]
                }
            },
            "required": ["tool_name"]
        },
        outputSchema=META_TOOL_OUTPUT_SCHEMA["TOOL_GET"],
        annotations=_meta_annotations("TOOL_GET"),
    ),
    types.Tool(
        name="TOOL_CALL",
        description=extract_description(tool_call),
        inputSchema={
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "description": "The name of the tool to call (e.g., 'TIME_SERIES_DAILY')"
                },
                "arguments": {
                    "type": "object",
                    "description": "Dictionary of arguments matching the tool's parameter schema"
                }
            },
            "required": ["tool_name", "arguments"]
        },
        outputSchema=META_TOOL_OUTPUT_SCHEMA["TOOL_CALL"],
        annotations=_meta_annotations("TOOL_CALL"),
    )
]


def build_tools() -> list[types.Tool]:
    """Build the full list of Alpha Vantage data tools as MCP Tool definitions.

    Each registered tool function is mapped to a types.Tool carrying its input schema,
    behavior hints (DATA_TOOL_ANNOTATIONS), a derived human-readable title, and the shared
    permissive outputSchema.
    """
    ensure_tools_loaded()
    tools = []
    for func in _all_tools_registry:
        name = func.__name__.upper()
        tools.append(
            types.Tool(
                name=name,
                description=extract_description(func),
                inputSchema=_build_parameter_schema(func),
                outputSchema=DATA_TOOL_OUTPUT_SCHEMA,
                annotations=types.ToolAnnotations(
                    title=derive_tool_title(name),
                    **DATA_TOOL_ANNOTATIONS,
                ),
            )
        )
    return tools


class StdioMCPServer:
    """Stdio MCP Server for Alpha Vantage exposing the real tool catalog directly.

    Also exposes the legacy TOOL_LIST/TOOL_GET/TOOL_CALL meta-tools alongside the flat
    catalog for backward compatibility with historical clients that still have them
    cached from the old progressive-discovery mode (todo 2764).
    """

    def __init__(self, api_key: str, verbose: bool = False):
        self.api_key = api_key
        self.verbose = verbose
        self.server = Server("alphavantage-mcp")
        self.tools = build_tools() + META_TOOLS

        # Set up the API key context
        set_api_key(api_key)

        if verbose:
            logger.info(f"Registering {len(self.tools)} Alpha Vantage tools")

        # Register handlers
        self._register_handlers()

    def _register_handlers(self):
        """Register MCP protocol handlers for the full tool catalog."""

        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List all available Alpha Vantage tools."""
            return self.tools

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict[str, Any]
        ) -> tuple[list[types.TextContent], dict[str, Any]]:
            """Dispatch a tool call to a meta-tool or directly to a named Alpha Vantage tool.

            Returns both unstructured text content and structuredContent matching the
            declared outputSchema (the lowlevel server validates the latter).
            Exceptions propagate to the lowlevel handler, which renders an isError result.
            """
            try:
                if name == "TOOL_LIST":
                    result = tool_list()
                elif name == "TOOL_GET":
                    tool_name = arguments.get("tool_name")
                    if not tool_name:
                        raise ValueError("tool_name is required")
                    result = tool_get(tool_name)
                elif name == "TOOL_CALL":
                    tool_name = arguments.get("tool_name")
                    tool_args = arguments.get("arguments", {})
                    if not tool_name:
                        raise ValueError("tool_name is required")
                    result = tool_call(tool_name, tool_args)
                else:
                    result = call_tool(name, arguments)

                # Unstructured text (back-compat) + structuredContent (matches outputSchema),
                # both derived from the same already-returned result (no re-fetch).
                text = result if isinstance(result, str) else json.dumps(result, indent=2)
                content = [types.TextContent(type="text", text=text)]
                structured = (
                    build_meta_tool_structured_content(name, result)
                    if name in META_TOOL_OUTPUT_SCHEMA
                    else build_data_structured_content(result)
                )
                return content, structured
            except Exception as e:
                # Re-raise so the lowlevel server builds a proper isError CallToolResult
                # instead of a text body that would fail outputSchema validation.
                logger.error(f"Error calling tool {name}: {e}")
                raise

    async def run(self):
        """Run the low-level server"""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="alphavantage-mcp",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
