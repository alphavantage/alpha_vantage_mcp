"""Write-path normalization of analytics identifier fields (todo 2892)."""

import hashlib
import json
from contextlib import contextmanager

from av_mcp.utils import normalize_analytics_field, parse_and_log_mcp_analytics
from loguru import logger


@contextmanager
def _capture_log_messages():
    messages = []
    sink_id = logger.add(messages.append, format="{message}")
    try:
        yield messages
    finally:
        logger.remove(sink_id)


def test_normalize_analytics_field_strips_whitespace_including_nbsp():
    assert normalize_analytics_field(" K \n") == "K"
    assert normalize_analytics_field("\xa0K\xa0") == "K"
    assert normalize_analytics_field(None) == ""
    assert normalize_analytics_field(7) == "7"
    assert normalize_analytics_field("   ") == ""


def test_parse_and_log_mcp_analytics_strips_identifiers_before_hash_and_log():
    clean_hash = hashlib.sha256(b"KEY").hexdigest()[:16]
    padded_hash = hashlib.sha256(b" KEY ").hexdigest()[:16]
    assert clean_hash != padded_hash  # precondition: padding changes the hash

    body = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": " tools/call ",
            "params": {
                "name": " GLOBAL_QUOTE ",
                "arguments": {"symbol": "IBM"},
            },
        }
    )

    with _capture_log_messages() as messages:
        parse_and_log_mcp_analytics(body, " KEY ", " cursor ")

    joined = "\n".join(messages)
    assert (
        f"MCP_ANALYTICS: method=tools/call, api_key_hash={clean_hash}, "
        f"platform=cursor, tool_name=GLOBAL_QUOTE,"
    ) in joined
    assert f"api_key_hash={padded_hash}" not in joined
