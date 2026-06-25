import httpx
import json
import os
from av_api.context import get_api_key

API_BASE_URL = "https://www.alphavantage.co/query"

# Shared HTTP client reused across requests for connection pooling (avoids a fresh
# TLS handshake per call). httpx.Client is thread-safe, so the threaded
# local_http_server can share this single instance across request threads.
_http_client = httpx.Client()

# Maximum token size for responses (configurable via environment variable)
MAX_RESPONSE_TOKENS = int(os.environ.get('MAX_RESPONSE_TOKENS', '32000'))

# Module-level entitlement state (replaces globals() hack)
_current_entitlement = None

# Module-level full-response override state set by the tool wrapper
_current_return_full_data = False

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


def _detect_av_error(response_text: str) -> dict | None:
    """Detect an Alpha Vantage error envelope and map it to a structured error.

    Alpha Vantage signals failures with **HTTP 200** and a JSON body keyed by
    ``Error Message`` (rejected request / bad params), ``Information`` or
    ``Note`` (rate limit). Left untouched these pass through as raw data, so the
    caller gets no actionable feedback. This normalizes them into a structured
    error and clearly maps invalid-key and rate-limit cases.

    Returns the structured error dict, or ``None`` for normal data responses.
    """
    try:
        parsed = json.loads(response_text)
    except (json.JSONDecodeError, TypeError):
        return None

    if not isinstance(parsed, dict):
        return None

    if "Error Message" in parsed:
        message = str(parsed["Error Message"])
        if "apikey" in message.lower():
            return {
                "error": {
                    "type": "invalid_api_key",
                    "message": message,
                    "detail": (
                        "The Alpha Vantage API key is invalid or missing. "
                        "Re-authenticate or supply a valid apikey."
                    ),
                }
            }
        return {
            "error": {
                "type": "invalid_request",
                "message": message,
                "detail": (
                    "Alpha Vantage rejected the request parameters. "
                    "Check the tool arguments and retry."
                ),
            }
        }

    for key in ("Information", "Note"):
        if key in parsed:
            return {
                "error": {
                    "type": "rate_limit",
                    "message": str(parsed[key]),
                    "detail": (
                        "Alpha Vantage rate limit reached. Wait and retry, or "
                        "use a premium API key for higher limits."
                    ),
                }
            }

    return None


def _parse_response_text(response_text: str, datatype: str) -> dict | str:
    if datatype == "json":
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            return response_text

    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        return response_text


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
    return_full_data = api_params.pop("return_full_data", None) is True or _current_return_full_data is True

    if entitlement:
        api_params["entitlement"] = entitlement
    elif "entitlement" in api_params:
        # Remove entitlement if it's None or empty
        api_params.pop("entitlement", None)

    response = _http_client.get(API_BASE_URL, params=api_params)
    response.raise_for_status()

    response_text = response.text

    # Alpha Vantage returns HTTP 200 even on failure; surface those error
    # envelopes as structured, actionable errors instead of raw data.
    av_error = _detect_av_error(response_text)
    if av_error is not None:
        return av_error

    # Determine datatype from params (default to csv if not specified)
    datatype = api_params.get("datatype", "csv")

    # Check response size (works for both JSON and CSV)
    estimated_tokens = estimate_tokens(response_text)

    # If response is within limits or full data was explicitly requested, return normally
    if estimated_tokens <= MAX_RESPONSE_TOKENS or return_full_data:
        return _parse_response_text(response_text, datatype)

    # For large responses, delegate to response_processor if configured
    if _response_processor is not None:
        return _response_processor(response_text, datatype, estimated_tokens)

    # No processor configured — return data as-is
    return _parse_response_text(response_text, datatype)
