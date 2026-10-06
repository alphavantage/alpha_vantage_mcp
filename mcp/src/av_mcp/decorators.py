import functools
import inspect
from types import UnionType
from typing import Union, get_args, get_origin, get_type_hints, Any

from av_api.registry import extract_description

def setup_custom_tool_decorator(mcp):
    """Set up custom tool decorator that converts function names to UPPERCASE_WITH_UNDERSCORES"""

    def custom_tool_decorator(self, description=None, annotations=None, output_schema=None):
        """Custom decorator that converts function names to UPPERCASE_WITH_UNDERSCORES"""
        def decorator(func):
            # Get function name and convert to UPPERCASE_WITH_UNDERSCORES
            func_name = func.__name__
            tool_name = func_name.upper()

            # Get docstring: use full description before Args:/Returns:
            doc = inspect.getdoc(func) or ''
            tool_description = description or extract_description(func)

            # Get type hints
            hints = get_type_hints(func)
            hints.pop('return', Any)

            # Build input schema from type hints and docstring
            properties = {}
            required = []

            # Parse docstring for argument descriptions
            arg_descriptions = {}
            if doc:
                lines = doc.split('\n')
                in_args = False
                for line in lines:
                    if line.strip().startswith('Args:'):
                        in_args = True
                        continue
                    if in_args:
                        if not line.strip() or line.strip().startswith('Returns:'):
                            break
                        if ':' in line:
                            arg_name, arg_desc = line.split(':', 1)
                            arg_descriptions[arg_name.strip()] = arg_desc.strip()

            def get_type_schema(type_hint: Any):
                origin = get_origin(type_hint)
                if type_hint is int:
                    return {'type': 'integer'}
                if type_hint is float:
                    return {'type': 'number'}
                if type_hint is bool:
                    return {'type': 'boolean'}
                if type_hint is str:
                    return {'type': 'string'}
                if type_hint is dict or origin is dict:
                    return {'type': 'object', 'additionalProperties': True}
                if type_hint is list or origin is list:
                    args = get_args(type_hint) if origin is list else ()
                    item_schema = get_type_schema(args[0]) if args else {'type': 'string'}
                    return {'type': 'array', 'items': item_schema}
                if origin is Union or origin is UnionType:
                    args = [arg for arg in get_args(type_hint) if arg is not type(None)]
                    if len(args) == 1:
                        return get_type_schema(args[0])
                    return {'oneOf': [get_type_schema(arg) for arg in args]}
                return {'type': 'string'}

            # Get function signature to check for default values
            sig = inspect.signature(func)

            # Build properties from type hints
            for param_name, param_type in hints.items():
                param_schema = get_type_schema(param_type)

                # A None default means the tool treats null as "not given"; let clients send it.
                param = sig.parameters.get(param_name)
                if param and param.default is None:
                    if 'type' in param_schema:
                        param_schema['type'] = [param_schema['type'], 'null']
                    else:
                        param_schema = {'anyOf': [param_schema, {'type': 'null'}]}

                if param_name in arg_descriptions:
                    param_schema['description'] = arg_descriptions[param_name]
                else:
                    # Special case for entitlement parameter
                    if param_name == 'entitlement':
                        param_schema['description'] = '"delayed" for 15-minute delayed data, "realtime" for realtime data'
                    else:
                        param_schema['description'] = f"Parameter {param_name}"

                properties[param_name] = param_schema

                # Only add to required if parameter has no default value
                param = sig.parameters.get(param_name)
                if param and param.default is inspect.Parameter.empty:
                    required.append(param_name)

            # Create tool schema
            tool_schema = {
                'name': tool_name,
                'description': tool_description,
                'inputSchema': {
                    'type': 'object',
                    'properties': properties,
                    'required': required,
                    'additionalProperties': False,
                },
            }
            if annotations is not None:
                # Convert Pydantic model to dict for JSON serialization compatibility
                if hasattr(annotations, 'model_dump'):
                    tool_schema['annotations'] = annotations.model_dump(exclude_none=True)
                else:
                    tool_schema['annotations'] = annotations
            if output_schema is not None:
                tool_schema['outputSchema'] = output_schema

            # Register the tool
            self.tools[tool_name] = tool_schema
            self.tool_implementations[tool_name] = func

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return decorator

    # Replace the original tool method
    mcp.tool = lambda description=None, annotations=None, output_schema=None: custom_tool_decorator(
        mcp, description=description, annotations=annotations, output_schema=output_schema
    )
