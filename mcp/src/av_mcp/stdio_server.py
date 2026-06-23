"""
Stdio MCP server for Alpha Vantage API.

This server provides MCP (Model Context Protocol) access to Alpha Vantage financial data
via stdio transport, suitable for use with local MCP clients.

Exposes the full catalog of Alpha Vantage data tools directly as normal MCP tools, with
direct tools/call dispatch (clients do their own discovery over the listed tools).
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
    """Stdio MCP Server for Alpha Vantage exposing the real tool catalog directly."""

    def __init__(self, api_key: str, verbose: bool = False):
        self.api_key = api_key
        self.verbose = verbose
        self.server = Server("alphavantage-mcp")
        self.tools = build_tools()

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
            """Dispatch a tool call directly to the named Alpha Vantage tool.

            Returns both unstructured text content and structuredContent matching the
            declared outputSchema (the lowlevel server validates the latter).
            Exceptions propagate to the lowlevel handler, which renders an isError result.
            """
            try:
                result = call_tool(name, arguments)
            except Exception as e:
                # Re-raise so the lowlevel server builds a proper isError CallToolResult
                # instead of a text body that would fail outputSchema validation.
                logger.error(f"Error calling tool {name}: {e}")
                raise

            # Unstructured text (back-compat) + structuredContent (matches outputSchema),
            # both derived from the same already-returned result (no re-fetch).
            text = result if isinstance(result, str) else json.dumps(result, indent=2)
            content = [types.TextContent(type="text", text=text)]
            structured = build_data_structured_content(result)
            return content, structured

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
