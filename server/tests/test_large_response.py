#!/usr/bin/env python3
"""Test script for large response handling in Alpha Vantage MCP."""

import json

from src.utils import estimate_tokens


def test_token_estimation():
    """Test token estimation function."""
    print("Testing token estimation...")

    # Test string
    text = "Hello world this is a test string"
    tokens = estimate_tokens(text)
    print(f"  String '{text}' => ~{tokens} tokens")

    # Test dict
    data = {"key1": "value1", "key2": [1, 2, 3], "key3": {"nested": "data"}}
    tokens = estimate_tokens(data)
    print(f"  Dict with {len(json.dumps(data))} chars => ~{tokens} tokens")

    # Test large list
    large_list = [{"id": i, "value": f"item_{i}" * 10} for i in range(1000)]
    tokens = estimate_tokens(large_list)
    print(f"  List with 1000 items => ~{tokens} tokens")
    print()


def test_csv_preview():
    """Test CSV preview generation."""
    print("Testing CSV preview...")

    csv_data = """timestamp,open,high,low,close,volume
2024-01-01,100.0,105.0,95.0,102.0,1000000
2024-01-02,101.0,106.0,96.0,103.0,1001000
2024-01-03,102.0,107.0,97.0,104.0,1002000
2024-01-04,103.0,108.0,98.0,105.0,1003000
2024-01-05,104.0,109.0,99.0,106.0,1004000
2024-01-06,105.0,110.0,100.0,107.0,1005000
2024-01-07,106.0,111.0,101.0,108.0,1006000
2024-01-08,107.0,112.0,102.0,109.0,1007000
2024-01-09,108.0,113.0,103.0,110.0,1008000
2024-01-10,109.0,114.0,104.0,111.0,1009000
2024-01-11,110.0,115.0,105.0,112.0,1010000
2024-01-12,111.0,116.0,106.0,113.0,1011000"""

    lines = csv_data.split("\n")
    preview = {
        "preview": True,
        "data_type": "csv",
        "total_lines": len(lines),
        "sample_data": "\n".join(lines[:10]),
        "headers": lines[0] if lines else None,
    }

    print("  CSV with", len(lines), "lines")
    print("  Headers:", preview["headers"])
    print("  Sample lines:", preview["sample_data"].count("\n") + 1)
    print()


def test_large_response_handling():
    """Test how the system would handle a large response."""
    print("Testing large response handling simulation...")

    # Simulate a large response
    large_data = {
        "Meta Data": {"Symbol": "TEST"},
        "Time Series": {
            f"2024-{m:02d}-{d:02d}": {
                "open": 100 + m + d,
                "high": 105 + m + d,
                "low": 95 + m + d,
                "close": 102 + m + d,
                "volume": 1000000 + m * 1000 + d * 100,
            }
            for m in range(1, 13)
            for d in range(1, 29)
        },
    }

    tokens = estimate_tokens(large_data)
    print(f"  Large dataset token estimate: {tokens}")

    MAX_TOKENS = 50000
    if tokens > MAX_TOKENS:
        print(f"  Would trigger large response handling (>{MAX_TOKENS} tokens)")
        print("  Would generate preview with first 50 lines of response")
    else:
        print(f"  Would return normally (<={MAX_TOKENS} tokens)")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Large Response Handling")
    print("=" * 60)
    print()

    test_token_estimation()
    test_csv_preview()
    test_large_response_handling()

    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)
