"""OAuth 2.1 authorization server implementation for MCP server.

Stateless design: authorization codes, access tokens, and refresh tokens are all
self-contained **encrypted** tokens (PyJWT HS256 envelope + Fernet-encrypted apikey claim,
see ``av_mcp.tokens``). No server-side token store. The raw Alpha Vantage apikey is never
returned to the client and is only decrypted on the request path.
"""

import json
import os
import time
import secrets
import hashlib
import base64
import urllib.parse
from typing import Optional

import jwt

from av_mcp.tokens import (
    ACCESS_TOKEN_TTL,
    AUTH_CODE_TTL,
    REFRESH_TOKEN_TTL,
    decode_token,
    encode_token,
    encrypt_apikey,
)

SCOPE = "alphavantage:read"

# Allowed non-loopback redirect hosts (exact host match, https only). Stateless: DCR cannot
# persist a client's redirect_uris, so validation is rule-based (see T12/T13 in plan 2555).
# Loopback (localhost / 127.0.0.1 / ::1) is handled separately, port-agnostic, for native clients.
ALLOWED_REDIRECT_HOSTS = {
    "claude.ai",  # https://claude.ai/api/mcp/auth_callback
    "claude.com",
    "chatgpt.com",  # ChatGPT connector callback (per-connector path)
    "chat.openai.com",
}
# Base domains whose apex and any subdomain are allowed (https only).
# mcp-use (Manufact) owns *.manufact.com: cloud connector, inspector, and
# preview environments all authenticate against this server.
ALLOWED_REDIRECT_DOMAINS = {
    "manufact.com",
}
LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


def generate_authorization_code() -> str:
    """Generate a secure authorization code."""
    return secrets.token_urlsafe(32)


def generate_state() -> str:
    """Generate a secure state parameter."""
    return secrets.token_urlsafe(32)


def resolve_base_url(event: dict) -> Optional[str]:
    """Resolve the issuer base URL from DOMAIN_NAME env or the request Host header."""
    domain_name = os.environ.get("DOMAIN_NAME")
    if domain_name:
        return f"https://{domain_name}"

    headers = event.get("headers", {}) or {}
    host = headers.get("Host") or headers.get("host")
    if not host:
        return None
    return f"https://{host}"


def is_valid_redirect_uri(redirect_uri: str) -> bool:
    """Validate a redirect_uri with port-agnostic loopback + an https host allowlist."""
    if not redirect_uri:
        return False
    try:
        parsed = urllib.parse.urlparse(redirect_uri)
    except ValueError:
        return False

    host = parsed.hostname or ""
    # Loopback clients (Claude Code): any port, http or https.
    if host in LOOPBACK_HOSTS:
        return parsed.scheme in ("http", "https")
    # Everything else must be https against the host allowlist or an allowed domain.
    if parsed.scheme != "https":
        return False
    if host in ALLOWED_REDIRECT_HOSTS:
        return True
    # Apex or subdomain of an allowed base domain (e.g. *.manufact.com). The
    # "." prefix on the suffix check prevents look-alikes like "evilmanufact.com".
    return any(host == domain or host.endswith(f".{domain}") for domain in ALLOWED_REDIRECT_DOMAINS)


def verify_pkce_challenge(code_verifier: str, code_challenge: str) -> bool:
    """Verify a PKCE S256 code challenge against the verifier."""
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    expected_challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return expected_challenge == code_challenge


def handle_metadata_discovery(event: dict) -> dict:
    """Handle OAuth 2.0 Authorization Server Metadata discovery (RFC 8414)."""
    base_url = resolve_base_url(event)
    if not base_url:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "missing_host_header"}),
        }

    metadata = {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/authorize",
        "token_endpoint": f"{base_url}/token",
        "registration_endpoint": f"{base_url}/register",
        "scopes_supported": [SCOPE],
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        # PKCE S256 is mandatory; "plain" is intentionally not advertised (T10).
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none"],
        "subject_types_supported": ["public"],
    }

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "public, max-age=3600",
        },
        "body": json.dumps(metadata),
    }


def handle_protected_resource_metadata(event: dict) -> dict:
    """Handle OAuth 2.0 Protected Resource Metadata discovery (RFC 9728)."""
    base_url = resolve_base_url(event)
    if not base_url:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "missing_host_header"}),
        }

    metadata = {
        "resource": f"{base_url}/mcp",
        "authorization_servers": [base_url],
        "scopes_supported": [SCOPE],
        "bearer_methods_supported": ["header"],
    }

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "public, max-age=3600",
        },
        "body": json.dumps(metadata),
    }


