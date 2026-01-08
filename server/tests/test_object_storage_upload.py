#!/usr/bin/env python3
"""Test script for S3 object storage upload functionality."""

import os
import json
from dotenv import load_dotenv
from src.utils import upload_to_object_storage, generate_storage_key

def test_generate_storage_key():
    """Test storage key generation."""
    print("Testing storage key generation...")

    test_data = '{"test": "data", "timestamp": 1234567890}'
    key = generate_storage_key(test_data)
    print(f"  Generated key: {key}")
    assert key.startswith("mcp-responses/")
    assert key.endswith(".json")
    print("  ✓ Key format is correct\n")

def test_upload_to_object_storage():
    """Test S3 upload with environment variables."""
    print("Testing S3 upload...")

    # Load environment variables
    load_dotenv()

    # Test data
    test_data = json.dumps({
        "test": "data",
        "timestamp": 1234567890,
        "message": "This is a test upload to S3"
    })

    # Attempt upload
    url = upload_to_object_storage(test_data)

    if url:
        print(f"  ✓ Upload successful!")
        print(f"  URL: {url}")

        # Verify URL format
        cdn_domain = os.environ.get('CDN_DOMAIN')
        if cdn_domain:
            assert cdn_domain in url, f"URL should contain {cdn_domain}"
            print("  ✓ URL format is correct")
    else:
        print("  ✗ Upload failed - checking configuration...")

        # Check required environment variables
        required_vars = ['CDN_BUCKET_NAME', 'CDN_DOMAIN']

        missing_vars = []
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)

        if missing_vars:
            print(f"  Missing environment variables: {missing_vars}")
        else:
            print("  All environment variables are set")

    print()

def test_upload_large_data():
    """Test S3 upload with large data."""
    print("Testing S3 upload with large data...")

    # Load environment variables
    load_dotenv()

    # Generate large test data
    large_data = {
        "Meta Data": {"Symbol": "TEST"},
        "Time Series": {
            f"2024-{m:02d}-{d:02d}": {
                "open": 100 + m + d,
                "high": 105 + m + d,
                "low": 95 + m + d,
                "close": 102 + m + d,
                "volume": 1000000 + m * 1000 + d * 100
            }
            for m in range(1, 13)
            for d in range(1, 29)
        }
    }

    large_json = json.dumps(large_data)
    print(f"  Data size: {len(large_json)} characters")

    url = upload_to_object_storage(large_json)

    if url:
        print(f"  ✓ Large data upload successful!")
        print(f"  URL: {url}")
    else:
        print("  ✗ Large data upload failed")

    print()

def test_env_variables():
    """Test that all required environment variables are present."""
    print("Testing environment variables...")

    # Load environment variables
    load_dotenv()

    required_vars = {
        'CDN_BUCKET_NAME': 'S3 bucket name for CDN storage',
        'CDN_DOMAIN': 'CDN domain for public URLs',
        'AWS_REGION': 'AWS region (optional, defaults to us-east-1)'
    }

    for var, description in required_vars.items():
        value = os.environ.get(var)
        if value:
            print(f"  ✓ {var}: {value}")
        else:
            print(f"  ✗ {var}: Missing ({description})")

    print()

if __name__ == "__main__":
    print("=" * 60)
    print("Testing S3 Object Storage Upload Functionality")
    print("=" * 60)
    print()

    test_env_variables()
    test_generate_storage_key()
    test_upload_to_object_storage()
    test_upload_large_data()

    print("=" * 60)
    print("All S3 tests completed!")
    print("=" * 60)