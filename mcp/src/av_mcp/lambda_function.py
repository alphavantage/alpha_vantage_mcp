from awslabs.mcp_lambda_handler import MCPLambdaHandler
from loguru import logger
from av_api.context import set_api_key
from .tools.registry import register_meta_tools
from .utils import parse_token_from_request, create_oauth_error_response, extract_client_platform, parse_and_log_mcp_analytics
from .oauth import handle_metadata_discovery, handle_authorization_request, handle_token_request, handle_registration_request


def create_mcp_handler() -> MCPLambdaHandler:
    """Create and configure MCP handler with meta-tools for progressive discovery."""
    mcp = MCPLambdaHandler(name="mcp-lambda-server", version="1.0.0")

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

    # Parse and log MCP method and params for analytics (after token parsing)
    if method == "POST":
        # Extract client platform information
        platform = extract_client_platform(event)

        # Log MCP analytics
        parse_and_log_mcp_analytics(body, token, platform)

    # Handle MCP requests
    mcp = create_mcp_handler()

    return mcp.handle_request(event, context)
