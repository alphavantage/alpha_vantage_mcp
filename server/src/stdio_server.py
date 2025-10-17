#!/usr/bin/env python3
"""
Stdio MCP server for Alpha Vantage API.

This server provides MCP (Model Context Protocol) access to Alpha Vantage financial data
via stdio transport, suitable for use with local MCP clients.

Usage:
    python stdio_server.py [API_KEY]

Environment Variables:
    ALPHA_VANTAGE_API_KEY: Your Alpha Vantage API key
"""

import asyncio
import os
import sys
from typing import Any

import click
import mcp.server.stdio
import mcp.types as types
from loguru import logger
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from .context import set_api_key
from .tools.registry import TOOL_MODULES, get_all_tools


class StdioMCPServer:
    """Stdio MCP Server for Alpha Vantage"""

    def __init__(self, api_key: str, categories: list[str] = None, verbose: bool = False):
        self.api_key = api_key
        self.categories = categories
        self.verbose = verbose
        self.server = Server("alphavantage-mcp")

        # Set up the API key context
        set_api_key(api_key)

        # Get all tools for the specified categories
        if categories:
            if verbose:
                logger.info(f"Loading tools for categories: {', '.join(categories)}")
            try:
                self.tools = get_all_tools(categories)
            except ValueError as e:
                logger.warning(f"Error with categories {categories}: {e}, loading all tools")
                self.tools = get_all_tools()
        else:
            if verbose:
                logger.info("Loading all tools")
            self.tools = get_all_tools()

        # Register handlers
        self._register_handlers()

    def _register_handlers(self):
        """Register MCP protocol handlers"""

        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available tools."""
            return [tool_def for tool_def, _ in self.tools]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
            """Handle tool calls."""
            for tool_def, tool_func in self.tools:
                if tool_def.name == name:
                    try:
                        # Call the tool function with provided arguments
                        if asyncio.iscoroutinefunction(tool_func):
                            result = await tool_func(**arguments)
                        else:
                            result = tool_func(**arguments)

                        # Convert result to text content
                        if isinstance(result, str):
                            return [types.TextContent(type="text", text=result)]
                        else:
                            return [types.TextContent(type="text", text=str(result))]

                    except Exception as e:
                        logger.error(f"Error calling tool {name}: {e}")
                        return [types.TextContent(type="text", text=f"Error: {str(e)}")]

            raise ValueError(f"Unknown tool: {name}")

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
@click.argument("api_key", required=False)
@click.option(
    "--api-key", "api_key_option", help="Alpha Vantage API key (alternative to positional argument)"
)
@click.option(
    "--categories", multiple=True, help="Tool categories to include (default: all categories)"
)
@click.option("--list-categories", is_flag=True, help="List available tool categories and exit")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def cli(api_key, api_key_option, categories, list_categories, verbose):
    (
        """Alpha Vantage MCP Server (stdio transport)

    Available tool categories:
    """
        + "\n".join(f"  - {cat}" for cat in TOOL_MODULES.keys())
        + """

    Examples:
      av-mcp YOUR_API_KEY
      av-mcp YOUR_API_KEY --categories core_stock_apis forex
      av-mcp --api-key YOUR_API_KEY --categories technical_indicators
    """
    )
    # Configure logging based on verbose flag
    if not verbose:
        logger.remove()
        logger.add(sys.stderr, level="WARNING")

    # List categories and exit if requested
    if list_categories:
        print("Available tool categories:")
        for category in TOOL_MODULES.keys():
            print(f"  - {category}")
        return

    # Get API key from args or environment
    api_key = api_key or api_key_option or os.getenv("ALPHA_VANTAGE_API_KEY")

    if not api_key:
        logger.error(
            "API key required. Provide via argument or ALPHA_VANTAGE_API_KEY environment variable"
        )
        print("Error: API key required", file=sys.stderr)
        print("Usage: av-mcp YOUR_API_KEY", file=sys.stderr)
        print("   or: ALPHA_VANTAGE_API_KEY=YOUR_KEY av-mcp", file=sys.stderr)
        sys.exit(1)

    # Validate categories if provided
    if categories:
        invalid_categories = [cat for cat in categories if cat not in TOOL_MODULES]
        if invalid_categories:
            logger.error(f"Invalid categories: {', '.join(invalid_categories)}")
            print(f"Error: Invalid categories: {', '.join(invalid_categories)}", file=sys.stderr)
            print("\\nAvailable categories:", file=sys.stderr)
            for cat in TOOL_MODULES.keys():
                print(f"  - {cat}", file=sys.stderr)
            sys.exit(1)

    # Create and run server
    if verbose:
        logger.info(
            f"Starting Alpha Vantage MCP Server (stdio) with {len(categories or TOOL_MODULES)} categories"
        )
    server = StdioMCPServer(api_key, list(categories), verbose)

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
