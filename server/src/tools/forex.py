from src.common import _make_api_request
from src.tools.registry import tool

# Note: currency_exchange_rate is defined in cryptocurrencies.py to avoid duplication
# It handles both digital/crypto and physical currency pairs


@tool
def fx_intraday(
    from_symbol: str,
    to_symbol: str,
    interval: str,
    outputsize: str = "compact",
    datatype: str = "csv",
) -> dict[str, str] | str:
    """
    This API returns intraday time series (timestamp, open, high, low, close) of the FX currency pair specified, updated realtime.

    Args:
        from_symbol: A three-letter symbol from the forex currency list. For example: from_symbol=EUR
        to_symbol: A three-letter symbol from the forex currency list. For example: to_symbol=USD
        interval: Time interval between two consecutive data points in the time series. The following values are supported: 1min, 5min, 15min, 30min, 60min
        outputsize: By default, outputsize=compact. Strings compact and full are accepted with the following specifications:
                   compact returns only the latest 100 data points in the intraday time series;
                   full returns the full-length intraday time series. The "compact" option is recommended if you would like to reduce the data size of each API call.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the intraday time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        Intraday FX time series data as a dictionary or string.
    """

    params = {
        "from_symbol": from_symbol,
        "to_symbol": to_symbol,
        "interval": interval,
        "outputsize": outputsize,
        "datatype": datatype,
    }

    return _make_api_request("FX_INTRADAY", params)


@tool
def fx_daily(
    from_symbol: str, to_symbol: str, outputsize: str = "compact", datatype: str = "csv"
) -> dict[str, str] | str:
    """
    This API returns the daily time series (timestamp, open, high, low, close) of the FX currency pair specified, updated realtime.

    Args:
        from_symbol: A three-letter symbol from the forex currency list. For example: from_symbol=EUR
        to_symbol: A three-letter symbol from the forex currency list. For example: to_symbol=USD
        outputsize: By default, outputsize=compact. Strings compact and full are accepted with the following specifications:
                   compact returns only the latest 100 data points in the daily time series;
                   full returns the full-length daily time series. The "compact" option is recommended if you would like to reduce the data size of each API call.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        Daily FX time series data as a dictionary or string.
    """

    params = {
        "from_symbol": from_symbol,
        "to_symbol": to_symbol,
        "outputsize": outputsize,
        "datatype": datatype,
    }

    return _make_api_request("FX_DAILY", params)


@tool
def fx_weekly(from_symbol: str, to_symbol: str, datatype: str = "csv") -> dict[str, str] | str:
    """
    This API returns the weekly time series (timestamp, open, high, low, close) of the FX currency pair specified, updated realtime.
    The latest data point is the price information for the week (or partial week) containing the current trading day, updated realtime.

    Args:
        from_symbol: A three-letter symbol from the forex currency list. For example: from_symbol=EUR
        to_symbol: A three-letter symbol from the forex currency list. For example: to_symbol=USD
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the weekly time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        Weekly FX time series data as a dictionary or string.
    """

    params = {
        "from_symbol": from_symbol,
        "to_symbol": to_symbol,
        "datatype": datatype,
    }

    return _make_api_request("FX_WEEKLY", params)


@tool
def fx_monthly(from_symbol: str, to_symbol: str, datatype: str = "csv") -> dict[str, str] | str:
    """
    This API returns the monthly time series (timestamp, open, high, low, close) of the FX currency pair specified, updated realtime.
    The latest data point is the prices information for the month (or partial month) containing the current trading day, updated realtime.

    Args:
        from_symbol: A three-letter symbol from the forex currency list. For example: from_symbol=EUR
        to_symbol: A three-letter symbol from the forex currency list. For example: to_symbol=USD
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the monthly time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        Monthly FX time series data as a dictionary or string.
    """

    params = {
        "from_symbol": from_symbol,
        "to_symbol": to_symbol,
        "datatype": datatype,
    }

    return _make_api_request("FX_MONTHLY", params)
