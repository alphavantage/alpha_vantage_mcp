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
        "src.tools.technical_indicators_part4"
    ],
    "ping": "src.tools.ping",
    "openai": "src.tools.openai"
}

# Categories that should have entitlement parameter added
ENTITLEMENT_CATEGORIES = {"core_stock_apis", "options_data_apis", "technical_indicators"}

# Tool registries
_tool_registries = {}  # Maps module name to list of tools in that module
_all_tools_registry = []  # List of all tools across all modules
_tools_by_name = {}  # Maps uppercase tool name to function

import inspect
import functools
from typing import get_type_hints, Union

def add_entitlement_parameter(func):
    """Decorator that adds entitlement parameter to a function"""
    
    # Get existing signature and type hints
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)
    
    # Create new parameter for entitlement
    entitlement_param = inspect.Parameter(
        'entitlement',
        inspect.Parameter.KEYWORD_ONLY,
        default=None,
        annotation='str | None'
    )
    
    # Add entitlement parameter to the signature
    params = list(sig.parameters.values())
    params.append(entitlement_param)
    new_sig = sig.replace(parameters=params)
    
    # Update docstring to include entitlement parameter
    docstring = func.__doc__ or ""
    if "Args:" in docstring and "entitlement" not in docstring:
        # Find the Args section and add entitlement parameter
        lines = docstring.split('\n')
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
            
            func.__doc__ = '\n'.join(lines)
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Extract entitlement if provided - it will be passed through params to _make_api_request
        entitlement = kwargs.pop('entitlement', None)
        
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
    wrapper.__annotations__ = {**type_hints, 'entitlement': 'str | None'}

    return wrapper


def add_return_url_parameter(func):
    """Decorator that adds return_url parameter to a function"""

    # Get existing signature and type hints
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)

    # Create new parameter for return_url
    return_url_param = inspect.Parameter(
        'return_url',
        inspect.Parameter.KEYWORD_ONLY,
        default=None,
        annotation='bool | None'
    )

    # Add return_url parameter to the signature
    params = list(sig.parameters.values())
    params.append(return_url_param)
    new_sig = sig.replace(parameters=params)

    # Update docstring to include return_url parameter
    docstring = func.__doc__ or ""
    if "Args:" in docstring and "return_url" not in docstring:
        lines = docstring.split('\n')
        args_idx = None
        returns_idx = None

        for i, line in enumerate(lines):
            if "Args:" in line:
                args_idx = i
            elif "Returns:" in line and args_idx is not None:
                returns_idx = i
                break

        if args_idx is not None:
            return_url_doc = '        return_url: If True, return the API URL instead of making the request'
            if returns_idx is not None:
                lines.insert(returns_idx, return_url_doc)
                lines.insert(returns_idx, "")
            else:
                lines.append(return_url_doc)

            func.__doc__ = '\n'.join(lines)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Extract return_url if provided
        return_url = kwargs.pop('return_url', None)

        # Handle string "true" from MCP JSON (becomes string, not boolean)
        if isinstance(return_url, str):
            return_url = return_url.lower() == 'true'

        # If return_url is True, set global variable for _make_api_request to check
        if return_url is True:
            import src.common
            src.common._current_return_url = True
            try:
                result = func(*args, **kwargs)
            finally:
                src.common._current_return_url = None
            return result

        return func(*args, **kwargs)

    # Apply the new signature to the wrapper
    wrapper.__signature__ = new_sig
    wrapper.__annotations__ = {**type_hints, 'return_url': 'bool | None'}

    return wrapper


def tool(func):
    """Decorator to mark functions as MCP tools"""
    # Determine which module/category this function belongs to
    module_name = func.__module__.split('.')[-1]  # Get last part of module name
    
    # Determine the category from the module name
    category = None
    for cat, module_spec in TOOL_MODULES.items():
        if isinstance(module_spec, list):
            # For technical_indicators which has multiple modules
            for mod_path in module_spec:
                if mod_path.split('.')[-1] == module_name:
                    category = cat
                    break
        else:
            # For single module categories
            if module_spec.split('.')[-1] == module_name:
                category = cat
                break
    
    # Apply entitlement decorator if this category needs it
    if category in ENTITLEMENT_CATEGORIES:
        func = add_entitlement_parameter(func)

    # Apply return_url decorator to all tools
    func = add_return_url_parameter(func)

    if module_name not in _tool_registries:
        _tool_registries[module_name] = []

    _tool_registries[module_name].append(func)
    _all_tools_registry.append(func)
    _tools_by_name[func.__name__.upper()] = func
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

def load_all_tools():
    """Load all tools by importing all tool modules"""
    import importlib

    # Import all modules and return all tools
    for module_spec in TOOL_MODULES.values():
        if isinstance(module_spec, list):
            for module_name in module_spec:
                importlib.import_module(module_name)
        else:
            importlib.import_module(module_spec)
    return _all_tools_registry

def register_all_tools_lazy(mcp):
    """Register all tools with lazy import"""
    tools = load_all_tools()
    for func in tools:
        mcp.tool()(func)

def get_all_tools():
    """Get all tools with their MCP tool definitions

    Returns:
        List of tuples containing (tool_definition, tool_function)
    """
    import mcp.types as types
    import inspect
    from typing import get_type_hints

    # Get all tools
    tools = load_all_tools()
    
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
            if param_type == str or param_type == 'str':
                schema_type = "string"
            elif param_type == int or param_type == 'int':
                schema_type = "integer"
            elif param_type == float or param_type == 'float':
                schema_type = "number"
            elif param_type == bool or param_type == 'bool':
                schema_type = "boolean"
            elif hasattr(param_type, '__origin__') and param_type.__origin__ is Union:
                # Handle Optional types (Union with None)
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
            
            # Add description from docstring if available
            if func.__doc__:
                # Try to extract parameter description from docstring
                lines = func.__doc__.split('\n')
                for line in lines:
                    if param_name in line and ':' in line:
                        desc = line.split(':', 1)[1].strip()
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
            inputSchema={
                "type": "object",
                "properties": properties,
                "required": required
            }
        )
        
        result.append((tool_def, func))

    return result