def handle_authorization_request(event: dict) -> dict:
    """Handle OAuth 2.1 authorization requests.

    Shows the consent UI where the user inputs their Alpha Vantage API key. Enforces PKCE S256
    and validates the redirect_uri before rendering anything.
    """
    query_params = event.get("queryStringParameters") or {}
    http_method = event.get("httpMethod") or event.get("requestContext", {}).get(
        "http", {}
    ).get("method", "GET")

    response_type = query_params.get("response_type")
    client_id = query_params.get("client_id")
    redirect_uri = query_params.get("redirect_uri")
    state = query_params.get("state")

    # PKCE parameters.
    code_challenge = query_params.get("code_challenge")
    code_challenge_method = query_params.get("code_challenge_method", "S256")

    if not client_id or not redirect_uri:
        return {
            "statusCode": 400,
            "body": json.dumps(
                {
                    "error": "invalid_request",
                    "error_description": "Missing required parameters",
                }
            ),
        }

    # Validate redirect_uri before we trust it enough to redirect errors to it.
    if not is_valid_redirect_uri(redirect_uri):
        return {
            "statusCode": 400,
            "body": json.dumps(
                {
                    "error": "invalid_request",
                    "error_description": "Invalid redirect URI",
                }
            ),
        }

    if response_type != "code":
        return create_error_redirect(redirect_uri, "unsupported_response_type", state)

    # Enforce PKCE S256 (T10): code_challenge is mandatory and must use the S256 method.
    if not code_challenge:
        return create_error_redirect(
            redirect_uri, "invalid_request", state, "PKCE code_challenge is required"
        )
    if code_challenge_method != "S256":
        return create_error_redirect(
            redirect_uri,
            "invalid_request",
            state,
            "Only the S256 code_challenge_method is supported",
        )

    # Handle POST request (form submission).
    if http_method == "POST":
        return handle_authorization_form_submission(event, query_params)

    # Show authorization form (GET request).
    return show_authorization_form(query_params)


def _read_authorization_html() -> Optional[str]:
    """Read the consent form HTML bundled at the mcp package root, or None if missing."""
    html_file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "authorization.html",
    )
    try:
        with open(html_file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None


def _oauth_form_query_string(query_params: dict) -> str:
    """Build the form-action query string preserving the OAuth + PKCE parameters."""
    oauth_params = {
        "response_type": query_params.get("response_type", ""),
        "client_id": query_params.get("client_id", ""),
        "redirect_uri": query_params.get("redirect_uri", ""),
        "code_challenge": query_params.get("code_challenge", ""),
        "code_challenge_method": query_params.get("code_challenge_method", "S256"),
    }
    if query_params.get("state"):
        oauth_params["state"] = query_params.get("state")
    return urllib.parse.urlencode(oauth_params)


def show_authorization_form(query_params: dict) -> dict:
    """Show HTML form for API key input and authorization consent."""
    query_string = _oauth_form_query_string(query_params)

    html_content = _read_authorization_html()
    if html_content is not None:
        html_content = html_content.replace(
            'action="/authorize"', f'action="/authorize?{query_string}"'
        )
    else:
        html_content = (
            "<!DOCTYPE html>\n<html><head><title>Authorization</title></head>\n"
            "<body><h1>Authorization form not found</h1>\n"
            "<p>Please check that authorization.html exists in the project root.</p>\n"
            "</body></html>"
        )

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/html; charset=utf-8",
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
        },
        "body": html_content,
    }


def handle_authorization_form_submission(event: dict, query_params: dict) -> dict:
    """Handle form submission with API key and complete the OAuth flow.

    Mints a short-TTL (<=60s) **encrypted** authorization code carrying the Fernet-encrypted
    apikey. Single-use is not enforceable statelessly; the short TTL plus mandatory PKCE
    (the code_verifier binds the exchange to the original client) is the mitigation.
    """
    body = event.get("body", "")
    if isinstance(body, str):
        try:
            if body.startswith("{"):
                form_data = json.loads(body)
            else:
                form_data = dict(urllib.parse.parse_qsl(body))
        except (json.JSONDecodeError, ValueError):
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {
                        "error": "invalid_request",
                        "error_description": "Malformed request body",
                    }
                ),
            }
    else:
        form_data = body or {}

    api_key = form_data.get("api_key", "").strip()
    if not api_key:
        return show_authorization_form_with_error(query_params, "API key is required")

    client_id = query_params.get("client_id")
    redirect_uri = query_params.get("redirect_uri")
    state = query_params.get("state")
    code_challenge = query_params.get("code_challenge")

    # Encrypted, short-lived authorization code. The apikey is Fernet-encrypted; the JWT
    # envelope carries the binding claims and a <=60s exp.
    encoded_code = encode_token(
        {
            "typ": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "code_challenge": code_challenge,
            "enc_apikey": encrypt_apikey(api_key),
        },
        AUTH_CODE_TTL,
    )

    redirect_params = {"code": encoded_code}
    if state:
        redirect_params["state"] = state

    redirect_url = f"{redirect_uri}?{urllib.parse.urlencode(redirect_params)}"

    return {
        "statusCode": 302,
        "headers": {
            "Location": redirect_url,
            "Cache-Control": "no-store",
            "Pragma": "no-cache",
        },
    }


