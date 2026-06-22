"""Tests for the stateless encrypted OAuth tokens and hardened OAuth flow (plan 2555)."""

import base64
import json
import os
from datetime import timedelta

# Provision the two server-held keys before importing the token module (read lazily, but set
# here so every test in the module shares stable keys).
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-do-not-use-in-prod")
from cryptography.fernet import Fernet  # noqa: E402

os.environ.setdefault("AV_APIKEY_ENC_KEY", Fernet.generate_key().decode())

import jwt  # noqa: E402
import pytest  # noqa: E402

from av_mcp import oauth, tokens  # noqa: E402
from av_mcp.utils import parse_token_from_request  # noqa: E402


# --- T1: token module round-trip + apikey not base64-readable + expiry ---------------------


def test_token_round_trip_returns_claims():
    token = tokens.encode_token(
        {"typ": "access", "client_id": "c1"}, timedelta(hours=1)
    )
    claims = tokens.decode_token(token)
    assert claims["typ"] == "access"
    assert claims["client_id"] == "c1"
    assert "exp" in claims


def test_apikey_claim_is_not_base64_readable():
    api_key = "WNDSXRANO529J79Q"
    enc = tokens.encrypt_apikey(api_key)
    # Ciphertext must not contain the apikey, nor be base64-decodable to it.
    assert api_key not in enc
    token = tokens.encode_token(
        {"typ": "access", "enc_apikey": enc}, timedelta(hours=1)
    )
    # The JWT payload is base64-readable, but the apikey inside it is not.
    payload_b64 = token.split(".")[1]
    payload_b64 += "=" * (-len(payload_b64) % 4)
    payload = base64.urlsafe_b64decode(payload_b64).decode()
    assert api_key not in payload


def test_decrypt_apikey_round_trip():
    enc = tokens.encrypt_apikey("MY_SECRET_KEY")
    assert tokens.decrypt_apikey(enc) == "MY_SECRET_KEY"


def test_expired_token_raises_expired_signature_error():
    token = tokens.encode_token({"typ": "access"}, timedelta(seconds=-10))
    with pytest.raises(jwt.ExpiredSignatureError):
        tokens.decode_token(token)


def test_decode_access_token_returns_apikey_for_valid_token():
    enc = tokens.encrypt_apikey("APIKEY123")
    token = tokens.encode_token(
        {"typ": "access", "enc_apikey": enc}, timedelta(hours=1)
    )
    assert tokens.decode_access_token(token) == "APIKEY123"


def test_decode_access_token_rejects_expired_random_and_wrong_typ():
    # Expired.
    enc = tokens.encrypt_apikey("APIKEY123")
    expired = tokens.encode_token(
        {"typ": "access", "enc_apikey": enc}, timedelta(seconds=-5)
    )
    assert tokens.decode_access_token(expired) is None
    # Random / tampered.
    assert tokens.decode_access_token("not-a-jwt") is None
    # Wrong typ (a refresh token must not work as an access token).
    refresh = tokens.encode_token(
        {"typ": "refresh", "enc_apikey": enc}, timedelta(days=1)
    )
    assert tokens.decode_access_token(refresh) is None


# --- Misconfig: unset OAuth keys fail consistently as TokenConfigError (server error) -------


def test_unset_jwt_key_raises_token_config_error(monkeypatch):
    enc = tokens.encrypt_apikey("K")
    token = tokens.encode_token(
        {"typ": "access", "enc_apikey": enc}, timedelta(hours=1)
    )
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    with pytest.raises(tokens.TokenConfigError):
        tokens.decode_access_token(token)


def test_unset_fernet_key_raises_token_config_error(monkeypatch):
    # Missing Fernet key must fail the SAME way as a missing JWT key (not masquerade as 401).
    enc = tokens.encrypt_apikey("K")
    token = tokens.encode_token(
        {"typ": "access", "enc_apikey": enc}, timedelta(hours=1)
    )
    monkeypatch.delenv("AV_APIKEY_ENC_KEY", raising=False)
    with pytest.raises(tokens.TokenConfigError):
        tokens.decode_access_token(token)


def test_minting_without_keys_raises_token_config_error(monkeypatch):
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    with pytest.raises(tokens.TokenConfigError):
        tokens.encode_token({"typ": "access"}, timedelta(hours=1))
    monkeypatch.delenv("AV_APIKEY_ENC_KEY", raising=False)
    with pytest.raises(tokens.TokenConfigError):
        tokens.encrypt_apikey("K")


def test_token_config_error_is_token_error():
    assert issubclass(tokens.TokenConfigError, tokens.TokenError)


