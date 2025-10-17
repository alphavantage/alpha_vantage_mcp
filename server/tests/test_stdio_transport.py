"""
MCP Client test for local MCP server using stdio transport
Run from the repository root:
    uv run tests/test_stdio_transport.py
"""

import asyncio
import os
import sys

import dotenv
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

dotenv.load_dotenv()

# Set test API key if not already set
if not os.getenv("ALPHAVANTAGE_API_KEY"):
    os.environ["ALPHAVANTAGE_API_KEY"] = "test"


async def test_mcp_server_stdio():
    """Test the local MCP server using stdio transport"""
    print("🚀 Testing local MCP server via stdio")
    print("=" * 50)

    try:
        # Create server parameters
        api_key = os.getenv("ALPHAVANTAGE_API_KEY", "test")
        server_params = StdioServerParameters(
            command="uvx", args=["av-mcp", api_key, "--categories", "ping"]
        )
        print(f"📡 Starting server: {server_params.command} {' '.join(server_params.args)}")

        # Connect to the local MCP server via stdio
        async with stdio_client(server_params) as (read_stream, write_stream):
            print("✅ Connected to MCP server via stdio")

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
                print("Your MCP server is working with stdio transport!")

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("Make sure your MCP server can be started locally")
        return False

    return True


async def main():
    """Main entry point"""
    success = await test_mcp_server_stdio()

    if success:
        print("\n✅ MCP server stdio test PASSED")
    else:
        print("\n❌ MCP server stdio test FAILED")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
