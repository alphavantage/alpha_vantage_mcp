"""logs_processor write-path parsing (todo 2892 trim defense)."""

import logs_processor


def test_parse_log_event_strips_identifier_fields():
    """Padded MCP_ANALYTICS captures are stripped before the JSONL record is built."""
    message = (
        "2026-07-26 05:00:00.123456 something MCP_ANALYTICS: "
        "method= tools/call , api_key_hash=abc , platform= cursor , "
        "tool_name= GLOBAL_QUOTE , arguments={\"symbol\": \"IBM\"}"
    )
    record = logs_processor.parse_log_event({"message": message})

    assert record is not None
    assert record["created_at"] == "2026-07-26 05:00:00.123456"
    assert record["method"] == "tools/call"
    assert record["api_key"] == "abc"
    assert record["platform"] == "cursor"
    assert record["tool_name"] == "GLOBAL_QUOTE"
    assert record["arguments"] == '{"symbol": "IBM"}'


def test_parse_log_event_returns_none_for_non_analytics():
    assert logs_processor.parse_log_event({"message": "info: hello"}) is None
