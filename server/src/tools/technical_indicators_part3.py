from src.common import _make_api_request
from src.tools.registry import tool


@tool
def mfi(
    symbol: str, interval: str, time_period: int, month: str = None, datatype: str = "csv"
) -> dict[str, str] | str:
    """Returns the money flow index (MFI) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        time_period: Number of data points used to calculate each MFI value. Positive integers are accepted.
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
               for the equity markets. By default, this parameter is not set and the technical indicator values
               will be calculated based on the most recent 30 days of intraday data. You can use the month
               parameter (in YYYY-MM format) to compute intraday technical indicators for a specific month
               in history. For example, month=2009-01.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV file.

    Returns:
        The money flow index (MFI) values in JSON or CSV format.
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "time_period": str(time_period),
        "datatype": datatype,
    }
    if month:
        params["month"] = month

    return _make_api_request("MFI", params)


@tool
def trix(
    symbol: str,
    interval: str,
    time_period: int,
    series_type: str,
    month: str = None,
    datatype: str = "csv",
) -> dict[str, str] | str:
    """Returns the 1-day rate of change of a triple smooth exponential moving average (TRIX) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        time_period: Number of data points used to calculate each TRIX value. Positive integers are accepted.
        series_type: The desired price type in the time series. Four types are supported: close, open, high, low
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
               for the equity markets. By default, this parameter is not set and the technical indicator values
               will be calculated based on the most recent 30 days of intraday data. You can use the month
               parameter (in YYYY-MM format) to compute intraday technical indicators for a specific month
               in history. For example, month=2009-01.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV file.

    Returns:
        The 1-day rate of change of a triple smooth exponential moving average (TRIX) values in JSON or CSV format.
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "time_period": str(time_period),
        "series_type": series_type,
        "datatype": datatype,
    }
    if month:
        params["month"] = month

    return _make_api_request("TRIX", params)


@tool
def ultosc(
    symbol: str,
    interval: str,
    timeperiod1: int = 7,
    timeperiod2: int = 14,
    timeperiod3: int = 28,
    month: str = None,
    datatype: str = "csv",
) -> dict[str, str] | str:
    """Returns the ultimate oscillator (ULTOSC) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        timeperiod1: The first time period for the indicator. Positive integers are accepted. By default, timeperiod1=7.
        timeperiod2: The second time period for the indicator. Positive integers are accepted. By default, timeperiod2=14.
        timeperiod3: The third time period for the indicator. Positive integers are accepted. By default, timeperiod3=28.
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
               for the equity markets. By default, this parameter is not set and the technical indicator values
               will be calculated based on the most recent 30 days of intraday data. You can use the month
               parameter (in YYYY-MM format) to compute intraday technical indicators for a specific month
               in history. For example, month=2009-01.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV file.

    Returns:
        The ultimate oscillator (ULTOSC) values in JSON or CSV format.
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "timeperiod1": str(timeperiod1),
        "timeperiod2": str(timeperiod2),
        "timeperiod3": str(timeperiod3),
        "datatype": datatype,
    }
    if month:
        params["month"] = month

    return _make_api_request("ULTOSC", params)


@tool
def dx(
    symbol: str, interval: str, time_period: int, month: str = None, datatype: str = "csv"
) -> dict[str, str] | str:
    """Returns the directional movement index (DX) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        time_period: Number of data points used to calculate each DX value. Positive integers are accepted.
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
               for the equity markets. By default, this parameter is not set and the technical indicator values
               will be calculated based on the most recent 30 days of intraday data. You can use the month
               parameter (in YYYY-MM format) to compute intraday technical indicators for a specific month
               in history. For example, month=2009-01.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV file.

    Returns:
        The directional movement index (DX) values in JSON or CSV format.
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "time_period": str(time_period),
        "datatype": datatype,
    }
    if month:
        params["month"] = month

    return _make_api_request("DX", params)


@tool
def minus_di(
    symbol: str, interval: str, time_period: int, month: str = None, datatype: str = "csv"
) -> dict[str, str] | str:
    """Returns the minus directional indicator (MINUS_DI) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        time_period: Number of data points used to calculate each MINUS_DI value. Positive integers are accepted.
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
               for the equity markets. By default, this parameter is not set and the technical indicator values
               will be calculated based on the most recent 30 days of intraday data. You can use the month
               parameter (in YYYY-MM format) to compute intraday technical indicators for a specific month
               in history. For example, month=2009-01.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV file.

    Returns:
        The minus directional indicator (MINUS_DI) values in JSON or CSV format.
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "time_period": str(time_period),
        "datatype": datatype,
    }
    if month:
        params["month"] = month

    return _make_api_request("MINUS_DI", params)


@tool
def plus_di(
    symbol: str, interval: str, time_period: int, month: str = None, datatype: str = "csv"
) -> dict[str, str] | str:
    """Returns the plus directional indicator (PLUS_DI) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        time_period: Number of data points used to calculate each PLUS_DI value. Positive integers are accepted.
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
               for the equity markets. By default, this parameter is not set and the technical indicator values
               will be calculated based on the most recent 30 days of intraday data. You can use the month
               parameter (in YYYY-MM format) to compute intraday technical indicators for a specific month
               in history. For example, month=2009-01.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV file.

    Returns:
        The plus directional indicator (PLUS_DI) values in JSON or CSV format.
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "time_period": str(time_period),
        "datatype": datatype,
    }
    if month:
        params["month"] = month

    return _make_api_request("PLUS_DI", params)


