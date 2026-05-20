import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lambda_function import normalize_content_type_header  # noqa: E402


def test_normalize_content_type_strips_charset_parameter():
    event = {"headers": {"content-type": "application/json; charset=utf-8"}}

    normalize_content_type_header(event)

    assert event["headers"]["content-type"] == "application/json"


def test_normalize_content_type_strips_parameter_without_space():
    event = {"headers": {"content-type": "application/json;charset=utf-8"}}

    normalize_content_type_header(event)

    assert event["headers"]["content-type"] == "application/json"


def test_normalize_content_type_leaves_application_json_unchanged():
    event = {"headers": {"content-type": "application/json"}}

    normalize_content_type_header(event)

    assert event["headers"]["content-type"] == "application/json"


def test_normalize_content_type_handles_case_insensitive_header_key():
    event = {"headers": {"Content-Type": "application/json; charset=utf-8"}}

    normalize_content_type_header(event)

    assert event["headers"]["Content-Type"] == "application/json"
    assert event["headers"]["content-type"] == "application/json"
