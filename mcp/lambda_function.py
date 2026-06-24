import json
from functools import lru_cache
from importlib.resources import files
from awslabs.mcp_lambda_handler import MCPLambdaHandler
from loguru import logger
from av_api.context import set_api_key
from av_mcp.decorators import setup_custom_tool_decorator
import av_mcp.common  # noqa: F401 — registers response processor for large responses
from av_api.registry import build_data_structured_content
from av_mcp.tools.registry import register_all_tools
from av_mcp.utils import (
    parse_token_from_request,
    create_oauth_error_response,
    extract_client_platform,
    parse_and_log_mcp_analytics,
    cors_headers,
)
from av_mcp.oauth import (
    handle_metadata_discovery,
    handle_protected_resource_metadata,
    handle_authorization_request,
    handle_token_request,
    handle_registration_request,
)
from av_mcp.tokens import decode_access_token, TokenConfigError


# Public, no-auth static pages bundled inside the package (todo 2600). The MCP server
# serves its own landing page (/) and artifact viewer (/artifacts) so it no longer
# depends on the CloudFront/S3 static site. Maps request path -> packaged file name.
STATIC_PAGES = {"/": "index.html", "/artifacts": "artifacts.html"}


@lru_cache(maxsize=None)
def _read_static_page(filename: str) -> str:
    """Read a bundled static HTML page from av_mcp/static (cached across warm invocations)."""
    return files("av_mcp").joinpath("static", filename).read_text(encoding="utf-8")


def serve_static_page(path: str) -> dict:
    """Return a bundled static HTML page as a 200 text/html response (public, no auth)."""
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "text/html; charset=utf-8"},
        "body": _read_static_page(STATIC_PAGES[path]),
    }


def oauth_misconfig_response() -> dict:
    """500 for unset OAuth signing/encryption keys (server misconfig, not an auth failure)."""
    logger.error(
        "OAuth signing/encryption keys not configured "
        "(JWT_SECRET_KEY / AV_APIKEY_ENC_KEY)"
    )
    return {
        "statusCode": 500,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(
            {
                "error": "server_error",
                "error_description": "OAuth is not configured on this server",
            }
        ),
    }


def add_data_tool_structured_content(parsed_request: dict, response: dict) -> None:
    """Inject structuredContent into a tools/call response (in place).

    The awslabs handler only emits `content`, but every data tool declares the shared
    DATA_TOOL_OUTPUT_SCHEMA, and MCP requires structuredContent whenever outputSchema is
    declared. The structuredContent is built from the already-returned text content
    (which reflects large-response processing) — it never re-runs the tool. Error results
    are skipped (validation is not applied to isError responses).
    """
    if not isinstance(parsed_request, dict) or parsed_request.get("method") != "tools/call":
        return
    try:
        resp_body = json.loads(response["body"])
    except (json.JSONDecodeError, TypeError, KeyError):
        return
    result = resp_body.get("result")
    if (
        not isinstance(result, dict)
        or "content" not in result
        or "structuredContent" in result
        or result.get("isError")
    ):
        return
    text = next(
        (
            c.get("text")
            for c in result["content"]
            if isinstance(c, dict) and c.get("type") == "text"
        ),
        None,
    )
    if text is None:
        return
    result["structuredContent"] = build_data_structured_content(text)
    response["body"] = json.dumps(resp_body)


def normalize_content_type_header(event):
    """Normalize Content-Type so awslabs handler accepts media-type parameters."""
    headers = event.get("headers")
    if not isinstance(headers, dict):
        return

    for key, value in list(headers.items()):
        if key.lower() != "content-type" or not isinstance(value, str):
            continue

        content_type = value.split(";", 1)[0].strip().lower()
        headers[key] = content_type
        headers["content-type"] = content_type
        return


def create_mcp_handler() -> MCPLambdaHandler:
    """Create and configure MCP handler with the full Alpha Vantage tool catalog."""
    mcp = MCPLambdaHandler(name="alphavantage-mcp-server", version="1.0.0")

    # Set up custom tool decorator for UPPER_SNAKE_CASE tool names
    setup_custom_tool_decorator(mcp)

    # Register the full catalog of real Alpha Vantage tools directly
    register_all_tools(mcp)
    logger.info(f"Registered {len(mcp.tools)} Alpha Vantage tools")

    return mcp


def _merge_cors_headers(response):
    """Add CORS headers to a Lambda response without clobbering stricter existing values.

    setdefault semantics: a handler that already set a header (e.g. Access-Control-Allow-Origin
    on the metadata endpoints) keeps its value; everything else gets the central cors_headers().
    """
    if not isinstance(response, dict):
        return response
    headers = response.get("headers")
    if not isinstance(headers, dict):
        headers = {}
        response["headers"] = headers
    for key, value in cors_headers().items():
        headers.setdefault(key, value)
    return response


def lambda_handler(event, context):
    """AWS Lambda entry point: CORS preflight short-circuit + central CORS merge."""
    method = event.get("httpMethod", "UNKNOWN")
    path = event.get("path", "/")

    # Log only the request line. Do NOT log Headers (Authorization: Bearer ...),
    # Query parameters (?apikey=...), or Body — they carry credentials that must
    # never reach CloudWatch (Software Directory Policy 1.C/1.D).
    logger.info(f"Incoming request: {method} {path}")

    # CORS preflight: short-circuit OPTIONS for ANY path before auth/routing (todo 2583).
    # Covers /.well-known/*, /token, /register, /authorize, and /mcp in one place.
    if method == "OPTIONS":
        return {"statusCode": 204, "headers": cors_headers(), "body": ""}

    return _merge_cors_headers(_handle_request(event, context))