# --- Credential parsing: Bearer + query + body all accepted (additive, non-breaking) --------


def test_parse_token_bearer_still_works():
    event = {"headers": {"Authorization": "Bearer abc.def.ghi"}}
    assert parse_token_from_request(event) == "abc.def.ghi"


def test_parse_token_query_apikey_still_works():
    event = {"headers": {}, "queryStringParameters": {"apikey": "QUERYKEY"}}
    assert parse_token_from_request(event) == "QUERYKEY"


def test_parse_token_body_apikey_still_works():
    event = {"headers": {}, "body": json.dumps({"apikey": "BODYKEY"})}
    assert parse_token_from_request(event) == "BODYKEY"


def test_parse_token_precedence_body_over_query_over_header():
    event = {
        "headers": {"Authorization": "Bearer HEADERKEY"},
        "queryStringParameters": {"apikey": "QUERYKEY"},
        "body": json.dumps({"apikey": "BODYKEY"}),
    }
    assert parse_token_from_request(event) == "BODYKEY"
    event.pop("body")
    assert parse_token_from_request(event) == "QUERYKEY"
    event["queryStringParameters"] = {}
    assert parse_token_from_request(event) == "HEADERKEY"


# --- T10: PKCE S256 enforcement + metadata --------------------------------------------------


def test_metadata_advertises_only_s256():
    event = {"headers": {"Host": "mcp.yovy.ai"}}
    resp = oauth.handle_metadata_discovery(event)
    body = json.loads(resp["body"])
    assert body["code_challenge_methods_supported"] == ["S256"]


def test_authorize_without_code_challenge_errors():
    event = {
        "httpMethod": "GET",
        "queryStringParameters": {
            "response_type": "code",
            "client_id": "c1",
            "redirect_uri": "https://claude.ai/api/mcp/auth_callback",
            "state": "xyz",
        },
    }
    resp = oauth.handle_authorization_request(event)
    # Redirected back to client with an error (PKCE is mandatory).
    assert resp["statusCode"] == 302
    assert "error=invalid_request" in resp["headers"]["Location"]


def test_authorize_rejects_plain_pkce_method():
    event = {
        "httpMethod": "GET",
        "queryStringParameters": {
            "response_type": "code",
            "client_id": "c1",
            "redirect_uri": "https://claude.ai/api/mcp/auth_callback",
            "code_challenge": "abc",
            "code_challenge_method": "plain",
        },
    }
    resp = oauth.handle_authorization_request(event)
    assert resp["statusCode"] == 302
    assert "error=invalid_request" in resp["headers"]["Location"]


# --- T2 / T3 / T5: encrypted auth code -> encrypted access + refresh tokens ------------------


def _pkce_pair():
    verifier = "verifier-0123456789-0123456789-0123456789-0123"
    challenge = (
        base64.urlsafe_b64encode(
            __import__("hashlib").sha256(verifier.encode()).digest()
        )
        .decode()
        .rstrip("=")
    )
    return verifier, challenge


def test_auth_code_and_token_flow_end_to_end():
    verifier, challenge = _pkce_pair()
    redirect_uri = "https://claude.ai/api/mcp/auth_callback"
    api_key = "WNDSXRANO529J79Q"

    # Authorization form submission -> encrypted code.
    sub_event = {
        "httpMethod": "POST",
        "queryStringParameters": {
            "response_type": "code",
            "client_id": "c1",
            "redirect_uri": redirect_uri,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": "st",
        },
        "body": f"api_key={api_key}",
    }
    resp = oauth.handle_authorization_request(sub_event)
    assert resp["statusCode"] == 302
    location = resp["headers"]["Location"]
    code = location.split("code=")[1].split("&")[0]

    # T2: the issued code is not base64-decodable to a readable apikey JSON.
    assert api_key not in code

    # T3: exchange the code -> encrypted access token (not the apikey), plus a refresh token.
    token_event = {
        "body": json.dumps(
            {
                "grant_type": "authorization_code",
                "code": code,
                "client_id": "c1",
                "redirect_uri": redirect_uri,
                "code_verifier": verifier,
            }
        )
    }
    token_resp = oauth.handle_token_request(token_event)
    assert token_resp["statusCode"] == 200
    token_body = json.loads(token_resp["body"])
    access_token = token_body["access_token"]
    assert access_token != api_key
    assert api_key not in access_token
    assert "refresh_token" in token_body

    # The access token decrypts back to the original apikey on the request path (T4).
    assert tokens.decode_access_token(access_token) == api_key

    # T5: refresh grant returns a fresh access token that also decrypts to the apikey.
    refresh_event = {
        "body": json.dumps(
            {
                "grant_type": "refresh_token",
                "refresh_token": token_body["refresh_token"],
            }
        )
    }
    refresh_resp = oauth.handle_token_request(refresh_event)
    assert refresh_resp["statusCode"] == 200
    new_access = json.loads(refresh_resp["body"])["access_token"]
    assert tokens.decode_access_token(new_access) == api_key


