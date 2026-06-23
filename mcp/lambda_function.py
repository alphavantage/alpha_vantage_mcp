import json
from awslabs.mcp_lambda_handler import MCPLambdaHandler
from loguru import logger
from av_api.context import set_api_key
from av_mcp.decorators import setup_custom_tool_decorator
import av_mcp.common  # noqa: F401 — registers response processor for large responses
from av_mcp.tools.registry import (
    register_meta_tools,
    get_tool_list,
    get_tool_schema,
    get_tool_schemas,
)
from av_mcp.tools.meta_tools import (
    META_TOOL_OUTPUT_SCHEMA,
    build_structured_content,
)
from av_mcp.utils import (
    parse_token_from_request,
    create_oauth_error_response,
    extract_client_platform,
    parse_and_log_mcp_analytics,
)
from av_mcp.oauth import (
    handle_metadata_discovery,
    handle_protected_resource_metadata,
    handle_authorization_request,
    handle_token_request,
    handle_registration_request,
)
from av_mcp.tokens import decode_access_token, TokenConfigError


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


def _meta_tool_structured(tool_name: str, arguments: dict, content: list) -> dict | None:
    """Build a meta-tool call's structuredContent (matching its declared outputSchema).

    TOOL_LIST/TOOL_GET re-read the in-process tool registry (pure, no network). TOOL_CALL
    reuses the already-computed text content (which reflects large-response processing)
    instead of re-running the proxied data tool.
    """
    if tool_name == "TOOL_LIST":
        return build_structured_content(tool_name, get_tool_list())
    if tool_name == "TOOL_GET":
        tn = arguments.get("tool_name")
        if not tn:
            return None
        raw = get_tool_schemas(tn) if isinstance(tn, list) else get_tool_schema(tn)
        return build_structured_content(tool_name, raw)
    # TOOL_CALL: derive from the returned text content.
    text = next(
        (c.get("text") for c in content if isinstance(c, dict) and c.get("type") == "text"),
        None,
    )
    if text is None:
        return None
    return build_structured_content(tool_name, text)


def add_meta_tool_structured_content(parsed_request: dict, response: dict) -> None:
    """Inject structuredContent into a tools/call response (in place).

    The awslabs handler only emits `content`, but each meta-tool declares an outputSchema,
    and MCP requires structuredContent whenever outputSchema is declared.
    """
    if not isinstance(parsed_request, dict) or parsed_request.get("method") != "tools/call":
        return
    params = parsed_request.get("params") or {}
    tool_name = params.get("name")
    if tool_name not in META_TOOL_OUTPUT_SCHEMA:
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
    ):
        return
    structured = _meta_tool_structured(tool_name, params.get("arguments") or {}, result["content"])
    if structured is None:
        return
    result["structuredContent"] = structured
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
    """Create and configure MCP handler with meta-tools for progressive discovery."""
    mcp = MCPLambdaHandler(name="alphavantage-mcp-server", version="1.0.0")

    # Set up custom tool decorator for UPPER_SNAKE_CASE tool names
    setup_custom_tool_decorator(mcp)

    # Progressive discovery mode: only register meta-tools
    logger.info("Registering meta-tools for progressive discovery")
    register_meta_tools(mcp)

    return mcp


def lambda_handler(event, context):
    """AWS Lambda handler function."""
    # Log incoming request details
    method = event.get("httpMethod", "UNKNOWN")
    path = event.get("path", "/")
    headers = event.get("headers", {})
    body = event.get("body", "")

    # Log only the request line. Do NOT log Headers (Authorization: Bearer ...),
    # Query parameters (?apikey=...), or Body — they carry credentials that must
    # never reach CloudWatch (Software Directory Policy 1.C/1.D).
    logger.info(f"Incoming request: {method} {path}")

    # Handle OAuth 2.1 endpoints first (before token validation). The token-minting endpoints
    # (/authorize POST, /token) require the OAuth keys; surface unset keys as a clean 500.
    if path in (
        "/.well-known/oauth-authorization-server",
        "/.well-known/oauth-protected-resource",
        "/authorize",
        "/token",
        "/register",
    ):
        try:
            if path == "/.well-known/oauth-authorization-server":
                return handle_metadata_discovery(event)
            elif path == "/.well-known/oauth-protected-resource":
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
    # - tools/call: add structuredContent for meta-tools (the awslabs handler emits only
    #   `content`, but each meta-tool declares an outputSchema).
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
                add_meta_tool_structured_content(parsed, response)

    return response