def _handle_request(event, context):
    """Resolve the caller's credential and dispatch (OAuth endpoints, MCP, errors)."""
    method = event.get("httpMethod", "UNKNOWN")
    path = event.get("path", "/")
    headers = event.get("headers", {})
    body = event.get("body", "")

    # Public static pages (before token validation): the landing page and the artifact
    # viewer are public, so serve them without a credential. Only intercept GET on exactly
    # / and /artifacts; every other path keeps its current behavior (todo 2600).
    if method == "GET" and path in STATIC_PAGES:
        return serve_static_page(path)

    # Handle OAuth 2.1 endpoints first (before token validation). The token-minting endpoints
    # (/authorize POST, /token) require the OAuth keys; surface unset keys as a clean 500.
    # Protected Resource Metadata: RFC 9728 inserts the resource path after the
    # well-known segment, so for the `/mcp` resource the canonical location is
    # `/.well-known/oauth-protected-resource/mcp`. Serve both the path-aware
    # form (spec-correct) and the bare form (backwards-compatible) so clients
    # and proxies resolve metadata regardless of which they request.
    protected_resource_paths = (
        "/.well-known/oauth-protected-resource",
        "/.well-known/oauth-protected-resource/mcp",
    )
    if path in (
        "/.well-known/oauth-authorization-server",
        *protected_resource_paths,
        "/authorize",
        "/token",
        "/register",
    ):
        try:
            if path == "/.well-known/oauth-authorization-server":
                return handle_metadata_discovery(event)
            elif path in protected_resource_paths:
                return handle_protected_resource_metadata(event)
            elif path == "/authorize":
                return handle_authorization_request(event)
            elif path == "/token":
                return handle_token_request(event)
            else:
                return handle_registration_request(event)
        except TokenConfigError:
            return oauth_misconfig_response()

    # Resolve the caller's credential. Bearer takes precedence: an Authorization: Bearer token
    # is an encrypted OAuth access token, validated by jwt.decode (signature + exp) + Fernet
    # decrypt of the apikey claim (no store lookup). If no Bearer is present, fall back to the
    # raw apikey supplied via ?apikey= query or request body (direct-apikey callers, non-breaking).
    auth_header = headers.get("Authorization") or headers.get("authorization")
    bearer = (
        auth_header[7:] if auth_header and auth_header.startswith("Bearer ") else ""
    )

    if bearer:
        # Reject malformed/expired/tampered access tokens with 401 (T4). Unset keys -> 500.
        try:
            api_key = decode_access_token(bearer)
        except TokenConfigError:
            return oauth_misconfig_response()
        if not api_key:
            return create_oauth_error_response(
                {
                    "error": "invalid_token",
                    "error_description": "The access token is invalid or expired",
                    "error_uri": "https://tools.ietf.org/html/rfc6750#section-3.1",
                },
                401,
            )
    else:
        # Raw apikey via query/body (direct-apikey callers).
        api_key = parse_token_from_request(event)
        if not api_key:
            return create_oauth_error_response(
                {
                    "error": "invalid_request",
                    "error_description": "Missing access token",
                    "error_uri": "https://tools.ietf.org/html/rfc6750#section-3.1",
                },
                401,
            )

    # Set the resolved apikey in context for tools to access
    set_api_key(api_key)

    # GET /mcp is used by MCP clients to open an SSE stream for server notifications.
    # Lambda doesn't support SSE, so return 405 to stop clients from retrying.
    # NOTE: Do NOT return 204 here — clients treat it as a successful SSE connection
    # and will retry endlessly, causing massive request volume.
    if method == "GET":
        return {
            "statusCode": 405,
            "headers": {"Allow": "POST"},
            "body": json.dumps(
                {"error": "SSE not supported, use POST for MCP requests"}
            ),
        }

    # Parse and log MCP method and params for analytics (after token parsing)
    if method == "POST":
        # Extract client platform information
        platform = extract_client_platform(event)

        # Log MCP analytics
        parse_and_log_mcp_analytics(body, api_key, platform)

    # Handle MCP requests
    normalize_content_type_header(event)
    mcp = create_mcp_handler()

    response = mcp.handle_request(event, context)

    # Post-process the response:
    # - initialize: drop the resources capability (MCPLambdaHandler hardcodes it, we only
    #   provide tools).
    # - tools/call: add structuredContent (the awslabs handler emits only `content`, but
    #   every data tool declares an outputSchema).
    if method == "POST" and body:
        try:
            parsed = json.loads(body) if isinstance(body, str) else body
        except (json.JSONDecodeError, TypeError):
            parsed = None
        if isinstance(parsed, dict):
            if parsed.get("method") == "initialize":
                try:
                    resp_body = json.loads(response["body"])
                    resp_body.get("result", {}).get("capabilities", {}).pop(
                        "resources", None
                    )
                    response["body"] = json.dumps(resp_body)
                except (json.JSONDecodeError, TypeError, KeyError):
                    pass
            elif parsed.get("method") == "tools/call":
                add_data_tool_structured_content(parsed, response)

    return response
