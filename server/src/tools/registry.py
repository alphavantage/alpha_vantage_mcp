# Re-export shared tool infrastructure from av_api
from av_api.registry import (  # noqa: F401
    tool,
    load_all_tools,
    get_tool_list,
    get_tool_schema,
    get_tool_schemas,
    call_tool,
    extract_description,
)


def register_all_tools(mcp):
    """Register all decorated tools with MCP server."""
    tools = load_all_tools()
    for func in tools:
        mcp.tool()(func)


def register_all_tools_lazy(mcp):
    """Register all tools with lazy import."""
    register_all_tools(mcp)


def get_all_tools():
    """Get all tools with their MCP tool definitions.

    Returns:
        List of tuples containing (tool_definition, tool_function)
    """
    import mcp.types as types
    import inspect
    from typing import get_type_hints, Union

    tools = load_all_tools()

    result = []
    for func in tools:
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)

        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            param_type = type_hints.get(param_name, str)

            if param_type == str or param_type == 'str':
                schema_type = "string"
            elif param_type == int or param_type == 'int':
                schema_type = "integer"
            elif param_type == float or param_type == 'float':
                schema_type = "number"
            elif param_type == bool or param_type == 'bool':
                schema_type = "boolean"
            elif hasattr(param_type, '__origin__') and param_type.__origin__ is Union:
                args = param_type.__args__
                if len(args) == 2 and type(None) in args:
                    non_none_type = args[0] if args[1] is type(None) else args[1]
                    if non_none_type == str:
                        schema_type = "string"
                    elif non_none_type == int:
                        schema_type = "integer"
                    elif non_none_type == float:
                        schema_type = "number"
                    elif non_none_type == bool:
                        schema_type = "boolean"
                    else:
                        schema_type = "string"
                else:
                    schema_type = "string"
            else:
                schema_type = "string"

            properties[param_name] = {"type": schema_type}

            if func.__doc__:
                lines = func.__doc__.split('\n')
                for line in lines:
                    if param_name in line and ':' in line:
                        desc = line.split(':', 1)[1].strip()
                        if desc:
                            properties[param_name]["description"] = desc
                        break

            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        tool_def = types.Tool(
            name=func.__name__.upper(),
            description=func.__doc__ or f"Execute {func.__name__}",
            inputSchema={
                "type": "object",
                "properties": properties,
                "required": required
            }
        )

        result.append((tool_def, func))

    return result


def register_meta_tools(mcp):
    """Register only the meta-tools (TOOL_LIST, TOOL_GET, TOOL_CALL) for progressive discovery."""
    from src.tools.meta_tools import tool_list, tool_get, tool_call

    for func in [tool_list, tool_get, tool_call]:
        mcp.tool(description=extract_description(func))(func)
