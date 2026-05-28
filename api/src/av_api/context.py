from contextvars import ContextVar
from typing import Optional

# Context variable to store the API key
api_key_context: ContextVar[Optional[str]] = ContextVar('api_key', default=None)

def set_api_key(api_key: str) -> None:
    """Set the API key in the current context."""
    api_key_context.set(api_key)

def get_api_key() -> Optional[str]:
    """Get the API key from the current context."""
    return api_key_context.get()