def show_authorization_form_with_error(query_params: dict, error_message: str) -> dict:
    """Show authorization form with error message."""
    query_string = _oauth_form_query_string(query_params)

    html_content = _read_authorization_html()
    if html_content is not None:
        html_content = html_content.replace(
            'action="/authorize"', f'action="/authorize?{query_string}"'
        )
        html_content = html_content.replace(
            'error_message">', f'error_message">{error_message}'
        )
        html_content = html_content.replace(
            'class="hidden"', 'class=""', 1
        )  # Show error box
    else:
        html_content = (
            "<!DOCTYPE html>\n<html><head><title>Authorization Error</title></head>\n"
            f"<body><h1>Authorization Error</h1>\n<p>{error_message}</p>\n"
            "<p>Please check that authorization.html exists in the project root.</p>\n"
            "</body></html>"
        )

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/html; charset=utf-8",
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
        },
        "body": html_content,
    }


def handle_token_request(event: dict) -> dict:
    """Handle OAuth 2.1 token exchange requests."""
    body = event.get("body", "")
    if isinstance(body, str):
        try:
            if body.startswith("{"):
                params = json.loads(body)
            else:
                params = dict(urllib.parse.parse_qsl(body))
        except (json.JSONDecodeError, ValueError):
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {
                        "error": "invalid_request",
                        "error_description": "Malformed request body",
                    }
                ),
            }
    else:
        params = body or {}

    grant_type = params.get("grant_type")

    if grant_type == "authorization_code":
        return handle_authorization_code_grant(params)
    elif grant_type == "refresh_token":
        return handle_refresh_token_grant(params)
    else:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "unsupported_grant_type"}),
        }


def _token_response(enc_apikey: str, client_id: Optional[str]) -> dict:
    """Mint an encrypted access + refresh token pair carrying the Fernet-encrypted apikey."""
    access_token = encode_token(
        {
            "typ": "access",
            "client_id": client_id,
            "scope": SCOPE,
            "enc_apikey": enc_apikey,
        },
        ACCESS_TOKEN_TTL,
    )
    refresh_token = encode_token(
        {
            "typ": "refresh",
            "client_id": client_id,
            "scope": SCOPE,
            "enc_apikey": enc_apikey,
        },
        REFRESH_TOKEN_TTL,
    )

    token_response = {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": int(ACCESS_TOKEN_TTL.total_seconds()),
        "refresh_token": refresh_token,
        "scope": SCOPE,
    }

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "Pragma": "no-cache",
        },
        "body": json.dumps(token_response),
    }


def handle_authorization_code_grant(params: dict) -> dict:
    """Handle the authorization_code grant: mint an encrypted access/refresh token pair."""
    code = params.get("code")
    client_id = params.get("client_id")
    redirect_uri = params.get("redirect_uri")
    code_verifier = params.get("code_verifier")

    if not all([code, client_id, redirect_uri]):
        return {
            "statusCode": 400,
            "body": json.dumps(
                {
                    "error": "invalid_request",
                    "error_description": "Missing required parameters",
                }
            ),
        }

    # Decode + validate the encrypted authorization code (signature + exp enforced here).
    try:
        code_data = decode_token(code)
    except jwt.ExpiredSignatureError:
        return {
            "statusCode": 400,
            "body": json.dumps(
                {
                    "error": "invalid_grant",
                    "error_description": "Authorization code expired",
                }
            ),
        }
    except jwt.InvalidTokenError:
        return {
            "statusCode": 400,
            "body": json.dumps(
                {
                    "error": "invalid_grant",
                    "error_description": "Invalid authorization code",
                }
            ),
        }

    if code_data.get("typ") != "code":
        return {
            "statusCode": 400,
            "body": json.dumps(
                {
                    "error": "invalid_grant",
                    "error_description": "Invalid authorization code",
                }
            ),
        }

    if (
        code_data.get("client_id") != client_id
        or code_data.get("redirect_uri") != redirect_uri
    ):
        return {
            "statusCode": 400,
            "body": json.dumps(
                {
                    "error": "invalid_grant",
                    "error_description": "Code validation failed",
                }
            ),
        }

    # Enforce PKCE S256 (T10): code_verifier is mandatory and must match the bound challenge.
    code_challenge = code_data.get("code_challenge")
    if not code_challenge:
        return {
            "statusCode": 400,
            "body": json.dumps(
                {
                    "error": "invalid_grant",
                    "error_description": "Missing PKCE challenge",
                }
            ),
        }
    if not code_verifier:
        return {
            "statusCode": 400,
            "body": json.dumps(
                {
                    "error": "invalid_request",
                    "error_description": "Missing code_verifier",
                }
            ),
        }
    if not verify_pkce_challenge(code_verifier, code_challenge):
        return {
            "statusCode": 400,
            "body": json.dumps(
                {
                    "error": "invalid_grant",
                    "error_description": "PKCE verification failed",
                }
            ),
        }

    enc_apikey = code_data.get("enc_apikey")
    if not enc_apikey:
        return {
            "statusCode": 400,
            "body": json.dumps(
                {
                    "error": "invalid_grant",
                    "error_description": "No API key found in authorization",
                }
            ),
        }

    return _token_response(enc_apikey, client_id)


