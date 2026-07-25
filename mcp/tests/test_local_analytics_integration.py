import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import lambda_function  # noqa: E402
import local_http_server  # noqa: E402

os.environ.pop("AV_HTTP_POOL", None)


class RecordingEmitter:
    def __init__(self):
        self.calls = []

    def emit_mcp_request(self, body, api_key, platform):
        self.calls.append((body, api_key, platform))


def test_local_server_hook_emits_resolved_key_without_lambda_configuration():
    emitter = RecordingEmitter()
    body = json.dumps({"method": "tools/list"})

    local_http_server.configure_analytics_emitter(emitter)
    try:
        lambda_function.parse_and_log_mcp_analytics(body, "unit-token", "test")
    finally:
        local_http_server.configure_analytics_emitter(None)

    assert emitter.calls == [(body, "unit-token", "test")]
