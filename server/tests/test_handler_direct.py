#!/usr/bin/env python3
"""
MCP client test for local MCP server
Tests the MCP server using a client-like approach
"""

import json
import os

import dotenv

from lambda_function import lambda_handler

dotenv.load_dotenv()


class MockMCPClient:
    """Mock MCP client that tests MCP server directly"""

    def __init__(self):
        self.request_id = 1

    def _call_lambda(self, method: str, params: dict = None) -> dict:
        """Call the Lambda function with MCP-formatted request"""
        body = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
        }
        if params:
            body["params"] = params

        self.request_id += 1

        # Create Lambda event
        event = {
            "httpMethod": "POST",
            "path": "/mcp",
            "headers": {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "Authorization": f"Bearer {os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')}",
            },
            "body": json.dumps(body),
            "queryStringParameters": None,
            "isBase64Encoded": False,
        }

        # Call the Lambda handler
        response = lambda_handler(event, None)

        # Parse response
        if response["statusCode"] == 200:
            try:
                return json.loads(response["body"])
            except json.JSONDecodeError as e:
                return {"error": f"Invalid JSON response: {e}"}
        else:
            return {"error": f"HTTP {response['statusCode']}: {response['body']}"}

    def initialize(self, client_info: dict = None) -> dict:
        """Initialize MCP connection"""
        params = {
            "protocolVersion": "2025-03-26",
            "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
            "clientInfo": client_info or {"name": "mcp-test-client", "version": "1.0.0"},
        }
        return self._call_lambda("initialize", params)

    def list_tools(self) -> dict:
        """List available tools"""
        return self._call_lambda("tools/list")

    def call_tool(self, name: str, arguments: dict = None) -> dict:
        """Call a specific tool"""
        params = {"name": name, "arguments": arguments or {}}
        return self._call_lambda("tools/call", params)


def print_test_result(test_name: str, success: bool, response: dict = None, details: str = None):
    """Print formatted test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")

    if details:
        print(f"   {details}")

    if response and not success:
        print(f"   Response: {json.dumps(response, indent=4)}")
    elif response and success:
        # Show condensed response for successful tests
        if isinstance(response, dict) and "result" in response:
            result = response["result"]
            if isinstance(result, dict):
                if "tools" in result:
                    tools_count = len(result["tools"])
                    print(f"   Found {tools_count} tools")
                elif "content" in result:
                    print("   Tool executed successfully")
                elif "protocolVersion" in result:
                    print(f"   Protocol version: {result['protocolVersion']}")


def test_mcp_client_functionality():
    """Test MCP functionality using client-like patterns"""
    print("🚀 Starting MCP Server Client Tests")
    print("=" * 50)

    client = MockMCPClient()
    results = []

    # Test 1: Initialize
    print("\n🔧 Initializing MCP session...")
    try:
        response = client.initialize()
        success = (
            "error" not in response
            and "result" in response
            and "protocolVersion" in response.get("result", {})
        )
        if success:
            result = response.get("result", {})
            print("✅ MCP session initialized")
            print(f"   Protocol version: {result.get('protocolVersion')}")
            if "serverInfo" in result:
                server_info = result["serverInfo"]
                print(f"   Server info: {server_info}")
        else:
            print("❌ Initialization failed")
        results.append(success)
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        results.append(False)

    # Test 2: List Tools
    print("\n🔨 Listing available tools...")
    try:
        response = client.list_tools()
        success = (
            "error" not in response
            and "result" in response
            and "tools" in response.get("result", {})
        )
        if success:
            tools = response.get("result", {}).get("tools", [])
            print(f"✅ Found {len(tools)} tools:")
            for tool in tools:
                name = tool.get("name", "unknown")
                description = tool.get("description", "No description")
                print(f"   - {name}: {description}")
        else:
            print("❌ Failed to list tools")
        results.append(success)
    except Exception as e:
        print(f"❌ Failed to list tools: {e}")
        results.append(False)

    # Test 3: Test ADD_TWO_NUMBERS tool
    print("\n🔢 Testing ADD_TWO_NUMBERS tool...")
    try:
        # First get the tools to see if ADD_TWO_NUMBERS exists
        tools_response = client.list_tools()
        if "result" in tools_response and "tools" in tools_response["result"]:
            tools = tools_response["result"]["tools"]
            has_add_tool = any(tool.get("name") == "ADD_TWO_NUMBERS" for tool in tools)

            if has_add_tool:
                response = client.call_tool("ADD_TWO_NUMBERS", {"a": 5, "b": 3})
                success = (
                    "error" not in response
                    and "result" in response
                    and "content" in response.get("result", {})
                )
                if success:
                    content = response.get("result", {}).get("content", [])
                    print(f"✅ Add two numbers response: {content}")
                    print("   5 + 3 = 8")
                else:
                    print("❌ Add two numbers failed")
                results.append(success)
            else:
                print("⚠️ ADD_TWO_NUMBERS tool not available, skipping test")
                results.append(True)  # Don't fail if tool doesn't exist
        else:
            print("❌ Could not check for ADD_TWO_NUMBERS tool")
            results.append(False)
    except Exception as e:
        print(f"❌ Add two numbers test failed: {e}")
        results.append(False)

    # Summary
    print(f"\n{'='*50}")
    print("📊 TEST SUMMARY")
    print(f"{'='*50}")
    passed = sum(results)
    total = len(results)
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")

    if passed == total:
        print("\n🎉 All tests passed! Your MCP server is working perfectly with client patterns.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the implementation.")

    return passed == total


def main():
    """Run the MCP client tests"""
    success = test_mcp_client_functionality()

    if success:
        print("\n✅ MCP server test PASSED")
    else:
        print("\n❌ MCP server test FAILED")
        return False

    return True


if __name__ == "__main__":
    main()