def handle_refresh_token_grant(params: dict) -> dict:
    """Handle the refresh_token grant: decrypt the refresh token, mint a fresh access token.

    Fully stateless. Stateless caveat: the old refresh token is NOT invalidated (no store to
    record rotation); see plan 2555 T6/T14 deferred items.
    """
    refresh_token = params.get("refresh_token")
    if not refresh_token:
        return {
            "statusCode": 400,
            "body": json.dumps(
                {
                    "error": "invalid_request",
                    "error_description": "Missing refresh_token",
                }
            ),
        }

    try:
        token_data = decode_token(refresh_token)
    except jwt.ExpiredSignatureError:
        return {
            "statusCode": 400,
            "body": json.dumps(
                {"error": "invalid_grant", "error_description": "Refresh token expired"}
            ),
        }
    except jwt.InvalidTokenError:
        return {
            "statusCode": 400,
            "body": json.dumps(
                {"error": "invalid_grant", "error_description": "Invalid refresh token"}
            ),
        }

    if token_data.get("typ") != "refresh":
        return {
            "statusCode": 400,
            "body": json.dumps(
                {"error": "invalid_grant", "error_description": "Invalid refresh token"}
            ),
        }

    enc_apikey = token_data.get("enc_apikey")
    if not enc_apikey:
        return {
            "statusCode": 400,
            "body": json.dumps(
                {"error": "invalid_grant", "error_description": "Invalid refresh token"}
            ),
        }

    return _token_response(enc_apikey, token_data.get("client_id"))


def handle_registration_request(event: dict) -> dict:
    """Handle dynamic client registration requests (RFC 7591).

    Stateless caveat (T12): the registered redirect_uris are NOT persisted, so later
    authorization requests validate redirect_uri by rule (see ``is_valid_redirect_uri``)
    rather than against a stored per-client allowlist.
    """
    try:
        body = event.get("body", "")
        if isinstance(body, str):
            registration_request = json.loads(body) if body else {}
        else:
            registration_request = body or {}
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "body": json.dumps(
                {"error": "invalid_request", "error_description": "Malformed JSON"}
            ),
        }

    client_id = f"mcp-client-{secrets.token_urlsafe(16)}"

    redirect_uris = registration_request.get("redirect_uris", [])
    for uri in redirect_uris:
        if not is_valid_redirect_uri(uri):
            return {
                "statusCode": 400,
                "body": json.dumps(
                    {
                        "error": "invalid_redirect_uri",
                        "error_description": f"Invalid redirect URI: {uri}",
                    }
                ),
            }

    registration_response = {
        "client_id": client_id,
        "client_id_issued_at": int(time.time()),  # Real Unix timestamp (T12 fix).
        "redirect_uris": redirect_uris or ["http://localhost:8080/callback"],
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none",  # Public client.
    }

    return {
        "statusCode": 201,
        "headers": {
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
        },
        "body": json.dumps(registration_response),
    }


def create_error_redirect(
    redirect_uri: str,
    error: str,
    state: Optional[str] = None,
    error_description: Optional[str] = None,
) -> dict:
    """Create error redirect response."""
    if not redirect_uri:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": error}),
        }

    error_params = {"error": error}
    if error_description:
        error_params["error_description"] = error_description
    if state:
        error_params["state"] = state

    redirect_url = f"{redirect_uri}?{urllib.parse.urlencode(error_params)}"

    return {
        "statusCode": 302,
        "headers": {
            "Location": redirect_url,
            "Cache-Control": "no-store",
            "Pragma": "no-cache",
        },
    }
