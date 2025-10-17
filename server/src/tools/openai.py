from typing import Any

from src.tools.registry import tool


@tool
def search(query: str) -> dict[str, list[dict[str, Any]]]:
    """
    Search for relevant Alpha Vantage data based on natural language query.

    Args:
        query: Natural language search query (e.g., "AAPL stock price daily", "Tesla earnings data")

    Returns:
        Dictionary with 'results' key containing list of relevant data sources.
        Each result includes id, title, text snippet describing the data, and url.
    """
    # Placeholder - return hardcoded examples for now
    return {
        "results": [
            {
                "id": "time_series_daily",
                "title": "Daily Time Series Stock Data",
                "text": "Get daily OHLCV data for stocks with 20+ years of history",
                "url": "https://www.alphavantage.co/documentation/",
            },
            {
                "id": "quote_endpoint",
                "title": "Real-time Stock Quote",
                "text": "Get current stock price and trading information",
                "url": "https://www.alphavantage.co/documentation/",
            },
        ]
    }


@tool
def fetch(id: str) -> dict[str, Any]:
    """
    Fetch complete financial data by calling the specified Alpha Vantage API function.

    Args:
        id: Alpha Vantage API function name (from search results)

    Returns:
        Complete data response with id, title, full data content, URL, and metadata
    """
    # Placeholder - return the id as-is for now
    return {
        "id": id,
        "title": f"Data for {id}",
        "text": f"Placeholder response for function: {id}",
        "url": "https://www.alphavantage.co/documentation/",
        "metadata": {"function_name": id},
    }