@tool
def minus_dm(
    symbol: str, interval: str, time_period: int, month: str = None, datatype: str = "csv"
) -> dict[str, str] | str:
    """Returns the minus directional movement (MINUS_DM) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        time_period: Number of data points used to calculate each MINUS_DM value. Positive integers are accepted.
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
               for the equity markets. By default, this parameter is not set and the technical indicator values
               will be calculated based on the most recent 30 days of intraday data. You can use the month
               parameter (in YYYY-MM format) to compute intraday technical indicators for a specific month
               in history. For example, month=2009-01.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV file.

    Returns:
        The minus directional movement (MINUS_DM) values in JSON or CSV format.
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "time_period": str(time_period),
        "datatype": datatype,
    }
    if month:
        params["month"] = month

    return _make_api_request("MINUS_DM", params)


@tool
def plus_dm(
    symbol: str, interval: str, time_period: int, month: str = None, datatype: str = "csv"
) -> dict[str, str] | str:
    """Returns the plus directional movement (PLUS_DM) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        time_period: Number of data points used to calculate each PLUS_DM value. Positive integers are accepted.
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
               for the equity markets. By default, this parameter is not set and the technical indicator values
               will be calculated based on the most recent 30 days of intraday data. You can use the month
               parameter (in YYYY-MM format) to compute intraday technical indicators for a specific month
               in history. For example, month=2009-01.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV file.

    Returns:
        The plus directional movement (PLUS_DM) values in JSON or CSV format.
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "time_period": str(time_period),
        "datatype": datatype,
    }
    if month:
        params["month"] = month

    return _make_api_request("PLUS_DM", params)


@tool
def bbands(
    symbol: str,
    interval: str,
    time_period: int,
    series_type: str,
    nbdevup: int = 2,
    nbdevdn: int = 2,
    matype: int = 0,
    month: str = None,
    datatype: str = "csv",
) -> dict[str, str] | str:
    """Returns the Bollinger bands (BBANDS) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        time_period: Number of data points used to calculate each BBANDS value. Positive integers are accepted.
        series_type: The desired price type in the time series. Four types are supported: close, open, high, low
        nbdevup: The standard deviation multiplier of the upper band. Positive integers are accepted. By default, nbdevup=2.
        nbdevdn: The standard deviation multiplier of the lower band. Positive integers are accepted. By default, nbdevdn=2.
        matype: Moving average type of the time series. By default, matype=0. Integers 0-8 are accepted with the following mappings:
               0 = Simple Moving Average (SMA), 1 = Exponential Moving Average (EMA), 2 = Weighted Moving Average (WMA),
               3 = Double Exponential Moving Average (DEMA), 4 = Triple Exponential Moving Average (TEMA),
               5 = Triangular Moving Average (TRIMA), 6 = T3 Moving Average, 7 = Kaufman Adaptive Moving Average (KAMA),
               8 = MESA Adaptive Moving Average (MAMA).
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
               for the equity markets. By default, this parameter is not set and the technical indicator values
               will be calculated based on the most recent 30 days of intraday data. You can use the month
               parameter (in YYYY-MM format) to compute intraday technical indicators for a specific month
               in history. For example, month=2009-01.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV file.

    Returns:
        The Bollinger bands (BBANDS) values in JSON or CSV format.
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "time_period": str(time_period),
        "series_type": series_type,
        "nbdevup": str(nbdevup),
        "nbdevdn": str(nbdevdn),
        "matype": str(matype),
        "datatype": datatype,
    }
    if month:
        params["month"] = month

    return _make_api_request("BBANDS", params)


@tool
def midpoint(
    symbol: str,
    interval: str,
    time_period: int,
    series_type: str,
    month: str = None,
    datatype: str = "csv",
) -> dict[str, str] | str:
    """Returns the midpoint (MIDPOINT) values. MIDPOINT = (highest value + lowest value)/2.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        time_period: Number of data points used to calculate each MIDPOINT value. Positive integers are accepted.
        series_type: The desired price type in the time series. Four types are supported: close, open, high, low
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
               for the equity markets. By default, this parameter is not set and the technical indicator values
               will be calculated based on the most recent 30 days of intraday data. You can use the month
               parameter (in YYYY-MM format) to compute intraday technical indicators for a specific month
               in history. For example, month=2009-01.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV file.

    Returns:
        The midpoint (MIDPOINT) values in JSON or CSV format.
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "time_period": str(time_period),
        "series_type": series_type,
        "datatype": datatype,
    }
    if month:
        params["month"] = month

    return _make_api_request("MIDPOINT", params)


