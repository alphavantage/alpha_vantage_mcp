import httpx
import json
import os
from src.context import get_api_key
from src.utils import estimate_tokens, upload_to_object_storage

API_BASE_URL = "https://www.alphavantage.co/query"

# Maximum token size for responses (configurable via environment variable)
MAX_RESPONSE_TOKENS = int(os.environ.get('MAX_RESPONSE_TOKENS', '8192'))


def _create_preview(response_text: str, datatype: str, estimated_tokens: int, error: str = None) -> dict:
    """Create preview data for large responses."""
    lines = response_text.split('\n')

    # Build sample_data up to half the token budget (~4 chars per token)
    max_preview_chars = MAX_RESPONSE_TOKENS // 2 * 4
    truncated = response_text[:max_preview_chars]
    # Snap to last complete line
    last_newline = truncated.rfind('\n')
    if last_newline != -1:
        truncated = truncated[:last_newline]
    sample_lines = truncated.split('\n')

    preview = {
        "preview": True,
        "data_type": datatype,
        "total_lines": len(lines),
        "sample_lines": len(sample_lines),
        "sample_data": '\n'.join(sample_lines),
        "headers": lines[0] if lines else None,
        "full_data_tokens": estimated_tokens,
        "max_tokens_exceeded": True,
        "content_type": "text/csv" if datatype == "csv" else "application/json",
        "message": f"This is a preview ({MAX_RESPONSE_TOKENS} token limit). Full data ({estimated_tokens} tokens) {'unavailable.' if error else 'at data_url. Fetch it if needed for your task.'}",
        "return_full_data_note": f"All tools support a return_full_data parameter. Set it to True to get the complete response without truncation. Only use when the user explicitly requests full data or when the preview is insufficient. WARNING: full data is {estimated_tokens} tokens — do NOT use return_full_data if it would exceed your context window.",
        "artifact_url": "https://mcp.alphavantage.co/artifacts",
        "artifact_note": "claude.ai artifacts can't fetch data_url due to CSP restrictions; users can paste artifact code into this page to render full data"
    }
    
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
    api_params.update({
        "function": function_name,
        "apikey": get_api_key(),
        "source": "alphavantagemcp"
    })
    
    # Handle entitlement parameter if present in params or global variable
    current_entitlement = globals().get('_current_entitlement')
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
        
        # Determine datatype: use param if specified, otherwise detect from response
        datatype = api_params.get("datatype")
        if not datatype:
            datatype = "json" if response_text.lstrip().startswith(("{", "[")) else "csv"
        
        # Check response size (works for both JSON and CSV)
        estimated_tokens = estimate_tokens(response_text)

        # If return_full_data is set, skip truncation/preview
        return_full_data = globals().get('_return_full_data', False)

        # If response is within limits or full data requested, return normally
        if return_full_data or estimated_tokens <= MAX_RESPONSE_TOKENS:
            if datatype == "json":
                try:
                    return json.loads(response_text)
                except json.JSONDecodeError:
                    return response_text
            else:
                return response_text
            
        # For large responses, upload to object storage and return preview
        try:
            data_url = upload_to_object_storage(response_text, datatype=datatype)
            
            # Create preview with data URL
            preview = _create_preview(response_text, datatype, estimated_tokens)
            preview["data_url"] = data_url
            
            return preview
            
        except Exception as e:
            # If upload fails, return error with preview
            return _create_preview(response_text, datatype, estimated_tokens, str(e))