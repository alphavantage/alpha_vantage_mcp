"""
MCP Client test for deployed MCP server using streamable HTTP transport
Run from the repository root:
    uv run tests/test_http_transport.py
"""

import asyncio
import os
import sys

import dotenv
import pytest
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

dotenv.load_dotenv()

# Set test API key if not already set
if not os.getenv("ALPHAVANTAGE_API_KEY"):
    os.environ["ALPHAVANTAGE_API_KEY"] = "test"

# MCP endpoint from deployment
api_key = os.getenv("ALPHAVANTAGE_API_KEY", "test")
domain_name = os.getenv("DOMAIN_NAME")
MCP_SERVER_ENDPOINT = None

if domain_name:
    MCP_SERVER_ENDPOINT = f"https://{domain_name}/mcp?apikey={api_key}"
else:
    base_endpoint = os.getenv("MCP_SERVER_ENDPOINT")
    if base_endpoint:
        MCP_SERVER_ENDPOINT = (
            f"{base_endpoint}?apikey={api_key}"
            if "?" not in base_endpoint
            else f"{base_endpoint}&apikey={api_key}"
        )


async def test_mcp_server():
    """Test the deployed MCP server using real MCP client"""
    if not MCP_SERVER_ENDPOINT:
        pytest.skip(
            "MCP_SERVER_ENDPOINT not configured - set DOMAIN_NAME or MCP_SERVER_ENDPOINT environment variable to run this integration test"
        )

    print("🚀 Testing deployed MCP server")
    print(f"📡 Connecting to: {MCP_SERVER_ENDPOINT}")
    print("=" * 60)

    try:
        # Connect to the deployed MCP server
        async with streamablehttp_client(MCP_SERVER_ENDPOINT) as (
            read_stream,
            write_stream,
            _,
        ):
            print("✅ Connected to MCP server endpoint")

            # Create a session using the client streams
            async with ClientSession(read_stream, write_stream) as session:
                print("✅ MCP session created")

                # Initialize the connection
                print("\n🔧 Initializing MCP session...")
                try:
                    initialize_result = await session.initialize()
                    print("✅ MCP session initialized")
                    print(f"   Protocol version: {initialize_result.protocolVersion}")
                    print(f"   Server info: {initialize_result.serverInfo}")
                except Exception as init_error:
                    print(f"❌ Initialization failed: {init_error}")
                    raise

                # List available tools
                print("\n🔨 Listing available tools...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                print(f"✅ Found {len(tools)} tools:")
                for tool in tools:
                    print(f"   - {tool.name}: {tool.description}")

                # Test ADD_TWO_NUMBERS tool
                if any(tool.name == "ADD_TWO_NUMBERS" for tool in tools):
                    print("\n🔢 Testing ADD_TWO_NUMBERS tool...")
                    add_result = await session.call_tool("ADD_TWO_NUMBERS", {"a": 5, "b": 3})
                    print(f"✅ Add two numbers response: {add_result.content}")
                    print("   5 + 3 = 8")
                else:
                    print("❌ ADD_TWO_NUMBERS tool not found")
                    return False

                print("\n🎉 All tests completed successfully!")
                print("Your MCP server is working with real MCP clients!")

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("Make sure your MCP server endpoint is correct and accessible")
        return False

    return True


async def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        global MCP_SERVER_ENDPOINT
        MCP_SERVER_ENDPOINT = sys.argv[1]
        print(f"Using custom endpoint: {MCP_SERVER_ENDPOINT}")

    success = await test_mcp_server()

    if success:
        print("\n✅ MCP server HTTP test PASSED")
    else:
        print("\n❌ MCP server HTTP test FAILED")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