@tool
def midprice(
    symbol: str, interval: str, time_period: int, month: str = None, datatype: str = "csv"
) -> dict[str, str] | str:
    """Returns the midpoint price (MIDPRICE) values. MIDPRICE = (highest high + lowest low)/2.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        time_period: Number of data points used to calculate each MIDPRICE value. Positive integers are accepted.
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
               for the equity markets. By default, this parameter is not set and the technical indicator values
               will be calculated based on the most recent 30 days of intraday data. You can use the month
               parameter (in YYYY-MM format) to compute intraday technical indicators for a specific month
               in history. For example, month=2009-01.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV file.

    Returns:
        The midpoint price (MIDPRICE) values in JSON or CSV format.
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "time_period": str(time_period),
        "datatype": datatype,
    }
    if month:
        params["month"] = month

    return _make_api_request("MIDPRICE", params)


@tool
def sar(
    symbol: str,
    interval: str,
    acceleration: float = 0.01,
    maximum: float = 0.20,
    month: str = None,
    datatype: str = "csv",
) -> dict[str, str] | str:
    """Returns the parabolic SAR (SAR) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        acceleration: The acceleration factor. Positive floats are accepted. By default, acceleration=0.01.
        maximum: The acceleration factor maximum value. Positive floats are accepted. By default, maximum=0.20.
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
               for the equity markets. By default, this parameter is not set and the technical indicator values
               will be calculated based on the most recent 30 days of intraday data. You can use the month
               parameter (in YYYY-MM format) to compute intraday technical indicators for a specific month
               in history. For example, month=2009-01.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV file.

    Returns:
        The parabolic SAR (SAR) values in JSON or CSV format.
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "acceleration": str(acceleration),
        "maximum": str(maximum),
        "datatype": datatype,
    }
    if month:
        params["month"] = month

    return _make_api_request("SAR", params)


@tool
def trange(
    symbol: str, interval: str, month: str = None, datatype: str = "csv"
) -> dict[str, str] | str:
    """Returns the true range (TRANGE) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
               for the equity markets. By default, this parameter is not set and the technical indicator values
               will be calculated based on the most recent 30 days of intraday data. You can use the month
               parameter (in YYYY-MM format) to compute intraday technical indicators for a specific month
               in history. For example, month=2009-01.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV file.

    Returns:
        The true range (TRANGE) values in JSON or CSV format.
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "datatype": datatype,
    }
    if month:
        params["month"] = month

    return _make_api_request("TRANGE", params)


@tool
def atr(
    symbol: str, interval: str, time_period: int, month: str = None, datatype: str = "csv"
) -> dict[str, str] | str:
    """Returns the average true range (ATR) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        time_period: Number of data points used to calculate each ATR value. Positive integers are accepted.
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
               for the equity markets. By default, this parameter is not set and the technical indicator values
               will be calculated based on the most recent 30 days of intraday data. You can use the month
               parameter (in YYYY-MM format) to compute intraday technical indicators for a specific month
               in history. For example, month=2009-01.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV file.

    Returns:
        The average true range (ATR) values in JSON or CSV format.
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "time_period": str(time_period),
        "datatype": datatype,
    }
    if month:
        params["month"] = month

    return _make_api_request("ATR", params)


@tool
def natr(
    symbol: str, interval: str, time_period: int, month: str = None, datatype: str = "csv"
) -> dict[str, str] | str:
    """Returns the normalized average true range (NATR) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        time_period: Number of data points used to calculate each NATR value. Positive integers are accepted.
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
               for the equity markets. By default, this parameter is not set and the technical indicator values
               will be calculated based on the most recent 30 days of intraday data. You can use the month
               parameter (in YYYY-MM format) to compute intraday technical indicators for a specific month
               in history. For example, month=2009-01.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV file.

    Returns:
        The normalized average true range (NATR) values in JSON or CSV format.
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "time_period": str(time_period),
        "datatype": datatype,
    }
    if month:
        params["month"] = month

    return _make_api_request("NATR", params)
