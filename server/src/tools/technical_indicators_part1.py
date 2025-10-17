from src.common import _make_api_request
from src.tools.registry import tool


@tool
def sma(
    symbol: str,
    interval: str,
    time_period: int,
    series_type: str,
    month: str = None,
    datatype: str = "csv",
) -> dict[str, str] | str:
    """
    Returns the simple moving average (SMA) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        time_period: Number of data points used to calculate each moving average value.
                    Positive integers are accepted (e.g., time_period=60, time_period=200)
        series_type: The desired price type in the time series. Four types are supported: close, open, high, low
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
              for the equity markets. By default, this parameter is not set and the technical indicator values will
              be calculated based on the most recent 30 days of intraday data. You can use the month parameter
              (in YYYY-MM format) to compute intraday technical indicators for a specific month in history.
              For example, month=2009-01. Any month equal to or later than 2000-01 (January 2000) is supported.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV file.

    Returns:
        The SMA values in JSON or CSV format.
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

    return _make_api_request("SMA", params)


@tool
def ema(
    symbol: str,
    interval: str,
    time_period: int,
    series_type: str,
    month: str = None,
    datatype: str = "csv",
) -> dict[str, str] | str:
    """
    Returns the exponential moving average (EMA) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        time_period: Number of data points used to calculate each moving average value.
                    Positive integers are accepted (e.g., time_period=60, time_period=200)
        series_type: The desired price type in the time series. Four types are supported: close, open, high, low
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
              for the equity markets. By default, this parameter is not set and the technical indicator values will
              be calculated based on the most recent 30 days of intraday data. You can use the month parameter
              (in YYYY-MM format) to compute intraday technical indicators for a specific month in history.
              For example, month=2009-01. Any month equal to or later than 2000-01 (January 2000) is supported.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV file.

    Returns:
        The EMA values in JSON or CSV format.
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

    return _make_api_request("EMA", params)


@tool
def wma(
    symbol: str,
    interval: str,
    time_period: int,
    series_type: str,
    month: str = None,
    datatype: str = "csv",
) -> dict[str, str] | str:
    """
    Returns the weighted moving average (WMA) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        time_period: Number of data points used to calculate each moving average value.
                    Positive integers are accepted (e.g., time_period=60, time_period=200)
        series_type: The desired price type in the time series. Four types are supported: close, open, high, low
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
              for the equity markets. By default, this parameter is not set and the technical indicator values will
              be calculated based on the most recent 30 days of intraday data. You can use the month parameter
              (in YYYY-MM format) to compute intraday technical indicators for a specific month in history.
              For example, month=2009-01. Any month equal to or later than 2000-01 (January 2000) is supported.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV file.

    Returns:
        The WMA values in JSON or CSV format.
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

    return _make_api_request("WMA", params)


@tool
def dema(
    symbol: str,
    interval: str,
    time_period: int,
    series_type: str,
    month: str = None,
    datatype: str = "csv",
) -> dict[str, str] | str:
    """
    Returns the double exponential moving average (DEMA) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        time_period: Number of data points used to calculate each moving average value.
                    Positive integers are accepted (e.g., time_period=60, time_period=200)
        series_type: The desired price type in the time series. Four types are supported: close, open, high, low
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
              for the equity markets. By default, this parameter is not set and the technical indicator values will
              be calculated based on the most recent 30 days of intraday data. You can use the month parameter
              (in YYYY-MM format) to compute intraday technical indicators for a specific month in history.
              For example, month=2009-01. Any month equal to or later than 2000-01 (January 2000) is supported.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV file.

    Returns:
        The DEMA values in JSON or CSV format.
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

    return _make_api_request("DEMA", params)


@tool
def tema(
    symbol: str,
    interval: str,
    time_period: int,
    series_type: str,
    month: str = None,
    datatype: str = "csv",
) -> dict[str, str] | str:
    """
    Returns the triple exponential moving average (TEMA) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        time_period: Number of data points used to calculate each moving average value.
                    Positive integers are accepted (e.g., time_period=60, time_period=200)
        series_type: The desired price type in the time series. Four types are supported: close, open, high, low
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
              for the equity markets. By default, this parameter is not set and the technical indicator values will
              be calculated based on the most recent 30 days of intraday data. You can use the month parameter
              (in YYYY-MM format) to compute intraday technical indicators for a specific month in history.
              For example, month=2009-01. Any month equal to or later than 2000-01 (January 2000) is supported.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV file.

    Returns:
        The TEMA values in JSON or CSV format.
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

    return _make_api_request("TEMA", params)


@tool
def trima(
    symbol: str,
    interval: str,
    time_period: int,
    series_type: str,
    month: str = None,
    datatype: str = "csv",
) -> dict[str, str] | str:
    """
    Returns the triangular moving average (TRIMA) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        time_period: Number of data points used to calculate each moving average value.
                    Positive integers are accepted (e.g., time_period=60, time_period=200)
        series_type: The desired price type in the time series. Four types are supported: close, open, high, low
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
              for the equity markets. By default, this parameter is not set and the technical indicator values will
              be calculated based on the most recent 30 days of intraday data. You can use the month parameter
              (in YYYY-MM format) to compute intraday technical indicators for a specific month in history.
              For example, month=2009-01. Any month equal to or later than 2000-01 (January 2000) is supported.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV file.

    Returns:
        The TRIMA values in JSON or CSV format.
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

    return _make_api_request("TRIMA", params)


