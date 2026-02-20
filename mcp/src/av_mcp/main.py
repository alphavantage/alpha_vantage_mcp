import os
import sys

import click


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.argument('api_key', required=False)
@click.option('--api-key', 'api_key_option', help='Alpha Vantage API key (alternative to positional argument)')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def serve(api_key, api_key_option, verbose):
    """Start MCP server (stdio transport).

    Uses progressive discovery mode with meta-tools (TOOL_LIST, TOOL_GET, TOOL_CALL).
    LLMs can discover and call specific tools on-demand without flooding the context.

    Examples:
      av-mcp YOUR_API_KEY
      av-mcp --api-key YOUR_API_KEY
      ALPHA_VANTAGE_API_KEY=YOUR_KEY av-mcp
    """
    import asyncio
    from loguru import logger
    from av_mcp.stdio_server import StdioMCPServer

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


if __name__ == "__main__":
    serve()
