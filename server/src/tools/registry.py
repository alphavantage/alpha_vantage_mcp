import functools
import inspect
from typing import Union, get_type_hints

# Tool module mapping with lazy imports
TOOL_MODULES = {
    "core_stock_apis": "src.tools.core_stock_apis",
    "options_data_apis": "src.tools.options_data_apis",
    "alpha_intelligence": "src.tools.alpha_intelligence",
    "commodities": "src.tools.commodities",
    "cryptocurrencies": "src.tools.cryptocurrencies",
    "economic_indicators": "src.tools.economic_indicators",
    "forex": "src.tools.forex",
    "fundamental_data": "src.tools.fundamental_data",
    "technical_indicators": [
        "src.tools.technical_indicators_part1",
        "src.tools.technical_indicators_part2",
        "src.tools.technical_indicators_part3",
        "src.tools.technical_indicators_part4",
    ],
    "ping": "src.tools.ping",
    "openai": "src.tools.openai",
}

# Categories that should have entitlement parameter added
ENTITLEMENT_CATEGORIES = {"core_stock_apis", "options_data_apis", "technical_indicators"}

# Registry for decorated tools by category
_tool_registries = {}
_all_tools_registry = []


def add_entitlement_parameter(func):
    """Decorator that adds entitlement parameter to a function"""

    # Get existing signature and type hints
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)

    # Create new parameter for entitlement
    entitlement_param = inspect.Parameter(
        "entitlement", inspect.Parameter.KEYWORD_ONLY, default=None, annotation="str | None"
    )

    # Add entitlement parameter to the signature
    params = list(sig.parameters.values())
    params.append(entitlement_param)
    new_sig = sig.replace(parameters=params)

    # Update docstring to include entitlement parameter
    docstring = func.__doc__ or ""
    if "Args:" in docstring and "entitlement" not in docstring:
        # Find the Args section and add entitlement parameter
        lines = docstring.split("\n")
        args_idx = None
        returns_idx = None

        for i, line in enumerate(lines):
            if "Args:" in line:
                args_idx = i
            elif "Returns:" in line and args_idx is not None:
                returns_idx = i
                break

        if args_idx is not None:
            entitlement_doc = '        entitlement: "delayed" for 15-minute delayed data, "realtime" for realtime data'
            if returns_idx is not None:
                lines.insert(returns_idx, entitlement_doc)
                lines.insert(returns_idx, "")
            else:
                lines.append(entitlement_doc)

            func.__doc__ = "\n".join(lines)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Extract entitlement if provided - it will be passed through params to _make_api_request
        entitlement = kwargs.pop("entitlement", None)

        # Call the original function, passing entitlement through a global variable
        if entitlement:
            # Set global variable that _make_api_request can check
            import src.common

            src.common._current_entitlement = entitlement
            try:
                result = func(*args, **kwargs)
            finally:
                src.common._current_entitlement = None
            return result

        return func(*args, **kwargs)

    # Apply the new signature to the wrapper
    wrapper.__signature__ = new_sig
    wrapper.__annotations__ = {**type_hints, "entitlement": "str | None"}

    return wrapper


def tool(func):
    """Decorator to mark functions as MCP tools"""
    # Determine which module/category this function belongs to
    module_name = func.__module__.split(".")[-1]  # Get last part of module name

    # Determine the category from the module name
    category = None
    for cat, module_spec in TOOL_MODULES.items():
        if isinstance(module_spec, list):
            # For technical_indicators which has multiple modules
            for mod_path in module_spec:
                if mod_path.split(".")[-1] == module_name:
                    category = cat
                    break
        else:
            # For single module categories
            if module_spec.split(".")[-1] == module_name:
                category = cat
                break

    # Apply entitlement decorator if this category needs it
    if category in ENTITLEMENT_CATEGORIES:
        func = add_entitlement_parameter(func)

    if module_name not in _tool_registries:
        _tool_registries[module_name] = []

    _tool_registries[module_name].append(func)
    _all_tools_registry.append(func)
    return func


