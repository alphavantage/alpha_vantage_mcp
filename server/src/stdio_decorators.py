import inspect


def setup_stdio_tool_decorator(mcp):
    """Set up custom tool decorator for stdio server that converts function names to UPPERCASE_WITH_UNDERSCORES"""

    # Store the original tool method
    original_tool = mcp.tool

    def custom_tool_decorator(name=None, description=None):
        """Custom decorator that converts function names to UPPERCASE_WITH_UNDERSCORES"""

        def decorator(func):
            # Get function name and convert to UPPERCASE_WITH_UNDERSCORES
            func_name = func.__name__
            tool_name = name or func_name.upper()

            # Get docstring and parse into description
            doc = inspect.getdoc(func) or ""
            tool_description = description or doc.split("\n\n")[0]  # First paragraph is description

            # Use the original MCP tool decorator with uppercase name
            return original_tool(name=tool_name, description=tool_description)(func)

        return decorator

    # Replace the tool method
    mcp.tool = custom_tool_decorator
