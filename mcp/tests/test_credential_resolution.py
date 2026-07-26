"""Lambda-level credential resolution regression tests (todo 2889).

Pytest version of the repro for the client-reported bug (email 26-07-26): a cached OAuth
Bearer token minted with an OLD apikey used to win over an explicit ``?apikey=NEW`` query
param (stale-key pinning), and a raw apikey sent as the Authorization header 401'd because
it failed strict JWT decoding. Scenarios:

- A: valid Bearer carrying OLD key + ``?apikey=NEW`` must resolve NEW (raw key wins).
- B: ``Authorization: Bearer <raw key>`` (and bare ``Authorization: <raw key>``) must be
  accepted as a raw apikey with 200.
- C: ``?apikey=NEW`` only resolves NEW (control, unchanged).

JWT-shaped-but-invalid Bearer values must still 401 (RFC 6750), and a credential-less
request must still 401.
"""

import json
import os
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Provision the two server-held keys before importing the token module (read lazily, but set
# here so every test in the module shares stable keys).
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-do-not-use-in-prod")
from cryptography.fernet import Fernet  # noqa: E402

os.environ.setdefault("AV_APIKEY_ENC_KEY", Fernet.generate_key().decode())

import lambda_function  # noqa: E402
from av_mcp import tokens  # noqa: E402

OLD_KEY = "1NDBR4B8ZNA8F5IV"
NEW_KEY = "1VCKZ7JS90AN00FP"


def _mint_access_token(api_key, ttl=timedelta(hours=1)):
    return tokens.encode_token(
        {"typ": "access", "enc_apikey": tokens.encrypt_apikey(api_key)}, ttl
    )


def _tools_list_event(headers=None, query=None):
    return {
        "httpMethod": "POST",
        "path": "/mcp",
        "headers": {"content-type": "application/json", **(headers or {})},
        "queryStringParameters": query,
        "body": json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}),
    }


def _capture_resolved_key(monkeypatch):
    """Stub set_api_key to capture which credential _handle_request resolved."""
    captured = {}
    monkeypatch.setattr(
        lambda_function, "set_api_key", lambda key: captured.__setitem__("key", key)
    )
    return captured


def test_scenario_a_explicit_query_apikey_wins_over_stale_bearer(monkeypatch):
    captured = _capture_resolved_key(monkeypatch)
    event = _tools_list_event(
        headers={"Authorization": f"Bearer {_mint_access_token(OLD_KEY)}"},
        query={"apikey": NEW_KEY},
    )
    response = lambda_function.lambda_handler(event, None)
    assert response["statusCode"] == 200
    assert captured["key"] == NEW_KEY


def test_scenario_b_raw_apikey_as_bearer_authorization(monkeypatch):
    captured = _capture_resolved_key(monkeypatch)
    event = _tools_list_event(headers={"Authorization": f"Bearer {NEW_KEY}"})
    response = lambda_function.lambda_handler(event, None)
    assert response["statusCode"] == 200
    assert captured["key"] == NEW_KEY


def test_scenario_b_raw_apikey_as_bare_authorization(monkeypatch):
    captured = _capture_resolved_key(monkeypatch)
    event = _tools_list_event(headers={"Authorization": NEW_KEY})
    response = lambda_function.lambda_handler(event, None)
    assert response["statusCode"] == 200
    assert captured["key"] == NEW_KEY


def test_scenario_c_query_only_control(monkeypatch):
    captured = _capture_resolved_key(monkeypatch)
    event = _tools_list_event(query={"apikey": NEW_KEY})
    response = lambda_function.lambda_handler(event, None)
    assert response["statusCode"] == 200
    assert captured["key"] == NEW_KEY


def test_valid_oauth_bearer_alone_still_resolves_token_key(monkeypatch):
    # OAuth-only clients (no raw key anywhere) keep working exactly as before.
    captured = _capture_resolved_key(monkeypatch)
    event = _tools_list_event(
        headers={"Authorization": f"Bearer {_mint_access_token(OLD_KEY)}"}
    )
    response = lambda_function.lambda_handler(event, None)
    assert response["statusCode"] == 200
    assert captured["key"] == OLD_KEY


def test_garbage_jwt_shaped_bearer_still_401(monkeypatch):
    captured = _capture_resolved_key(monkeypatch)
    event = _tools_list_event(headers={"Authorization": "Bearer aaa.bbb.ccc"})
    response = lambda_function.lambda_handler(event, None)
    assert response["statusCode"] == 401
    assert json.loads(response["body"])["error"] == "invalid_token"
    assert "key" not in captured


def test_expired_oauth_bearer_still_401(monkeypatch):
    captured = _capture_resolved_key(monkeypatch)
    event = _tools_list_event(
        headers={
            "Authorization": f"Bearer {_mint_access_token(OLD_KEY, timedelta(seconds=-5))}"
        }
    )
    response = lambda_function.lambda_handler(event, None)
    assert response["statusCode"] == 401
    assert json.loads(response["body"])["error"] == "invalid_token"
    assert "key" not in captured


def test_no_credential_still_401(monkeypatch):
    captured = _capture_resolved_key(monkeypatch)
    response = lambda_function.lambda_handler(_tools_list_event(), None)
    assert response["statusCode"] == 401
    assert json.loads(response["body"])["error"] == "invalid_request"
    assert "key" not in captured
