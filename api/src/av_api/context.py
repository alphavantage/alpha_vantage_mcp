from contextvars import ContextVar
from typing import Optional

# Context variable to store the API key
api_key_context: ContextVar[Optional[str]] = ContextVar('api_key', default=None)

# Context variable to store the detected MCP client name (clientInfo.name on stdio,
# normalized User-Agent platform on Lambda). Used by the return_full_data decorator
# to pick an adaptive default per client capability.
client_name_context: ContextVar[Optional[str]] = ContextVar('client_name', default=None)


def set_api_key(api_key: str) -> None:
    """Set the API key in the current context."""
    api_key_context.set(api_key)

def get_api_key() -> Optional[str]:
    """Get the API key from the current context."""
    return api_key_context.get()


def set_client_name(name: Optional[str]) -> None:
    """Set the detected MCP client name in the current context."""
    client_name_context.set(name)


def get_client_name() -> Optional[str]:
    """Get the detected MCP client name from the current context."""
    return client_name_context.get()


def is_capable_client(name: Optional[str]) -> bool:
    """Return True if the client name looks like a Claude family client.

    Heuristic: any name whose lowercased form contains ``"claude"`` is treated as
    a capable client that offloads large tool results to files (Claude.ai,
    Claude Code, Claude Desktop, claude-user UA, etc.). Unknown non-Claude
    clients return False and keep the preview default.
    """
    if not name:
        return False
    return "claude" in name.lower()