@tool
def kama(
    symbol: str,
    interval: str,
    time_period: int,
    series_type: str,
    month: str = None,
    datatype: str = "csv",
) -> dict[str, str] | str:
    """
    Returns the Kaufman adaptive moving average (KAMA) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        time_period: Number of data points used to calculate each moving average value.
                    Positive integers are accepted (e.g., time_period=60, time_period=200)
        series_type: The desired price type in the time series. Four types are supported: close, open, high, low
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
              for the equity markets. By default, this parameter is not set and the technical indicator values will
              be calculated based on the most recent 30 days of intraday data. You can use the month parameter
              (in YYYY-MM format) to compute intraday technical indicators for a specific month in history.
              For example, month=2009-01. Any month equal to or later than 2000-01 (January 2000) is supported.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV file.

    Returns:
        The KAMA values in JSON or CSV format.
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

    return _make_api_request("KAMA", params)


@tool
def mama(
    symbol: str,
    interval: str,
    series_type: str,
    month: str = None,
    fastlimit: float = 0.01,
    slowlimit: float = 0.01,
    datatype: str = "csv",
) -> dict[str, str] | str:
    """
    Returns the MESA adaptive moving average (MAMA) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        series_type: The desired price type in the time series. Four types are supported: close, open, high, low
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
              for the equity markets. By default, this parameter is not set and the technical indicator values will
              be calculated based on the most recent 30 days of intraday data. You can use the month parameter
              (in YYYY-MM format) to compute intraday technical indicators for a specific month in history.
              For example, month=2009-01. Any month equal to or later than 2000-01 (January 2000) is supported.
        fastlimit: Positive floats are accepted. By default, fastlimit=0.01.
        slowlimit: Positive floats are accepted. By default, slowlimit=0.01.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV file.

    Returns:
        The MAMA values in JSON or CSV format.
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "series_type": series_type,
        "datatype": datatype,
    }
    if month:
        params["month"] = month
    if fastlimit != 0.01:
        params["fastlimit"] = str(fastlimit)
    if slowlimit != 0.01:
        params["slowlimit"] = str(slowlimit)

    return _make_api_request("MAMA", params)


@tool
def vwap(
    symbol: str, interval: str, month: str = None, datatype: str = "csv"
) -> dict[str, str] | str:
    """
    Returns the volume weighted average price (VWAP) for intraday time series.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 In keeping with mainstream investment literatures on VWAP, the following
                 intraday intervals are supported: 1min, 5min, 15min, 30min, 60min
        month: By default, this parameter is not set and the technical indicator values will
              be calculated based on the most recent 30 days of intraday data. You can use the month parameter
              (in YYYY-MM format) to compute intraday technical indicators for a specific month in history.
              For example, month=2009-01. Any month equal to or later than 2000-01 (January 2000) is supported.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV file.

    Returns:
        The VWAP values in JSON or CSV format.
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "datatype": datatype,
    }
    if month:
        params["month"] = month

    return _make_api_request("VWAP", params)


@tool
def t3(
    symbol: str,
    interval: str,
    time_period: int,
    series_type: str,
    month: str = None,
    datatype: str = "csv",
) -> dict[str, str] | str:
    """
    Returns the triple exponential moving average (T3) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        time_period: Number of data points used to calculate each moving average value.
                    Positive integers are accepted (e.g., time_period=60, time_period=200)
        series_type: The desired price type in the time series. Four types are supported: close, open, high, low
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
              for the equity markets. By default, this parameter is not set and the technical indicator values will
              be calculated based on the most recent 30 days of intraday data. You can use the month parameter
              (in YYYY-MM format) to compute intraday technical indicators for a specific month in history.
              For example, month=2009-01. Any month equal to or later than 2000-01 (January 2000) is supported.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV file.

    Returns:
        The T3 values in JSON or CSV format.
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

    return _make_api_request("T3", params)