def register_all_tools(mcp):
    """Register all decorated tools"""
    # Import all modules to trigger decoration
    import importlib

    for module_spec in TOOL_MODULES.values():
        if isinstance(module_spec, list):
            for module_name in module_spec:
                importlib.import_module(module_name)
        else:
            importlib.import_module(module_spec)

    # Register all decorated tools
    for func in _all_tools_registry:
        mcp.tool()(func)


def get_tools_by_categories(categories=None):
    """Get tools filtered by categories, importing modules as needed"""
    import importlib

    if not categories:
        # Import all modules and return all tools
        for module_spec in TOOL_MODULES.values():
            if isinstance(module_spec, list):
                for module_name in module_spec:
                    importlib.import_module(module_name)
            else:
                importlib.import_module(module_spec)
        return _all_tools_registry

    # Validate all categories first
    invalid_categories = [cat for cat in categories if cat not in TOOL_MODULES]
    if invalid_categories:
        raise ValueError(f"Unknown tool categories: {', '.join(invalid_categories)}")

    # Import specified category modules to trigger decoration
    for category in categories:
        if category in TOOL_MODULES:
            module_spec = TOOL_MODULES[category]
            if isinstance(module_spec, list):
                for module_name in module_spec:
                    importlib.import_module(module_name)
            else:
                importlib.import_module(module_spec)

    # Collect tools from specified categories
    filtered_tools = []
    for category in categories:
        # Map category to module name(s) and get tools from registry
        if category in TOOL_MODULES:
            module_spec = TOOL_MODULES[category]
            if isinstance(module_spec, list):
                # For technical_indicators which has multiple modules
                for module_path in module_spec:
                    module_name = module_path.split(".")[-1]
                    if module_name in _tool_registries:
                        filtered_tools.extend(_tool_registries[module_name])
            else:
                # For single module categories
                module_name = module_spec.split(".")[-1]
                if module_name in _tool_registries:
                    filtered_tools.extend(_tool_registries[module_name])

    return filtered_tools


def register_tools_by_categories(mcp, categories):
    """Register tools from multiple categories"""
    tools = get_tools_by_categories(categories)
    for func in tools:
        mcp.tool()(func)


def get_all_tools(categories=None):
    """Get all tools with their MCP tool definitions

    Args:
        categories: Optional list of categories to filter by

    Returns:
        List of tuples containing (tool_definition, tool_function)
    """
    import inspect
    from typing import get_type_hints

    import mcp.types as types

    # Get the tools from specified categories
    tools = get_tools_by_categories(categories)

    result = []
    for func in tools:
        # Create MCP tool definition from function
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)

        # Build parameters schema
        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            param_type = type_hints.get(param_name, str)

            # Convert Python types to JSON schema types
            if param_type is str or param_type == "str":
                schema_type = "string"
            elif param_type is int or param_type == "int":
                schema_type = "integer"
            elif param_type is float or param_type == "float":
                schema_type = "number"
            elif param_type is bool or param_type == "bool":
                schema_type = "boolean"
            elif hasattr(param_type, "__origin__") and param_type.__origin__ is Union:
                # Handle Optional types (Union with None)
                args = param_type.__args__
                if len(args) == 2 and type(None) in args:
                    non_none_type = args[0] if args[1] is type(None) else args[1]
                    if non_none_type is str:
                        schema_type = "string"
                    elif non_none_type is int:
                        schema_type = "integer"
                    elif non_none_type is float:
                        schema_type = "number"
                    elif non_none_type is bool:
                        schema_type = "boolean"
                    else:
                        schema_type = "string"
                else:
                    schema_type = "string"
            else:
                schema_type = "string"

            properties[param_name] = {"type": schema_type}

            # Add description from docstring if available
            if func.__doc__:
                # Try to extract parameter description from docstring
                lines = func.__doc__.split("\n")
                for line in lines:
                    if param_name in line and ":" in line:
                        desc = line.split(":", 1)[1].strip()
                        if desc:
                            properties[param_name]["description"] = desc
                        break

            # Mark as required if no default value
            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        # Create the tool definition
        tool_def = types.Tool(
            name=func.__name__.upper(),
            description=func.__doc__ or f"Execute {func.__name__}",
            inputSchema={"type": "object", "properties": properties, "required": required},
        )

        result.append((tool_def, func))

    return result
