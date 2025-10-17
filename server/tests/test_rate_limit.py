"""
MCP Client test for rate limiting using GLOBAL_QUOTE tool
Run from the repository root:
    uv run tests/test_rate_limit.py

Add --rate-limit-test flag to test with 30 API calls (for rate limit testing):
    uv run tests/test_rate_limit.py --rate-limit-test
"""

import asyncio
import os
import sys

import dotenv
import pytest
from loguru import logger
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


async def test_rate_limit(rate_limit_test=False):
    """Test rate limiting with GLOBAL_QUOTE tool"""
    if not MCP_SERVER_ENDPOINT:
        pytest.skip(
            "MCP_SERVER_ENDPOINT not configured - set DOMAIN_NAME or MCP_SERVER_ENDPOINT environment variable to run this integration test"
        )

    print("🚀 Testing MCP server rate limiting")
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

                # Test GLOBAL_QUOTE tool with AAPL
                if any(tool.name == "GLOBAL_QUOTE" for tool in tools):
                    num_calls = 30 if rate_limit_test else 1
                    call_desc = f"({num_calls} times)" if rate_limit_test else ""
                    print(f"\n📈 Testing GLOBAL_QUOTE tool with AAPL {call_desc}...")
                    for i in range(1, num_calls + 1):
                        try:
                            logger.info(f"Making GLOBAL_QUOTE call #{i}/{num_calls}")
                            quote_result = await session.call_tool(
                                "GLOBAL_QUOTE", {"symbol": "AAPL"}
                            )
                            logger.success(
                                f"Call #{i} - GLOBAL_QUOTE AAPL response: {quote_result.content}"
                            )
                        except Exception as quote_error:
                            logger.error(f"Call #{i} - GLOBAL_QUOTE test failed: {quote_error}")
                    print(
                        f"✅ Completed {num_calls} GLOBAL_QUOTE call{'s' if num_calls > 1 else ''}"
                    )
                else:
                    print("❌ GLOBAL_QUOTE tool not found")
                    return False

                print("\n🎉 Rate limit test completed successfully!")
                print("Your MCP server handled the rate limiting test!")

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("Make sure your MCP server endpoint is correct and accessible")
        return False

    return True


async def main():
    """Main entry point"""
    rate_limit_test = "--rate-limit-test" in sys.argv
    if rate_limit_test:
        sys.argv.remove("--rate-limit-test")

    if len(sys.argv) > 1:
        global MCP_SERVER_ENDPOINT
        MCP_SERVER_ENDPOINT = sys.argv[1]
        print(f"Using custom endpoint: {MCP_SERVER_ENDPOINT}")

    success = await test_rate_limit(rate_limit_test=rate_limit_test)

    if success:
        print("\n✅ Rate limit test PASSED")
    else:
        print("\n❌ Rate limit test FAILED")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
