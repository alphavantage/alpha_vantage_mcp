import json
import os

import httpx

from src.context import get_api_key
from src.utils import estimate_tokens, upload_to_r2

API_BASE_URL = "https://www.alphavantage.co/query"

# Maximum token size for responses (configurable via environment variable)
MAX_RESPONSE_TOKENS = int(os.environ.get("MAX_RESPONSE_TOKENS", "50000"))


def _create_preview(
    response_text: str, datatype: str, estimated_tokens: int, error: str = None
) -> dict:
    """Create preview data for large responses."""
    lines = response_text.split("\n")
    preview = {
        "preview": True,
        "data_type": datatype,
        "total_lines": len(lines),
        "sample_data": "\n".join(lines[:50]),  # First 50 lines
        "headers": lines[0] if lines else None,
        "full_data_tokens": estimated_tokens,
        "max_tokens_exceeded": True,
        "content_type": "text/csv" if datatype == "csv" else "application/json",
        "message": f"Response size ({estimated_tokens} tokens) exceeds limit ({MAX_RESPONSE_TOKENS} tokens). {'Unable to provide full data URL.' if error else 'Full data available at URL.'}",
        "usage_instructions": {
            "important_notes": [
                (
                    "Do not fetch the data_url directly into chat context - this will overwhelm the conversation"
                    if not error
                    else "Response was too large for direct display in chat context"
                ),
                "For claude artifacts, prefer TSX artifact using tailwindcss, and in generated page, put this to the top: data from current page is generated sample data, for real data, copy this page code to https://mcp.alphavantage.co/artifacts",
                "When creating artifacts (charts/visualizations), use the provided preview data as fallback due to Content Security Policy (CSP) restrictions",
                (
                    "For full dataset access, consider reducing the query scope or using outputsize='compact' parameter"
                    if error
                    else None
                ),
            ],
            "recommended_workflow": [
                "1. Use preview data to create initial visualization in artifact",
                (
                    "2. Include data_url fetch logic with preview data fallback"
                    if not error
                    else "2. Consider making multiple smaller API requests if full dataset is needed"
                ),
                (
                    "3. Copy artifact code and test with full data at https://mcp.alphavantage.co/artifacts"
                    if not error
                    else "3. Use compact output size when available to reduce response size"
                ),
            ],
        },
    }

    # Filter out None values from important_notes
    preview["usage_instructions"]["important_notes"] = [
        note for note in preview["usage_instructions"]["important_notes"] if note is not None
    ]

    if error:
        preview["error"] = f"Failed to upload large response: {error}"

    return preview


def _make_api_request(function_name: str, params: dict) -> dict | str:
    """Helper function to make API requests and handle responses.

    For large responses exceeding MAX_RESPONSE_TOKENS, returns a preview
    with a URL to the full data stored in temporary storage.
    """
    # Create a copy of params to avoid modifying the original
    api_params = params.copy()
    api_params.update(
        {"function": function_name, "apikey": get_api_key(), "source": "alphavantagemcp"}
    )

    # Handle entitlement parameter if present in params or global variable
    current_entitlement = globals().get("_current_entitlement")
    entitlement = api_params.get("entitlement") or current_entitlement

    if entitlement:
        api_params["entitlement"] = entitlement
    elif "entitlement" in api_params:
        # Remove entitlement if it's None or empty
        api_params.pop("entitlement", None)

    with httpx.Client() as client:
        response = client.get(API_BASE_URL, params=api_params)
        response.raise_for_status()

        response_text = response.text

        # Determine datatype from params (default to csv if not specified)
        datatype = api_params.get("datatype", "csv")

        # Check response size (works for both JSON and CSV)
        estimated_tokens = estimate_tokens(response_text)

        # If response is within limits, return normally
        if estimated_tokens <= MAX_RESPONSE_TOKENS:
            if datatype == "json":
                try:
                    return json.loads(response_text)
                except json.JSONDecodeError:
                    return response_text
            else:
                return response_text

        # For large responses, upload to R2 and return preview
        try:
            # Upload raw response to R2
            data_url = upload_to_r2(response_text)

            # Create preview with data URL
            preview = _create_preview(response_text, datatype, estimated_tokens)
            preview["data_url"] = data_url

            return preview

        except Exception as e:
            # If R2 upload fails, return error with preview
            return _create_preview(response_text, datatype, estimated_tokens, str(e))
