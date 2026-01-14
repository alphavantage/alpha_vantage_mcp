#!/usr/bin/env python3
"""Test script for OpenAI schema generation."""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.openai_actions import generate_openapi_schema, execute_tool

def test_schema_generation():
    """Test generating the OpenAPI schema."""
    print("Testing OpenAPI schema generation...")
    schema = generate_openapi_schema()
    
    # Pretty print the schema
    print(json.dumps(schema, indent=2))
    
    # Verify schema structure
    assert "openapi" in schema
    assert "paths" in schema
    assert "info" in schema
    
    # Check that we have some paths
    assert len(schema["paths"]) > 0
    
    # Check a specific tool exists (function names are uppercased)
    assert "/openai/PING" in schema["paths"]
    assert "/openai/ADD_TWO_NUMBERS" in schema["paths"]
    
    # Check that all descriptions are within 300 character limit
    print("\nChecking description lengths...")
    exceeded_limit = []
    for path, methods in schema["paths"].items():
        for method, details in methods.items():
            if "description" in details:
                desc_len = len(details["description"])
                if desc_len > 300:
                    exceeded_limit.append(f"Path {path}, method {method}: {desc_len} chars")
    
    if exceeded_limit:
        print("❌ Descriptions exceeding 300 character limit:")
        for item in exceeded_limit:
            print(f"  {item}")
        assert False, f"{len(exceeded_limit)} descriptions exceed 300 character limit"
    else:
        print("✓ All descriptions are within 300 character limit")
    
    print(f"\n✓ Schema generated successfully with {len(schema['paths'])} endpoints")
    return schema

def test_tool_execution():
    """Test executing tools directly."""
    print("\nTesting tool execution...")
    
    # Test ping
    result = execute_tool("ping", {})
    assert result == "pong"
    print("✓ ping() returned:", result)
    
    # Test add_two_numbers
    result = execute_tool("add_two_numbers", {"a": 5, "b": 3})
    assert result == 8
    print("✓ add_two_numbers(5, 3) returned:", result)
    
    print("✓ Tool execution working correctly")


def main():
    """Run all tests."""
    print("=" * 60)
    print("OpenAI Schema Generator Tests")
    print("=" * 60)
    
    try:
        # Run tests
        schema = test_schema_generation()
        test_tool_execution()
        
        print("\n" + "=" * 60)
        print("All tests passed! ✅")
        print("=" * 60)
        
        # Print sample endpoint info
        print("\nSample endpoints generated:")
        for path in list(schema["paths"].keys())[:5]:
            print(f"  • {path}")
        if len(schema["paths"]) > 5:
            print(f"  ... and {len(schema['paths']) - 5} more")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    main()