def test_token_exchange_requires_code_verifier():
    verifier, challenge = _pkce_pair()
    redirect_uri = "https://claude.ai/api/mcp/auth_callback"
    code = tokens.encode_token(
        {
            "typ": "code",
            "client_id": "c1",
            "redirect_uri": redirect_uri,
            "code_challenge": challenge,
            "enc_apikey": tokens.encrypt_apikey("K"),
        },
        timedelta(seconds=60),
    )
    token_event = {
        "body": json.dumps(
            {
                "grant_type": "authorization_code",
                "code": code,
                "client_id": "c1",
                "redirect_uri": redirect_uri,
            }
        )
    }
    resp = oauth.handle_token_request(token_event)
    assert resp["statusCode"] == 400
    assert json.loads(resp["body"])["error"] == "invalid_request"


def test_expired_auth_code_rejected():
    verifier, challenge = _pkce_pair()
    redirect_uri = "https://claude.ai/api/mcp/auth_callback"
    code = tokens.encode_token(
        {
            "typ": "code",
            "client_id": "c1",
            "redirect_uri": redirect_uri,
            "code_challenge": challenge,
            "enc_apikey": tokens.encrypt_apikey("K"),
        },
        timedelta(seconds=-1),
    )
    token_event = {
        "body": json.dumps(
            {
                "grant_type": "authorization_code",
                "code": code,
                "client_id": "c1",
                "redirect_uri": redirect_uri,
                "code_verifier": verifier,
            }
        )
    }
    resp = oauth.handle_token_request(token_event)
    assert resp["statusCode"] == 400
    assert json.loads(resp["body"])["error"] == "invalid_grant"


# --- T8: protected resource metadata --------------------------------------------------------


def test_protected_resource_metadata():
    event = {"headers": {"Host": "mcp.yovy.ai"}}
    resp = oauth.handle_protected_resource_metadata(event)
    body = json.loads(resp["body"])
    assert body["resource"] == "https://mcp.yovy.ai/mcp"
    assert body["authorization_servers"] == ["https://mcp.yovy.ai"]


# --- T9: WWW-Authenticate resource_metadata pointer -----------------------------------------


def test_www_authenticate_includes_resource_metadata(monkeypatch):
    from av_mcp.utils import create_oauth_error_response

    monkeypatch.setenv("DOMAIN_NAME", "mcp.yovy.ai")
    resp = create_oauth_error_response(
        {"error": "invalid_token", "error_description": "bad"}, 401
    )
    www = resp["headers"]["WWW-Authenticate"]
    assert (
        'resource_metadata="https://mcp.yovy.ai/.well-known/oauth-protected-resource"'
        in www
    )


# --- T13: redirect_uri validation (port-agnostic loopback + host allowlist) ------------------


@pytest.mark.parametrize(
    "uri",
    [
        "http://localhost:1234/callback",
        "http://127.0.0.1:54999/cb",
        "https://claude.ai/api/mcp/auth_callback",
        "https://chatgpt.com/connector/oauth/abc",
    ],
)
def test_redirect_uri_allowed(uri):
    assert oauth.is_valid_redirect_uri(uri) is True


@pytest.mark.parametrize(
    "uri",
    [
        "https://evil.example.com/callback",
        "http://claude.ai/api/mcp/auth_callback",  # non-loopback http not allowed
        "ftp://localhost/cb",
        "",
    ],
)
def test_redirect_uri_rejected(uri):
    assert oauth.is_valid_redirect_uri(uri) is False


# --- T12: DCR client_id_issued_at is a real timestamp ---------------------------------------


def test_registration_issued_at_is_unix_timestamp():
    import time

    event = {"body": json.dumps({"redirect_uris": ["http://localhost:8080/callback"]})}
    resp = oauth.handle_registration_request(event)
    assert resp["statusCode"] == 201
    body = json.loads(resp["body"])
    issued_at = body["client_id_issued_at"]
    # A sane recent Unix timestamp (within a day of now), not a random 32-bit int.
    assert abs(issued_at - int(time.time())) < 86400
