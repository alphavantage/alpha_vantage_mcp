import base64
import json
import urllib.request
from awslabs.mcp_lambda_handler import MCPLambdaHandler
from loguru import logger
from av_api.context import set_api_key
from av_mcp.decorators import setup_custom_tool_decorator
import av_mcp.common  # noqa: F401 — registers response processor for large responses
from av_mcp.tools.registry import register_meta_tools
from av_mcp.utils import parse_token_from_request, create_oauth_error_response, extract_client_platform, parse_and_log_mcp_analytics, get_base_url
from av_mcp.oauth import handle_metadata_discovery, handle_authorization_request, handle_token_request, handle_registration_request

_LOGO_URL = "https://cdn.alphavantage.co/logo.png"
_LOGO_B64: str | None = None


def _get_logo_b64() -> str:
    global _LOGO_B64
    if _LOGO_B64 is None:
        with urllib.request.urlopen(_LOGO_URL, timeout=5) as r:
            _LOGO_B64 = base64.b64encode(r.read()).decode("ascii")
    return _LOGO_B64


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
    query_params = event.get("queryStringParameters", {})

    logger.info(f"Incoming request: {method} {path}")
    logger.info(f"Headers: {headers}")
    logger.info(f"Query parameters: {query_params}")
    logger.info(f"Body: {body}")

    # Proxy logo/favicon from CDN as same-origin content (no redirect).
    # MCP spec requires icon URIs to be same-origin as the server; a 302 to a
    # different origin is rejected by strict clients (e.g. ChatGPT connector).
    if path in ("/favicon.ico", "/logo.png"):
        try:
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "image/png",
                    "Cache-Control": "public, max-age=86400"
                },
                "body": _get_logo_b64(),
                "isBase64Encoded": True
            }
        except Exception as e:
            logger.error(f"Failed to proxy logo: {e}")
            return {"statusCode": 502, "body": ""}

    # Handle OAuth 2.1 endpoints first (before token validation)
    if path == "/.well-known/oauth-authorization-server":
        return handle_metadata_discovery(event)
    elif path == "/authorize":
        return handle_authorization_request(event)
    elif path == "/token":
        return handle_token_request(event)
    elif path == "/register":
        return handle_registration_request(event)

    # Extract Bearer token from Authorization header
    token = parse_token_from_request(event)

    # Validate token presence for MCP/API requests
    if not token:
        return create_oauth_error_response({
            "error": "invalid_request",
            "error_description": "Missing access token",
            "error_uri": "https://tools.ietf.org/html/rfc6750#section-3.1"
        }, 401)

    # Set token in context for tools to access
    set_api_key(token)

    # GET /mcp is used by MCP clients to open an SSE stream for server notifications.
    # Lambda doesn't support SSE, so return 405 to stop clients from retrying.
    # NOTE: Do NOT return 204 here — clients treat it as a successful SSE connection
    # and will retry endlessly, causing massive request volume.
    if method == "GET":
        return {
            "statusCode": 405,
            "headers": {"Allow": "POST"},
            "body": json.dumps({"error": "SSE not supported, use POST for MCP requests"})
        }

    # Parse and log MCP method and params for analytics (after token parsing)
    if method == "POST":
        # Extract client platform information
        platform = extract_client_platform(event)

        # Log MCP analytics
        parse_and_log_mcp_analytics(body, token, platform)

    # Handle MCP requests
    mcp = create_mcp_handler()

    response = mcp.handle_request(event, context)

    # Post-process initialize response:
    # - Remove hardcoded `resources` capability (we only provide tools)
    # - Inject branding (title/icons/websiteUrl) into serverInfo
    #   per MCP 2025-06-18 Implementation fields; SDK allows extra fields.
    if method == "POST" and body:
        try:
            parsed = json.loads(body) if isinstance(body, str) else body
            if parsed.get("method") == "initialize":
                resp_body = json.loads(response["body"])
                result = resp_body.get("result", {})
                result.get("capabilities", {}).pop("resources", None)
                server_info = result.setdefault("serverInfo", {})
                server_info["title"] = "Alpha Vantage"
                server_info["icons"] = [{
                    "src": f"{get_base_url(event)}/logo.png",
                    "mimeType": "image/png",
                    "sizes": ["any"]
                }]
                server_info["websiteUrl"] = "https://www.alphavantage.co"
                response["body"] = json.dumps(resp_body)
        except (json.JSONDecodeError, TypeError, KeyError):
            pass

    return response
