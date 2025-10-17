#!/usr/bin/env python3
"""Test script for Cloudflare R2 upload functionality."""

import json
import os

from dotenv import load_dotenv

from src.utils import generate_r2_key, upload_to_r2


def test_generate_r2_key():
    """Test R2 key generation."""
    print("Testing R2 key generation...")

    test_data = '{"test": "data", "timestamp": 1234567890}'
    key = generate_r2_key(test_data)
    print(f"  Generated key: {key}")
    assert key.startswith("alphavantage-responses/")
    assert key.endswith(".json")
    print("  ✓ Key format is correct\n")


def test_upload_to_r2():
    """Test R2 upload with environment variables."""
    print("Testing R2 upload...")

    # Load environment variables
    load_dotenv()

    # Test data
    test_data = json.dumps(
        {
            "test": "data",
            "timestamp": 1234567890,
            "message": "This is a test upload to Cloudflare R2",
        }
    )

    # Attempt upload
    url = upload_to_r2(test_data)

    if url:
        print("  ✓ Upload successful!")
        print(f"  URL: {url}")

        # Verify URL format
        r2_domain = os.environ.get("R2_PUBLIC_DOMAIN", "https://data.alphavantage-mcp.com")
        assert url.startswith(r2_domain), f"URL should start with {r2_domain}"
        print("  ✓ URL format is correct")
    else:
        print("  ✗ Upload failed - checking configuration...")

        # Check required environment variables
        required_vars = [
            "R2_BUCKET",
            "R2_PUBLIC_DOMAIN",
            "R2_ENDPOINT_URL",
            "R2_ACCESS_KEY_ID",
            "R2_SECRET_ACCESS_KEY",
        ]

        missing_vars = []
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)

        if missing_vars:
            print(f"  Missing environment variables: {missing_vars}")
        else:
            print("  All environment variables are set")

    print()


def test_upload_with_custom_bucket():
    """Test R2 upload with custom bucket name."""
    print("Testing R2 upload with custom bucket...")

    # Load environment variables
    load_dotenv()

    test_data = json.dumps({"test": "custom bucket upload"})
    custom_bucket = "test-bucket"

    url = upload_to_r2(test_data, bucket_name=custom_bucket)

    if url:
        print("  ✓ Custom bucket upload successful!")
        print(f"  URL: {url}")
    else:
        print("  ✗ Custom bucket upload failed")

    print()


def test_upload_large_data():
    """Test R2 upload with large data."""
    print("Testing R2 upload with large data...")

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
                "volume": 1000000 + m * 1000 + d * 100,
            }
            for m in range(1, 13)
            for d in range(1, 29)
        },
    }

    large_json = json.dumps(large_data)
    print(f"  Data size: {len(large_json)} characters")

    url = upload_to_r2(large_json)

    if url:
        print("  ✓ Large data upload successful!")
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
        "R2_BUCKET": "Cloudflare R2 bucket name",
        "R2_PUBLIC_DOMAIN": "Public domain for R2 URLs",
        "R2_ENDPOINT_URL": "R2 S3-compatible endpoint URL",
        "R2_ACCESS_KEY_ID": "R2 access key ID",
        "R2_SECRET_ACCESS_KEY": "R2 secret access key",
    }

    for var, description in required_vars.items():
        value = os.environ.get(var)
        if value:
            # Mask sensitive values
            if "KEY" in var or "SECRET" in var:
                masked_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
                print(f"  ✓ {var}: {masked_value}")
            else:
                print(f"  ✓ {var}: {value}")
        else:
            print(f"  ✗ {var}: Missing ({description})")

    print()


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Cloudflare R2 Upload Functionality")
    print("=" * 60)
    print()

    test_env_variables()
    test_generate_r2_key()
    test_upload_to_r2()
    test_upload_with_custom_bucket()
    test_upload_large_data()

    print("=" * 60)
    print("All R2 tests completed!")
    print("=" * 60)