@tool
def macd(
    symbol: str,
    interval: str,
    series_type: str,
    month: str = None,
    fastperiod: int = 12,
    slowperiod: int = 26,
    signalperiod: int = 9,
    datatype: str = "csv",
) -> dict[str, str] | str:
    """
    Returns the moving average convergence / divergence (MACD) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        series_type: The desired price type in the time series. Four types are supported: close, open, high, low
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
              for the equity markets. By default, this parameter is not set and the technical indicator values will
              be calculated based on the most recent 30 days of intraday data. You can use the month parameter
              (in YYYY-MM format) to compute intraday technical indicators for a specific month in history.
              For example, month=2009-01. Any month equal to or later than 2000-01 (January 2000) is supported.
        fastperiod: Positive integers are accepted. By default, fastperiod=12.
        slowperiod: Positive integers are accepted. By default, slowperiod=26.
        signalperiod: Positive integers are accepted. By default, signalperiod=9.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV file.

    Returns:
        The MACD values in JSON or CSV format.
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "series_type": series_type,
        "datatype": datatype,
    }
    if month:
        params["month"] = month
    if fastperiod != 12:
        params["fastperiod"] = str(fastperiod)
    if slowperiod != 26:
        params["slowperiod"] = str(slowperiod)
    if signalperiod != 9:
        params["signalperiod"] = str(signalperiod)

    return _make_api_request("MACD", params)


@tool
def macdext(
    symbol: str,
    interval: str,
    series_type: str,
    month: str = None,
    fastperiod: int = 12,
    slowperiod: int = 26,
    signalperiod: int = 9,
    fastmatype: int = 0,
    slowmatype: int = 0,
    signalmatype: int = 0,
    datatype: str = "csv",
) -> dict[str, str] | str:
    """
    Returns the moving average convergence / divergence values with controllable moving average type.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        series_type: The desired price type in the time series. Four types are supported: close, open, high, low
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
              for the equity markets. By default, this parameter is not set and the technical indicator values will
              be calculated based on the most recent 30 days of intraday data. You can use the month parameter
              (in YYYY-MM format) to compute intraday technical indicators for a specific month in history.
              For example, month=2009-01. Any month equal to or later than 2000-01 (January 2000) is supported.
        fastperiod: Positive integers are accepted. By default, fastperiod=12.
        slowperiod: Positive integers are accepted. By default, slowperiod=26.
        signalperiod: Positive integers are accepted. By default, signalperiod=9.
        fastmatype: Moving average type for the faster moving average. By default, fastmatype=0.
                   Integers 0 - 8 are accepted with the following mappings. 0 = Simple Moving Average (SMA),
                   1 = Exponential Moving Average (EMA), 2 = Weighted Moving Average (WMA),
                   3 = Double Exponential Moving Average (DEMA), 4 = Triple Exponential Moving Average (TEMA),
                   5 = Triangular Moving Average (TRIMA), 6 = T3 Moving Average, 7 = Kaufman Adaptive Moving Average (KAMA),
                   8 = MESA Adaptive Moving Average (MAMA).
        slowmatype: Moving average type for the slower moving average. By default, slowmatype=0.
                   Integers 0 - 8 are accepted with the following mappings. 0 = Simple Moving Average (SMA),
                   1 = Exponential Moving Average (EMA), 2 = Weighted Moving Average (WMA),
                   3 = Double Exponential Moving Average (DEMA), 4 = Triple Exponential Moving Average (TEMA),
                   5 = Triangular Moving Average (TRIMA), 6 = T3 Moving Average, 7 = Kaufman Adaptive Moving Average (KAMA),
                   8 = MESA Adaptive Moving Average (MAMA).
        signalmatype: Moving average type for the signal moving average. By default, signalmatype=0.
                     Integers 0 - 8 are accepted with the following mappings. 0 = Simple Moving Average (SMA),
                     1 = Exponential Moving Average (EMA), 2 = Weighted Moving Average (WMA),
                     3 = Double Exponential Moving Average (DEMA), 4 = Triple Exponential Moving Average (TEMA),
                     5 = Triangular Moving Average (TRIMA), 6 = T3 Moving Average, 7 = Kaufman Adaptive Moving Average (KAMA),
                     8 = MESA Adaptive Moving Average (MAMA).
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV file.

    Returns:
        The MACDEXT values in JSON or CSV format.
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "series_type": series_type,
        "datatype": datatype,
    }
    if month:
        params["month"] = month
    if fastperiod != 12:
        params["fastperiod"] = str(fastperiod)
    if slowperiod != 26:
        params["slowperiod"] = str(slowperiod)
    if signalperiod != 9:
        params["signalperiod"] = str(signalperiod)
    if fastmatype != 0:
        params["fastmatype"] = str(fastmatype)
    if slowmatype != 0:
        params["slowmatype"] = str(slowmatype)
    if signalmatype != 0:
        params["signalmatype"] = str(signalmatype)

    return _make_api_request("MACDEXT", params)


