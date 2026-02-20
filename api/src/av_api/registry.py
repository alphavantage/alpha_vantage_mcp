import importlib
import inspect
import functools
from typing import Union, get_type_hints

# Module names that should have entitlement parameter added
_ENTITLEMENT_MODULES = {
    "core_stock_apis",
    "options_data_apis",
    "technical_indicators_part1",
    "technical_indicators_part2",
    "technical_indicators_part3",
    "technical_indicators_part4",
}

# Tool registries
_all_tools_registry = []  # List of all tools across all modules
_tools_by_name = {}  # Maps uppercase tool name to function


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

        # Call the original function, passing entitlement through module-level variable
        if entitlement:
            import av_api.client
            av_api.client._current_entitlement = entitlement
            try:
                result = func(*args, **kwargs)
            finally:
                av_api.client._current_entitlement = None
            return result

        return func(*args, **kwargs)

    # Apply the new signature to the wrapper
    wrapper.__signature__ = new_sig
    wrapper.__annotations__ = {**type_hints, 'entitlement': 'str | None'}

    return wrapper

def tool(func):
    """Decorator to mark functions as tools"""
    module_name = func.__module__.split('.')[-1]

    # Apply entitlement decorator if this module needs it
    if module_name in _ENTITLEMENT_MODULES:
        func = add_entitlement_parameter(func)

    _all_tools_registry.append(func)
    _tools_by_name[func.__name__.upper()] = func
    return func


# Tool module mapping for lazy imports
TOOL_MODULES = {
    "core_stock_apis": "av_api.tools.core_stock_apis",
    "options_data_apis": "av_api.tools.options_data_apis",
    "alpha_intelligence": "av_api.tools.alpha_intelligence",
    "commodities": "av_api.tools.commodities",
    "cryptocurrencies": "av_api.tools.cryptocurrencies",
    "economic_indicators": "av_api.tools.economic_indicators",
    "forex": "av_api.tools.forex",
    "fundamental_data": "av_api.tools.fundamental_data",
    "technical_indicators": [
        "av_api.tools.technical_indicators_part1",
        "av_api.tools.technical_indicators_part2",
        "av_api.tools.technical_indicators_part3",
        "av_api.tools.technical_indicators_part4",
    ],
    "ping": "av_api.tools.ping",
    "openai": "av_api.tools.openai",
}


def ensure_tools_loaded():
    """Ensure all tool modules are imported so tools are registered."""
    for module_spec in TOOL_MODULES.values():
        if isinstance(module_spec, list):
            for module_name in module_spec:
                importlib.import_module(module_name)
        else:
            importlib.import_module(module_spec)


def extract_description(func) -> str:
    """Extract docstring content before Args:/Returns: as the description."""
    if not func.__doc__:
        return f"Execute {func.__name__}"

    lines = func.__doc__.strip().split('\n')
    description_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('Args:') or stripped.startswith('Returns:'):
            break
        if stripped:
            description_lines.append(stripped)

    return ' '.join(description_lines) if description_lines else f"Execute {func.__name__}"


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
        "required": required,
    }


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
    ensure_tools_loaded()

    tool_name_upper = tool_name.upper()

    if tool_name_upper not in _tools_by_name:
        available = list(_tools_by_name.keys())[:10]
        raise ValueError(f"Tool '{tool_name}' not found. Available tools include: {available}...")

    func = _tools_by_name[tool_name_upper]
    return func(**arguments)


def get_tool_list() -> list[dict]:
    """Get list of all tools with names and descriptions only (no schema).

    Returns:
        List of dicts with 'name' and 'description' fields
    """
    ensure_tools_loaded()

    return [
        {
            "name": func.__name__.upper(),
            "description": extract_description(func),
        }
        for func in _all_tools_registry
    ]


def get_tool_schema(tool_name: str) -> dict:
    """Get full schema for a specific tool.

    Args:
        tool_name: The uppercase name of the tool (e.g., "TIME_SERIES_DAILY")

    Returns:
        Dict with 'name', 'description', and 'parameters' (JSON schema)

    Raises:
        ValueError: If tool not found
    """
    ensure_tools_loaded()

    tool_name_upper = tool_name.upper()

    if tool_name_upper not in _tools_by_name:
        available = list(_tools_by_name.keys())[:10]
        raise ValueError(f"Tool '{tool_name}' not found. Available tools include: {available}...")

    func = _tools_by_name[tool_name_upper]

    return {
        "name": tool_name_upper,
        "description": func.__doc__ or f"Execute {func.__name__}",
        "parameters": _build_parameter_schema(func),
    }


def get_tool_schemas(tool_names: list[str]) -> list[dict]:
    """Get full schemas for multiple tools.

    Args:
        tool_names: List of uppercase tool names

    Returns:
        List of dicts, each with 'name', 'description', and 'parameters' (JSON schema)

    Raises:
        ValueError: If any tool not found
    """
    ensure_tools_loaded()

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
            "parameters": _build_parameter_schema(func),
        })

    if not_found:
        available = list(_tools_by_name.keys())[:10]
        raise ValueError(f"Tools not found: {', '.join(not_found)}. Available tools include: {available}...")

    return schemas
