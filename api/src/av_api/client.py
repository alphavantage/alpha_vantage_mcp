import httpx
import json
import os
from av_api.context import get_api_key

API_BASE_URL = "https://www.alphavantage.co/query"

# Maximum token size for responses (configurable via environment variable)
MAX_RESPONSE_TOKENS = int(os.environ.get('MAX_RESPONSE_TOKENS', '8192'))

# Module-level entitlement state (replaces globals() hack)
_current_entitlement = None

# Pluggable response processor for large responses.
# Signature: (response_text: str, datatype: str, estimated_tokens: int) -> dict | str
_response_processor = None


def set_response_processor(fn):
    """Set a callback to handle large responses (e.g., preview + S3 upload).

    The callback receives (response_text, datatype, estimated_tokens) and should
    return the processed result (typically a preview dict).
    """
    global _response_processor
    _response_processor = fn


def estimate_tokens(data) -> int:
    """Estimate the number of tokens in a data structure.

    Uses a simple heuristic: ~4 characters per token.
    """
    if isinstance(data, str):
        return len(data) // 4
    elif isinstance(data, (dict, list)):
        json_str = json.dumps(data, separators=(',', ':'))
        return len(json_str) // 4
    else:
        return len(str(data)) // 4


def _make_api_request(function_name: str, params: dict) -> dict | str:
    """Helper function to make API requests and handle responses.

    For large responses exceeding MAX_RESPONSE_TOKENS, delegates to the
    configured response_processor if one is set, otherwise returns the
    data as-is.
    """
    # Create a copy of params to avoid modifying the original
    api_params = params.copy()
    api_params.update({
        "function": function_name,
        "apikey": get_api_key(),
        "source": "alphavantagemcp"
    })

    # Handle entitlement parameter if present in params or module-level variable
    entitlement = api_params.get("entitlement") or _current_entitlement

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

        # For large responses, delegate to response_processor if configured
        if _response_processor is not None:
            return _response_processor(response_text, datatype, estimated_tokens)

        # No processor configured — return data as-is
        if datatype == "json":
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                return response_text
        else:
            return response_text
