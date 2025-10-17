from src.tools.registry import tool


@tool
def ping() -> str:
    """Check if the service is healthy."""
    return "pong"


@tool
def add_two_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b