@tool
def stoch(
    symbol: str,
    interval: str,
    month: str = None,
    fastkperiod: int = 5,
    slowkperiod: int = 3,
    slowdperiod: int = 3,
    slowkmatype: int = 0,
    slowdmatype: int = 0,
    datatype: str = "csv",
) -> dict[str, str] | str:
    """
    Returns the stochastic oscillator (STOCH) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
              for the equity markets. By default, this parameter is not set and the technical indicator values will
              be calculated based on the most recent 30 days of intraday data. You can use the month parameter
              (in YYYY-MM format) to compute intraday technical indicators for a specific month in history.
              For example, month=2009-01. Any month equal to or later than 2000-01 (January 2000) is supported.
        fastkperiod: The time period of the fastk moving average. Positive integers are accepted. By default, fastkperiod=5.
        slowkperiod: The time period of the slowk moving average. Positive integers are accepted. By default, slowkperiod=3.
        slowdperiod: The time period of the slowd moving average. Positive integers are accepted. By default, slowdperiod=3.
        slowkmatype: Moving average type for the slowk moving average. By default, slowkmatype=0.
                    Integers 0 - 8 are accepted with the following mappings. 0 = Simple Moving Average (SMA),
                    1 = Exponential Moving Average (EMA), 2 = Weighted Moving Average (WMA),
                    3 = Double Exponential Moving Average (DEMA), 4 = Triple Exponential Moving Average (TEMA),
                    5 = Triangular Moving Average (TRIMA), 6 = T3 Moving Average, 7 = Kaufman Adaptive Moving Average (KAMA),
                    8 = MESA Adaptive Moving Average (MAMA).
        slowdmatype: Moving average type for the slowd moving average. By default, slowdmatype=0.
                    Integers 0 - 8 are accepted with the following mappings. 0 = Simple Moving Average (SMA),
                    1 = Exponential Moving Average (EMA), 2 = Weighted Moving Average (WMA),
                    3 = Double Exponential Moving Average (DEMA), 4 = Triple Exponential Moving Average (TEMA),
                    5 = Triangular Moving Average (TRIMA), 6 = T3 Moving Average, 7 = Kaufman Adaptive Moving Average (KAMA),
                    8 = MESA Adaptive Moving Average (MAMA).
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV file.

    Returns:
        The STOCH values in JSON or CSV format.
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "datatype": datatype,
    }
    if month:
        params["month"] = month
    if fastkperiod != 5:
        params["fastkperiod"] = str(fastkperiod)
    if slowkperiod != 3:
        params["slowkperiod"] = str(slowkperiod)
    if slowdperiod != 3:
        params["slowdperiod"] = str(slowdperiod)
    if slowkmatype != 0:
        params["slowkmatype"] = str(slowkmatype)
    if slowdmatype != 0:
        params["slowdmatype"] = str(slowdmatype)

    return _make_api_request("STOCH", params)


@tool
def stochf(
    symbol: str,
    interval: str,
    month: str = None,
    fastkperiod: int = 5,
    fastdperiod: int = 3,
    fastdmatype: int = 0,
    datatype: str = "csv",
) -> dict[str, str] | str:
    """
    Returns the stochastic fast (STOCHF) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
              for the equity markets. By default, this parameter is not set and the technical indicator values will
              be calculated based on the most recent 30 days of intraday data. You can use the month parameter
              (in YYYY-MM format) to compute intraday technical indicators for a specific month in history.
              For example, month=2009-01. Any month equal to or later than 2000-01 (January 2000) is supported.
        fastkperiod: The time period of the fastk moving average. Positive integers are accepted. By default, fastkperiod=5.
        fastdperiod: The time period of the fastd moving average. Positive integers are accepted. By default, fastdperiod=3.
        fastdmatype: Moving average type for the fastd moving average. By default, fastdmatype=0.
                    Integers 0 - 8 are accepted with the following mappings. 0 = Simple Moving Average (SMA),
                    1 = Exponential Moving Average (EMA), 2 = Weighted Moving Average (WMA),
                    3 = Double Exponential Moving Average (DEMA), 4 = Triple Exponential Moving Average (TEMA),
                    5 = Triangular Moving Average (TRIMA), 6 = T3 Moving Average, 7 = Kaufman Adaptive Moving Average (KAMA),
                    8 = MESA Adaptive Moving Average (MAMA).
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV file.

    Returns:
        The STOCHF values in JSON or CSV format.
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "datatype": datatype,
    }
    if month:
        params["month"] = month
    if fastkperiod != 5:
        params["fastkperiod"] = str(fastkperiod)
    if fastdperiod != 3:
        params["fastdperiod"] = str(fastdperiod)
    if fastdmatype != 0:
        params["fastdmatype"] = str(fastdmatype)

    return _make_api_request("STOCHF", params)
