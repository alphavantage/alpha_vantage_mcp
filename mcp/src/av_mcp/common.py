import os
from av_api.client import _make_api_request, set_response_processor, MAX_RESPONSE_TOKENS  # noqa: F401
from av_mcp.utils import upload_to_object_storage


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


def _server_response_processor(response_text: str, datatype: str, estimated_tokens: int) -> dict:
    """Process large responses: upload to S3 and return a preview."""
    try:
        data_url = upload_to_object_storage(response_text, datatype=datatype)

        # Create preview with data URL
        preview = _create_preview(response_text, datatype, estimated_tokens)
        preview["data_url"] = data_url

        return preview

    except Exception as e:
        # If upload fails, return error with preview
        return _create_preview(response_text, datatype, estimated_tokens, str(e))


# Install the server-specific response processor at import time
set_response_processor(_server_response_processor)