def _ensure_tools_loaded():
    """Ensure all tool modules are imported so tools are registered."""
    import importlib

    for module_spec in TOOL_MODULES.values():
        if isinstance(module_spec, list):
            for module_name in module_spec:
                importlib.import_module(module_name)
        else:
            importlib.import_module(module_spec)


def _extract_description(func) -> str:
    """Extract the first line/paragraph of a docstring as description."""
    if not func.__doc__:
        return f"Execute {func.__name__}"

    # Get first non-empty line or paragraph
    lines = func.__doc__.strip().split('\n')
    description_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('Args:') or stripped.startswith('Returns:'):
            break
        if stripped:
            description_lines.append(stripped)
        elif description_lines:
            # Empty line after content means end of first paragraph
            break

    return ' '.join(description_lines) if description_lines else f"Execute {func.__name__}"


def get_tool_list() -> list[dict]:
    """Get list of all tools with names and descriptions only (no schema).

    Returns:
        List of dicts with 'name' and 'description' fields
    """
    _ensure_tools_loaded()

    tools = _all_tools_registry

    return [
        {
            "name": func.__name__.upper(),
            "description": _extract_description(func)
        }
        for func in tools
    ]


def _build_parameter_schema(func) -> dict:
    """Build JSON schema for function parameters."""
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)

    properties = {}
    required = []

    for param_name, param in sig.parameters.items():
        param_type = type_hints.get(param_name, str)

        # Convert Python types to JSON schema types
        if param_type == str or param_type == 'str':
            schema_type = "string"
        elif param_type == int or param_type == 'int':
            schema_type = "integer"
        elif param_type == float or param_type == 'float':
            schema_type = "number"
        elif param_type == bool or param_type == 'bool':
            schema_type = "boolean"
        elif hasattr(param_type, '__origin__') and param_type.__origin__ is Union:
            # Handle Optional types (Union with None)
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

        # Add description from docstring if available
        if func.__doc__:
            lines = func.__doc__.split('\n')
            for line in lines:
                if param_name in line and ':' in line:
                    desc = line.split(':', 1)[1].strip()
                    if desc:
                        properties[param_name]["description"] = desc
                    break

        # Mark as required if no default value
        if param.default == inspect.Parameter.empty:
            required.append(param_name)

    return {
        "type": "object",
        "properties": properties,
        "required": required
    }


def get_tool_schema(tool_name: str) -> dict:
    """Get full schema for a specific tool.

    Args:
        tool_name: The uppercase name of the tool (e.g., "TIME_SERIES_DAILY")

    Returns:
        Dict with 'name', 'description', and 'parameters' (JSON schema)

    Raises:
        ValueError: If tool not found
    """
    _ensure_tools_loaded()

    tool_name_upper = tool_name.upper()

    if tool_name_upper not in _tools_by_name:
        available = list(_tools_by_name.keys())[:10]
        raise ValueError(f"Tool '{tool_name}' not found. Available tools include: {available}...")

    func = _tools_by_name[tool_name_upper]

    return {
        "name": tool_name_upper,
        "description": func.__doc__ or f"Execute {func.__name__}",
        "parameters": _build_parameter_schema(func)
    }


def get_tool_schemas(tool_names: list[str]) -> list[dict]:
    """Get full schemas for multiple tools.

    Args:
        tool_names: List of uppercase tool names (e.g., ["TIME_SERIES_DAILY", "TIME_SERIES_INTRADAY"])

    Returns:
        List of dicts, each with 'name', 'description', and 'parameters' (JSON schema)

    Raises:
        ValueError: If any tool not found
    """
    _ensure_tools_loaded()

    schemas = []
    not_found = []

    for tool_name in tool_names:
        tool_name_upper = tool_name.upper()

        if tool_name_upper not in _tools_by_name:
            not_found.append(tool_name)
            continue

        func = _tools_by_name[tool_name_upper]
        schemas.append({
            "name": tool_name_upper,
            "description": func.__doc__ or f"Execute {func.__name__}",
            "parameters": _build_parameter_schema(func)
        })

    if not_found:
        available = list(_tools_by_name.keys())[:10]
        raise ValueError(f"Tools not found: {', '.join(not_found)}. Available tools include: {available}...")

    return schemas


def call_tool(tool_name: str, arguments: dict):
    """Execute a tool by name with provided arguments.

    Args:
        tool_name: The uppercase name of the tool (e.g., "TIME_SERIES_DAILY")
        arguments: Dict of arguments to pass to the tool

    Returns:
        Result from the tool execution

    Raises:
        ValueError: If tool not found
    """
    _ensure_tools_loaded()

    tool_name_upper = tool_name.upper()

    if tool_name_upper not in _tools_by_name:
        available = list(_tools_by_name.keys())[:10]
        raise ValueError(f"Tool '{tool_name}' not found. Available tools include: {available}...")

    func = _tools_by_name[tool_name_upper]
    return func(**arguments)


def register_meta_tools(mcp):
    """Register only the meta-tools (TOOL_LIST, TOOL_GET, TOOL_CALL) for progressive discovery."""
    from src.tools.meta_tools import tool_list, tool_get, tool_call

    mcp.tool()(tool_list)
    mcp.tool()(tool_get)
    mcp.tool()(tool_call)