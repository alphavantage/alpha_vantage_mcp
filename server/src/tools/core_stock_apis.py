from src.common import _make_api_request
from src.tools.registry import tool


@tool
def time_series_intraday(
    symbol: str,
    interval: str,
    adjusted: bool = True,
    extended_hours: bool = True,
    month: str | None = None,
    outputsize: str = "compact",
    datatype: str = "csv",
) -> dict | str:
    """
    Returns current and 20+ years of historical intraday OHLCV time series of the equity specified.

    Args:
        symbol: The name of the equity. For example: symbol=IBM
        interval: Time interval between consecutive data points. Supported: 1min, 5min, 15min, 30min, 60min
        adjusted: By default True. Set False to query raw (as-traded) intraday values
        extended_hours: By default True. Set False for regular trading hours only
        month: Query specific month in YYYY-MM format. Example: 2009-01
        outputsize: "compact" (100 data points) or "full" (30 days or full month)
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the data in JSON format; csv returns the data as a CSV (comma separated value) file.

    Returns:
        Dict or string containing the time series data based on datatype parameter.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "adjusted": str(adjusted).lower(),
        "extended_hours": str(extended_hours).lower(),
        "outputsize": outputsize,
        "datatype": datatype,
    }
    if month:
        params["month"] = month

    return _make_api_request("TIME_SERIES_INTRADAY", params)


@tool
def time_series_daily(
    symbol: str, outputsize: str = "compact", datatype: str = "csv"
) -> dict | str:
    """
    Returns raw daily time series (OHLCV) of the global equity specified, covering 20+ years of historical data.

    Args:
        symbol: The name of the equity. For example: symbol=IBM
        outputsize: "compact" (100 data points) or "full" (20+ years of historical data)
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the data in JSON format; csv returns the data as a CSV (comma separated value) file.

    Returns:
        Dict or string containing the daily time series data based on datatype parameter.
    """
    params = {
        "symbol": symbol,
        "outputsize": outputsize,
        "datatype": datatype,
    }

    return _make_api_request("TIME_SERIES_DAILY", params)


@tool
def time_series_daily_adjusted(
    symbol: str, outputsize: str = "compact", datatype: str = "csv"
) -> dict | str:
    """
    Returns raw daily OHLCV values, adjusted close values, and historical split/dividend events.

    Args:
        symbol: The name of the equity. For example: symbol=IBM
        outputsize: "compact" (100 data points) or "full" (20+ years of historical data)
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the data in JSON format; csv returns the data as a CSV (comma separated value) file.

    Returns:
        Dict or string containing the daily adjusted time series data based on datatype parameter.
    """
    params = {
        "symbol": symbol,
        "outputsize": outputsize,
        "datatype": datatype,
    }

    return _make_api_request("TIME_SERIES_DAILY_ADJUSTED", params)


@tool
def time_series_weekly(symbol: str, datatype: str = "csv") -> dict | str:
    """
    Returns weekly time series (last trading day of each week, OHLCV) covering 20+ years of historical data.

    Args:
        symbol: The name of the equity. For example: symbol=IBM
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the data in JSON format; csv returns the data as a CSV (comma separated value) file.

    Returns:
        Dict or string containing the weekly time series data based on datatype parameter.
    """
    params = {
        "symbol": symbol,
        "datatype": datatype,
    }

    return _make_api_request("TIME_SERIES_WEEKLY", params)


@tool
def time_series_weekly_adjusted(symbol: str, datatype: str = "csv") -> dict | str:
    """
    Returns weekly adjusted time series (OHLCV, adjusted close, volume, dividend) covering 20+ years.

    Args:
        symbol: The name of the equity. For example: symbol=IBM
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the data in JSON format; csv returns the data as a CSV (comma separated value) file.

    Returns:
        Dict or string containing the weekly adjusted time series data based on datatype parameter.
    """
    params = {
        "symbol": symbol,
        "datatype": datatype,
    }

    return _make_api_request("TIME_SERIES_WEEKLY_ADJUSTED", params)


@tool
def time_series_monthly(symbol: str, datatype: str = "csv") -> dict | str:
    """
    Returns monthly time series (last trading day of each month, OHLCV) covering 20+ years.

    Args:
        symbol: The name of the equity. For example: symbol=IBM
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the data in JSON format; csv returns the data as a CSV (comma separated value) file.

    Returns:
        Dict or string containing the monthly time series data based on datatype parameter.
    """
    params = {
        "symbol": symbol,
        "datatype": datatype,
    }

    return _make_api_request("TIME_SERIES_MONTHLY", params)


@tool
def time_series_monthly_adjusted(symbol: str, datatype: str = "csv") -> dict | str:
    """
    Returns monthly adjusted time series (OHLCV, adjusted close, volume, dividend) covering 20+ years.

    Args:
        symbol: The name of the equity. For example: symbol=IBM
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the data in JSON format; csv returns the data as a CSV (comma separated value) file.

    Returns:
        Dict or string containing the monthly adjusted time series data based on datatype parameter.
    """
    params = {
        "symbol": symbol,
        "datatype": datatype,
    }

    return _make_api_request("TIME_SERIES_MONTHLY_ADJUSTED", params)


@tool
def global_quote(symbol: str, datatype: str = "csv") -> dict | str:
    """
    Returns the latest price and volume information for a ticker.

    Args:
        symbol: The symbol of the global ticker. For example: symbol=IBM
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the data in JSON format; csv returns the data as a CSV (comma separated value) file.

    Returns:
        Dict or string containing the latest quote information based on datatype parameter.
    """
    params = {
        "symbol": symbol,
        "datatype": datatype,
    }
    return _make_api_request("GLOBAL_QUOTE", params)


@tool
def realtime_bulk_quotes(symbol: str, datatype: str = "csv") -> dict | str:
    """
    Returns realtime quotes for US-traded symbols in bulk, accepting up to 100 symbols per request.

    Args:
        symbol: Up to 100 symbols separated by comma. Example: MSFT,AAPL,IBM
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the data in JSON format; csv returns the data as a CSV (comma separated value) file.

    Returns:
        Dict or string containing realtime bulk quotes based on datatype parameter.
    """
    params = {
        "symbol": symbol,
        "datatype": datatype,
    }

    return _make_api_request("REALTIME_BULK_QUOTES", params)


@tool
def symbol_search(keywords: str, datatype: str = "csv") -> dict | str:
    """
    Returns best-matching symbols and market information based on keywords.

    Args:
        keywords: A text string of your choice. Example: microsoft
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the data in JSON format; csv returns the data as a CSV (comma separated value) file.

    Returns:
        Dict or string containing symbol search results based on datatype parameter.
    """
    params = {
        "keywords": keywords,
        "datatype": datatype,
    }

    return _make_api_request("SYMBOL_SEARCH", params)


@tool
def market_status() -> dict:
    """
    Returns the current market status (open vs. closed) of major trading venues worldwide.

    Returns:
        Dict containing current market status information.
    """
    params = {}

    return _make_api_request("MARKET_STATUS", params)
