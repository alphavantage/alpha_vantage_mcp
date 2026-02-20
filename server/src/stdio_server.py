#!/usr/bin/env python3
"""
Stdio MCP server for Alpha Vantage API.

This server provides MCP (Model Context Protocol) access to Alpha Vantage financial data
via stdio transport, suitable for use with local MCP clients.

Uses progressive discovery mode: only meta-tools (TOOL_LIST, TOOL_GET, TOOL_CALL) are
exposed, allowing LLMs to discover and call specific tools on-demand without flooding
the context window.

Usage:
    python stdio_server.py [API_KEY]

Environment Variables:
    ALPHA_VANTAGE_API_KEY: Your Alpha Vantage API key
"""

import os
import sys
import asyncio
import json
import click
from typing import Any
from loguru import logger

import mcp.server.stdio
import mcp.types as types
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from .context import set_api_key
from .tools.meta_tools import tool_list, tool_get, tool_call
from .tools.registry import extract_description


# Meta-tool definitions for progressive discovery
# Descriptions are derived from meta_tools.py docstrings
META_TOOLS = [
    types.Tool(
        name="TOOL_LIST",
        description=extract_description(tool_list),
        inputSchema={
            "type": "object",
            "properties": {},
            "required": []
        }
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
        }
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
                    "description": "Dictionary of arguments matching the tool's parameter schema from TOOL_GET"
                }
            },
            "required": ["tool_name", "arguments"]
        }
    )
]


class StdioMCPServer:
    """Stdio MCP Server for Alpha Vantage with progressive discovery"""

    def __init__(self, api_key: str, verbose: bool = False):
        self.api_key = api_key
        self.verbose = verbose
        self.server = Server("alphavantage-mcp")

        # Set up the API key context
        set_api_key(api_key)

        if verbose:
            logger.info("Registering meta-tools for progressive discovery")

        # Register handlers
        self._register_handlers()

    def _register_handlers(self):
        """Register MCP protocol handlers for meta-tools only"""

        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available meta-tools."""
            return META_TOOLS

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
            """Handle meta-tool calls."""
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
                    raise ValueError(f"Unknown tool: {name}")

                # Convert result to text content
                if isinstance(result, str):
                    return [types.TextContent(type="text", text=result)]
                else:
                    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    
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


@click.command()
@click.argument('api_key', required=False)
@click.option('--api-key', 'api_key_option', help='Alpha Vantage API key (alternative to positional argument)')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def cli(api_key, api_key_option, verbose):
    """Alpha Vantage MCP Server (stdio transport)

    Uses progressive discovery mode with meta-tools (TOOL_LIST, TOOL_GET, TOOL_CALL).
    LLMs can discover and call specific tools on-demand without flooding the context.

    Examples:
      av-mcp YOUR_API_KEY
      av-mcp --api-key YOUR_API_KEY
      ALPHA_VANTAGE_API_KEY=YOUR_KEY av-mcp
    """
    # Configure logging based on verbose flag
    if not verbose:
        logger.remove()
        logger.add(sys.stderr, level="WARNING")

    # Get API key from args or environment
    api_key = api_key or api_key_option or os.getenv('ALPHA_VANTAGE_API_KEY')

    if not api_key:
        logger.error("API key required. Provide via argument or ALPHA_VANTAGE_API_KEY environment variable")
        print("Error: API key required", file=sys.stderr)
        print("Usage: av-mcp YOUR_API_KEY", file=sys.stderr)
        print("   or: ALPHA_VANTAGE_API_KEY=YOUR_KEY av-mcp", file=sys.stderr)
        sys.exit(1)

    # Create and run server with progressive discovery
    if verbose:
        logger.info("Starting Alpha Vantage MCP Server (stdio) with progressive discovery")
    server = StdioMCPServer(api_key, verbose)

    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        if verbose:
            logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


def main():
    """Main entry point"""
    cli()


if __name__ == "__main__":
    main()