import functools
import inspect
from typing import Any, get_type_hints


def setup_custom_tool_decorator(mcp):
    """Set up custom tool decorator that converts function names to UPPERCASE_WITH_UNDERSCORES"""

    def custom_tool_decorator(self):
        """Custom decorator that converts function names to UPPERCASE_WITH_UNDERSCORES"""

        def decorator(func):
            # Get function name and convert to UPPERCASE_WITH_UNDERSCORES
            func_name = func.__name__
            tool_name = func_name.upper()

            # Get docstring and parse into description
            doc = inspect.getdoc(func) or ""
            description = doc.split("\n\n")[0]  # First paragraph is description

            # Get type hints
            hints = get_type_hints(func)
            hints.pop("return", Any)

            # Build input schema from type hints and docstring
            properties = {}
            required = []

            # Parse docstring for argument descriptions
            arg_descriptions = {}
            if doc:
                lines = doc.split("\n")
                in_args = False
                for line in lines:
                    if line.strip().startswith("Args:"):
                        in_args = True
                        continue
                    if in_args:
                        if not line.strip() or line.strip().startswith("Returns:"):
                            break
                        if ":" in line:
                            arg_name, arg_desc = line.split(":", 1)
                            arg_descriptions[arg_name.strip()] = arg_desc.strip()

            def get_type_schema(type_hint: Any):
                # Basic type mapping (simplified version)
                if type_hint is int:
                    return {"type": "integer"}
                elif type_hint is float:
                    return {"type": "number"}
                elif type_hint is bool:
                    return {"type": "boolean"}
                elif type_hint is str:
                    return {"type": "string"}
                else:
                    return {"type": "string"}  # Default

            # Get function signature to check for default values
            sig = inspect.signature(func)

            # Build properties from type hints
            for param_name, param_type in hints.items():
                param_schema = get_type_schema(param_type)

                if param_name in arg_descriptions:
                    param_schema["description"] = arg_descriptions[param_name]
                else:
                    # Special case for entitlement parameter
                    if param_name == "entitlement":
                        param_schema["description"] = (
                            '"delayed" for 15-minute delayed data, "realtime" for realtime data'
                        )
                    else:
                        param_schema["description"] = f"Parameter {param_name}"

                properties[param_name] = param_schema

                # Only add to required if parameter has no default value
                param = sig.parameters.get(param_name)
                if param and param.default is inspect.Parameter.empty:
                    required.append(param_name)

            # Create tool schema
            tool_schema = {
                "name": tool_name,
                "description": description,
                "inputSchema": {"type": "object", "properties": properties, "required": required},
            }

            # Register the tool
            self.tools[tool_name] = tool_schema
            self.tool_implementations[tool_name] = func

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return decorator

    # Replace the original tool method
    mcp.tool = lambda: custom_tool_decorator(mcp)
