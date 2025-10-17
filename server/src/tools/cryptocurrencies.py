from src.common import _make_api_request
from src.tools.registry import tool


@tool
def currency_exchange_rate(
    from_currency: str, to_currency: str, datatype: str = "csv"
) -> dict[str, str] | str:
    """
    This API returns the realtime exchange rate for any pair of digital currency (e.g., Bitcoin) or physical currency (e.g., USD).

    Args:
        from_currency: The currency you would like to get the exchange rate for. It can either be a physical currency or digital/crypto currency. For example: from_currency=USD or from_currency=BTC.
        to_currency: The destination currency for the exchange rate. It can either be a physical currency or digital/crypto currency. For example: to_currency=USD or to_currency=BTC.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications: json returns the exchange rate in JSON format; csv returns the data as a CSV (comma separated value) file.

    Returns:
        The exchange rate data in the specified format.
    """

    params = {
        "from_currency": from_currency,
        "to_currency": to_currency,
        "datatype": datatype,
    }

    return _make_api_request("CURRENCY_EXCHANGE_RATE", params)


@tool
def crypto_intraday(
    symbol: str, market: str, interval: str, outputsize: str = "compact", datatype: str = "csv"
) -> dict[str, str] | str:
    """
    This API returns intraday time series (timestamp, open, high, low, close, volume) of the cryptocurrency specified, updated realtime.

    Args:
        symbol: The digital/crypto currency of your choice. It can be any of the currencies in the digital currency list. For example: symbol=ETH.
        market: The exchange market of your choice. It can be any of the market in the market list. For example: market=USD.
        interval: Time interval between two consecutive data points in the time series. The following values are supported: 1min, 5min, 15min, 30min, 60min
        outputsize: By default, outputsize=compact. Strings compact and full are accepted with the following specifications: compact returns only the latest 100 data points in the intraday time series; full returns the full-length intraday time series. The "compact" option is recommended if you would like to reduce the data size of each API call.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications: json returns the intraday time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        The intraday time series data in the specified format.
    """

    params = {
        "symbol": symbol,
        "market": market,
        "interval": interval,
        "outputsize": outputsize,
        "datatype": datatype,
    }

    return _make_api_request("CRYPTO_INTRADAY", params)


@tool
def digital_currency_daily(symbol: str, market: str, datatype: str = "csv") -> dict[str, str] | str:
    """
    This API returns the daily historical time series for a digital currency (e.g., BTC) traded on a specific market (e.g., EUR/Euro), refreshed daily at midnight (UTC). Prices and volumes are quoted in both the market-specific currency and USD.

    Args:
        symbol: The digital/crypto currency of your choice. It can be any of the currencies in the digital currency list. For example: symbol=BTC.
        market: The exchange market of your choice. It can be any of the market in the market list. For example: market=EUR.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications: json returns the daily time series in JSON format; csv returns the data as a CSV (comma separated value) file.

    Returns:
        The daily time series data in the specified format.
    """

    params = {
        "symbol": symbol,
        "market": market,
        "datatype": datatype,
    }

    return _make_api_request("DIGITAL_CURRENCY_DAILY", params)


@tool
def digital_currency_weekly(
    symbol: str, market: str, datatype: str = "csv"
) -> dict[str, str] | str:
    """
    This API returns the weekly historical time series for a digital currency (e.g., BTC) traded on a specific market (e.g., EUR/Euro), refreshed daily at midnight (UTC). Prices and volumes are quoted in both the market-specific currency and USD.

    Args:
        symbol: The digital/crypto currency of your choice. It can be any of the currencies in the digital currency list. For example: symbol=BTC.
        market: The exchange market of your choice. It can be any of the market in the market list. For example: market=EUR.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications: json returns the weekly time series in JSON format; csv returns the data as a CSV (comma separated value) file.

    Returns:
        The weekly time series data in the specified format.
    """

    params = {
        "symbol": symbol,
        "market": market,
        "datatype": datatype,
    }

    return _make_api_request("DIGITAL_CURRENCY_WEEKLY", params)


@tool
def digital_currency_monthly(
    symbol: str, market: str, datatype: str = "csv"
) -> dict[str, str] | str:
    """
    This API returns the monthly historical time series for a digital currency (e.g., BTC) traded on a specific market (e.g., EUR/Euro), refreshed daily at midnight (UTC). Prices and volumes are quoted in both the market-specific currency and USD.

    Args:
        symbol: The digital/crypto currency of your choice. It can be any of the currencies in the digital currency list. For example: symbol=BTC.
        market: The exchange market of your choice. It can be any of the market in the market list. For example: market=EUR.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications: json returns the monthly time series in JSON format; csv returns the data as a CSV (comma separated value) file.

    Returns:
        The monthly time series data in the specified format.
    """

    params = {
        "symbol": symbol,
        "market": market,
        "datatype": datatype,
    }

    return _make_api_request("DIGITAL_CURRENCY_MONTHLY", params)
