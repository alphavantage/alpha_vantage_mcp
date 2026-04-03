from av_api.client import _make_api_request
from av_api.registry import tool


@tool
def index_data(
    symbol: str,
    interval: str,
    datatype: str = "json"
) -> dict[str, str] | str:
    """
    Returns daily, weekly, or monthly OHLC time series data for 200+ major market indices (e.g., DJI, SPX, COMP, NDX, VIX, RUT). For the full list of supported indices, use INDEX_CATALOG.

    Args:
        symbol: The index symbol (e.g., DJI for Dow Jones, SPX for S&P 500, COMP for NASDAQ Composite, NDX for NASDAQ 100, VIX for Cboe Volatility Index, RUT for Russell 2000).
        interval: Time interval between two data points. Supported values: daily, weekly, monthly.
        datatype: By default, json. Strings json and csv are accepted.

    Returns:
        OHLC time series data for the specified index.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "datatype": datatype,
    }
    return _make_api_request("INDEX_DATA", params)


@tool
def index_catalog(
    datatype: str = "json"
) -> dict[str, str] | str:
    """
    Returns the full list of supported index symbols with their long-form names.

    Args:
        datatype: By default, json. Strings json and csv are accepted.

    Returns:
        List of supported index symbols and names.
    """
    params = {
        "datatype": datatype,
    }
    return _make_api_request("INDEX_CATALOG", params)
