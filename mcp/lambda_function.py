import json
from awslabs.mcp_lambda_handler import MCPLambdaHandler
from loguru import logger
from av_api.context import set_api_key, set_client_name
from av_mcp.decorators import setup_custom_tool_decorator
import av_mcp.common  # noqa: F401 — registers response processor for large responses
from av_mcp.tools.registry import register_meta_tools
from av_mcp.utils import parse_token_from_request, create_oauth_error_response, extract_client_platform, parse_and_log_mcp_analytics
from av_mcp.oauth import handle_metadata_discovery, handle_authorization_request, handle_token_request, handle_registration_request


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
    query_params = event.get("queryStringParameters", {})

    logger.info(f"Incoming request: {method} {path}")
    logger.info(f"Headers: {headers}")
    logger.info(f"Query parameters: {query_params}")
    logger.info(f"Body: {body}")

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

    # Parse and log MCP method and params for analytics (after token parsing).
    # Also set the detected client name so the API layer can pick an adaptive
    # default for return_full_data per client capability.
    if method == "POST":
        platform = extract_client_platform(event)
        set_client_name(platform)
        parse_and_log_mcp_analytics(body, token, platform)

    # Handle MCP requests
    normalize_content_type_header(event)
    mcp = create_mcp_handler()

    response = mcp.handle_request(event, context)

    # Remove resources capability from initialize response
    # (MCPLambdaHandler hardcodes it, but we only provide tools)
    if method == "POST" and body:
        try:
            parsed = json.loads(body) if isinstance(body, str) else body
            if parsed.get("method") == "initialize":
                resp_body = json.loads(response["body"])
                resp_body.get("result", {}).get("capabilities", {}).pop("resources", None)
                response["body"] = json.dumps(resp_body)
        except (json.JSONDecodeError, TypeError, KeyError):
            pass

    return response
