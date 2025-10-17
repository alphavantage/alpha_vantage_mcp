import inspect
import json
from typing import Any, Union, get_type_hints

from loguru import logger

from src.tools.registry import get_tools_by_categories


def python_type_to_openapi_type(python_type):
    """Convert Python type hints to OpenAPI types."""
    type_mapping = {
        str: ("string", None),
        int: ("integer", None),
        float: ("number", None),
        bool: ("boolean", None),
        list: ("array", None),
        dict: ("object", None),
    }

    # Handle Optional types
    if hasattr(python_type, "__origin__"):
        if python_type.__origin__ is Union:
            # For Optional[X], get the non-None type
            args = [arg for arg in python_type.__args__ if arg is not None]
            if args:
                return python_type_to_openapi_type(args[0])
        elif python_type.__origin__ is list:
            return ("array", None)
        elif python_type.__origin__ is dict:
            return ("object", None)

    # Default mapping
    return type_mapping.get(python_type, ("string", None))


def load_all_tools(categories: list[str] | None = None):
    """Load all tools and return them as a list, optionally filtered by categories."""
    return get_tools_by_categories(categories)


def generate_openapi_schema(
    base_url: str = "https://your-api-gateway-url.amazonaws.com",
    categories: list[str] | None = None,
) -> dict:
    """Generate OpenAPI schema for all MCP tools, optionally filtered by categories."""
    tools = load_all_tools(categories)

    paths = {}

    for func in tools:
        func_name = func.__name__
        # Capitalize all characters in function name for schema display
        display_name = func_name.upper()
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)

        # Build request body properties
        request_body_properties = {}
        required_params = []

        # Always add apikey as an optional property for authentication
        request_body_properties["apikey"] = {
            "type": "string",
            "description": "Alpha Vantage API key for authentication (optional - can also be provided via query parameter or Authorization header)",
        }

        for param_name, param in sig.parameters.items():
            param_type = type_hints.get(param_name, str)
            openapi_type, format_type = python_type_to_openapi_type(param_type)

            # Check if parameter has a default value
            has_default = param.default != inspect.Parameter.empty

            # For OpenAI Actions, we'll use request body for all parameters
            param_schema = {"type": openapi_type}
            if format_type:
                param_schema["format"] = format_type

            # Add description from docstring if available
            if func.__doc__:
                # Parse docstring for parameter descriptions
                lines = func.__doc__.split("\n")
                for line in lines:
                    if param_name in line and ":" in line:
                        desc = line.split(":", 1)[1].strip()
                        param_schema["description"] = desc
                        break

            request_body_properties[param_name] = param_schema

            if not has_default:
                required_params.append(param_name)

        # Create the path entry
        # Process description to meet 300 character limit
        description = func.__doc__ if func.__doc__ else f"Execute the {display_name} function"
        if len(description) > 300:
            # Remove newlines and extra spaces
            description = " ".join(description.split())
            # Remove Args section if still too long
            if len(description) > 300 and "Args:" in description:
                parts = description.split("Args:")
                # Keep the part before Args and after Returns if exists
                if "Returns:" in description:
                    returns_part = description.split("Returns:")[1]
                    description = parts[0].strip() + " Returns: " + returns_part.strip()
                else:
                    description = parts[0].strip()
            # Remove Returns section if still too long
            if len(description) > 300 and "Returns:" in description:
                description = description.split("Returns:")[0].strip()
            # Truncate if still too long
            if len(description) > 300:
                description = description[:297] + "..."

        path_entry = {
            "post": {
                "summary": (
                    func.__doc__.split("\n")[0] if func.__doc__ else f"Execute {display_name}"
                ),
                "description": description,
                "operationId": display_name,
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": request_body_properties,
                                "required": required_params,
                            }
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "result": {
                                            "type": "string",
                                            "description": "The function result",
                                        }
                                    },
                                }
                            }
                        },
                    },
                    "400": {"description": "Bad request"},
                    "500": {"description": "Internal server error"},
                },
            }
        }

        paths[f"/openai/{display_name}"] = path_entry

    # Build the complete OpenAPI schema
    schema = {
        "openapi": "3.1.0",
        "info": {
            "title": "Alpha Vantage MCP Tools API",
            "description": "OpenAI Actions compatible API for Alpha Vantage MCP tools",
            "version": "1.0.0",
        },
        "servers": [{"url": base_url}],
        "paths": paths,
        "components": {"schemas": {}},
    }

    return schema


def execute_tool(function_name: str, params: dict, categories: list[str] | None = None) -> Any:
    """Execute a tool function by name with given parameters, optionally filtered by categories."""
    tools = load_all_tools(categories)

    # Find the function (case-insensitive comparison)
    for func in tools:
        if func.__name__.lower() == function_name.lower():
            try:
                # Execute the function with provided parameters
                result = func(**params)
                return result
            except Exception as e:
                logger.error(f"Error executing {function_name}: {e}")
                raise

    raise ValueError(f"Function {function_name} not found")


def handle_openai_request(event: dict, categories: list[str] | None = None) -> dict:
    """Handle OpenAI Actions API requests."""
    path = event.get("path", "/")
    method = event.get("httpMethod", "GET")

    # Handle /openai endpoint - return schema
    if path == "/openai" and method == "GET":
        # Get base URL from event
        domain = event.get("requestContext", {}).get(
            "domainName", "your-api-gateway-url.amazonaws.com"
        )
        base_url = f"https://{domain}"

        schema = generate_openapi_schema(base_url, categories)

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps(schema),
        }

    # Handle /openai/{function_name} endpoints - execute tools
    if path.startswith("/openai/") and method == "POST":
        function_name = path.split("/")[-1]

        try:
            # Parse request body
            body = json.loads(event.get("body", "{}"))

            # Remove apikey from body params if present (it's for auth, not a tool param)
            params = {k: v for k, v in body.items() if k != "apikey"}

            # Execute the tool with category filtering
            result = execute_tool(function_name, params, categories)

            # Format response
            response_body = {"result": result if isinstance(result, str) else json.dumps(result)}

            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": json.dumps(response_body),
            }

        except ValueError as e:
            return {
                "statusCode": 404,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"error": str(e)}),
            }
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"error": "Internal server error"}),
            }

    # Handle OPTIONS for CORS
    if method == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            },
            "body": "",
        }

    # Return None to indicate this request should be handled elsewhere
    return None
