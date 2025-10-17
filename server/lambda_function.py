from awslabs.mcp_lambda_handler import MCPLambdaHandler
from loguru import logger

from src.context import set_api_key
from src.decorators import setup_custom_tool_decorator
from src.oauth import (
    handle_authorization_request,
    handle_metadata_discovery,
    handle_registration_request,
    handle_token_request,
)
from src.openai_actions import handle_openai_request
from src.tools.registry import register_all_tools, register_tools_by_categories
from src.utils import (
    create_oauth_error_response,
    extract_client_platform,
    parse_and_log_mcp_analytics,
    parse_token_from_request,
    parse_tool_categories_from_request,
)


def create_mcp_handler_for_categories(categories: list[str] | None) -> MCPLambdaHandler:
    """Create and configure MCP handler for specific tool categories."""
    mcp = MCPLambdaHandler(name="mcp-lambda-server", version="1.0.0")

    # Set up custom tool decorator
    setup_custom_tool_decorator(mcp)

    # Register tools based on categories
    if categories:
        logger.info(f"Registering tools for categories: {', '.join(categories)}")
        try:
            register_tools_by_categories(mcp, categories)
        except ValueError as e:
            logger.warning(f"Error with categories {categories}: {e}, registering all tools")
            register_all_tools(mcp)
    else:
        logger.info("Registering all tools")
        register_all_tools(mcp)

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
        return create_oauth_error_response(
            {
                "error": "invalid_request",
                "error_description": "Missing access token",
                "error_uri": "https://tools.ietf.org/html/rfc6750#section-3.1",
            },
            401,
        )

    # Set token in context for tools to access
    set_api_key(token)

    # Parse and log MCP method and params for analytics (after token parsing)
    if method == "POST":
        # Extract client platform information
        platform = extract_client_platform(event)

        # Log MCP analytics
        parse_and_log_mcp_analytics(body, token, platform)

    # Parse tool categories from request path or query parameters
    categories = parse_tool_categories_from_request(event)

    # Check if this is an OpenAI Actions request
    if path.startswith("/openai"):
        response = handle_openai_request(event, categories)
        if response:
            return response

    # Handle MCP requests

    # Create MCP handler with appropriate tools
    mcp = create_mcp_handler_for_categories(categories)

    return mcp.handle_request(event, context)
