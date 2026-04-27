import json
import os
from av_api.client import _make_api_request, set_response_processor, MAX_RESPONSE_TOKENS  # noqa: F401
from av_mcp.utils import upload_to_object_storage


# Heuristic: top-level dicts with more than this many keys are treated as
# keyed time series (e.g. "Time Series (Daily)") and truncated like arrays.
_KEYED_SERIES_THRESHOLD = 10


def _build_json_sample(parsed, max_array_items: int = 2):
    """Build a structured preview that keeps every top-level field visible.

    Top-level arrays and large keyed dicts are truncated to ``max_array_items``
    entries with ``<key>_total_count`` / ``<key>_truncated`` siblings so the
    consumer can see that more data exists. Nested dicts are flattened one
    level deep using the same strategy.
    """
    if not isinstance(parsed, dict):
        return parsed

    sample: dict = {}
    for key, value in parsed.items():
        if isinstance(value, list):
            sample[key] = value[:max_array_items]
            if len(value) > max_array_items:
                sample[f"{key}_total_count"] = len(value)
                sample[f"{key}_truncated"] = True
        elif isinstance(value, dict) and len(value) > _KEYED_SERIES_THRESHOLD:
            kept = dict(list(value.items())[:max_array_items])
            sample[key] = kept
            sample[f"{key}_total_count"] = len(value)
            sample[f"{key}_truncated"] = True
        elif isinstance(value, dict):
            inner: dict = {}
            for ik, iv in value.items():
                if isinstance(iv, list):
                    inner[ik] = iv[:max_array_items]
                    if len(iv) > max_array_items:
                        inner[f"{ik}_total_count"] = len(iv)
                        inner[f"{ik}_truncated"] = True
                else:
                    inner[ik] = iv
            sample[key] = inner
        else:
            sample[key] = value
    return sample


def _create_preview(response_text: str, datatype: str, estimated_tokens: int, error: str = None) -> dict:
    """Create preview data for large responses."""
    lines = response_text.split('\n')

    sample_data = None
    sample_line_count = 0
    effective_datatype = datatype
    try:
        parsed = json.loads(response_text)
    except (ValueError, TypeError):
        parsed = None
    if parsed is not None:
        effective_datatype = "json"
        structured = _build_json_sample(parsed)
        sample_data = json.dumps(structured, indent=2)
        sample_line_count = sample_data.count('\n') + 1

    if sample_data is None:
        # Fallback: prefix-truncate up to half the token budget (~4 chars per token)
        max_preview_chars = MAX_RESPONSE_TOKENS // 2 * 4
        truncated = response_text[:max_preview_chars]
        # Snap to last complete line
        last_newline = truncated.rfind('\n')
        if last_newline != -1:
            truncated = truncated[:last_newline]
        sample_lines = truncated.split('\n')
        sample_data = '\n'.join(sample_lines)
        sample_line_count = len(sample_lines)

    preview = {
        "preview": True,
        "data_type": effective_datatype,
        "total_lines": len(lines),
        "sample_lines": sample_line_count,
        "sample_data": sample_data,
        "headers": lines[0] if lines else None,
        "full_data_tokens": estimated_tokens,
        "max_tokens_exceeded": True,
        "content_type": "text/csv" if effective_datatype == "csv" else "application/json",
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
