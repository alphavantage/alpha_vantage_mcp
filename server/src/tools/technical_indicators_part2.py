from src.common import _make_api_request
from src.tools.registry import tool


@tool
def rsi(
    symbol: str,
    interval: str,
    time_period: int,
    series_type: str,
    month: str = None,
    datatype: str = "csv",
) -> dict[str, str] | str:
    """Returns the relative strength index (RSI) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        time_period: Number of data points used to calculate each RSI value. Positive integers are accepted (e.g., time_period=60, time_period=200)
        series_type: The desired price type in the time series. Four types are supported: close, open, high, low
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min) for the equity markets.
              By default, this parameter is not set and the technical indicator values will be calculated based on the most recent 30 days of intraday data.
              You can use the month parameter (in YYYY-MM format) to compute intraday technical indicators for a specific month in history.
              For example, month=2009-01. Any month equal to or later than 2000-01 (January 2000) is supported.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        RSI values in the specified format (dict or str).
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

    return _make_api_request("RSI", params)


@tool
def stochrsi(
    symbol: str,
    interval: str,
    time_period: int,
    series_type: str,
    month: str = None,
    fastkperiod: int = None,
    fastdperiod: int = None,
    fastdmatype: int = None,
    datatype: str = "csv",
) -> dict[str, str] | str:
    """Returns the stochastic relative strength index (STOCHRSI) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        time_period: Number of data points used to calculate each STOCHRSI value. Positive integers are accepted (e.g., time_period=60, time_period=200)
        series_type: The desired price type in the time series. Four types are supported: close, open, high, low
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min) for the equity markets.
              By default, this parameter is not set and the technical indicator values will be calculated based on the most recent 30 days of intraday data.
              You can use the month parameter (in YYYY-MM format) to compute intraday technical indicators for a specific month in history.
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
                 json returns the daily time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        STOCHRSI values in the specified format (dict or str).
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
    if fastkperiod is not None:
        params["fastkperiod"] = str(fastkperiod)
    if fastdperiod is not None:
        params["fastdperiod"] = str(fastdperiod)
    if fastdmatype is not None:
        params["fastdmatype"] = str(fastdmatype)

    return _make_api_request("STOCHRSI", params)


@tool
def willr(
    symbol: str, interval: str, time_period: int, month: str = None, datatype: str = "csv"
) -> dict[str, str] | str:
    """Returns the Williams' %R (WILLR) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        time_period: Number of data points used to calculate each WILLR value. Positive integers are accepted (e.g., time_period=60, time_period=200)
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min) for the equity markets.
              By default, this parameter is not set and the technical indicator values will be calculated based on the most recent 30 days of intraday data.
              You can use the month parameter (in YYYY-MM format) to compute intraday technical indicators for a specific month in history.
              For example, month=2009-01. Any month equal to or later than 2000-01 (January 2000) is supported.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        Williams' %R values in the specified format (dict or str).
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "time_period": str(time_period),
        "datatype": datatype,
    }
    if month:
        params["month"] = month

    return _make_api_request("WILLR", params)


@tool
def adx(
    symbol: str, interval: str, time_period: int, month: str = None, datatype: str = "csv"
) -> dict[str, str] | str:
    """Returns the average directional movement index (ADX) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        time_period: Number of data points used to calculate each ADX value. Positive integers are accepted (e.g., time_period=60, time_period=200)
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min) for the equity markets.
              By default, this parameter is not set and the technical indicator values will be calculated based on the most recent 30 days of intraday data.
              You can use the month parameter (in YYYY-MM format) to compute intraday technical indicators for a specific month in history.
              For example, month=2009-01. Any month equal to or later than 2000-01 (January 2000) is supported.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        ADX values in the specified format (dict or str).
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "time_period": str(time_period),
        "datatype": datatype,
    }
    if month:
        params["month"] = month

    return _make_api_request("ADX", params)


@tool
def adxr(
    symbol: str, interval: str, time_period: int, month: str = None, datatype: str = "csv"
) -> dict[str, str] | str:
    """Returns the average directional movement index rating (ADXR) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        time_period: Number of data points used to calculate each ADXR value. Positive integers are accepted (e.g., time_period=60, time_period=200)
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min) for the equity markets.
              By default, this parameter is not set and the technical indicator values will be calculated based on the most recent 30 days of intraday data.
              You can use the month parameter (in YYYY-MM format) to compute intraday technical indicators for a specific month in history.
              For example, month=2009-01. Any month equal to or later than 2000-01 (January 2000) is supported.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        ADXR values in the specified format (dict or str).
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "time_period": str(time_period),
        "datatype": datatype,
    }
    if month:
        params["month"] = month

    return _make_api_request("ADXR", params)


@tool
def apo(
    symbol: str,
    interval: str,
    series_type: str,
    month: str = None,
    fastperiod: int = None,
    slowperiod: int = None,
    matype: int = None,
    datatype: str = "csv",
) -> dict[str, str] | str:
    """Returns the absolute price oscillator (APO) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        series_type: The desired price type in the time series. Four types are supported: close, open, high, low
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min) for the equity markets.
              By default, this parameter is not set and the technical indicator values will be calculated based on the most recent 30 days of intraday data.
              You can use the month parameter (in YYYY-MM format) to compute intraday technical indicators for a specific month in history.
              For example, month=2009-01. Any month equal to or later than 2000-01 (January 2000) is supported.
        fastperiod: Positive integers are accepted. By default, fastperiod=12.
        slowperiod: Positive integers are accepted. By default, slowperiod=26.
        matype: Moving average type. By default, matype=0. Integers 0 - 8 are accepted with the following mappings.
               0 = Simple Moving Average (SMA), 1 = Exponential Moving Average (EMA), 2 = Weighted Moving Average (WMA),
               3 = Double Exponential Moving Average (DEMA), 4 = Triple Exponential Moving Average (TEMA),
               5 = Triangular Moving Average (TRIMA), 6 = T3 Moving Average, 7 = Kaufman Adaptive Moving Average (KAMA),
               8 = MESA Adaptive Moving Average (MAMA).
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        APO values in the specified format (dict or str).
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "series_type": series_type,
        "datatype": datatype,
    }
    if month:
        params["month"] = month
    if fastperiod is not None:
        params["fastperiod"] = str(fastperiod)
    if slowperiod is not None:
        params["slowperiod"] = str(slowperiod)
    if matype is not None:
        params["matype"] = str(matype)

    return _make_api_request("APO", params)


@tool
def ppo(
    symbol: str,
    interval: str,
    series_type: str,
    month: str = None,
    fastperiod: int = None,
    slowperiod: int = None,
    matype: int = None,
    datatype: str = "csv",
) -> dict[str, str] | str:
    """Returns the percentage price oscillator (PPO) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        series_type: The desired price type in the time series. Four types are supported: close, open, high, low
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min) for the equity markets.
              By default, this parameter is not set and the technical indicator values will be calculated based on the most recent 30 days of intraday data.
              You can use the month parameter (in YYYY-MM format) to compute intraday technical indicators for a specific month in history.
              For example, month=2009-01. Any month equal to or later than 2000-01 (January 2000) is supported.
        fastperiod: Positive integers are accepted. By default, fastperiod=12.
        slowperiod: Positive integers are accepted. By default, slowperiod=26.
        matype: Moving average type. By default, matype=0. Integers 0 - 8 are accepted with the following mappings.
               0 = Simple Moving Average (SMA), 1 = Exponential Moving Average (EMA), 2 = Weighted Moving Average (WMA),
               3 = Double Exponential Moving Average (DEMA), 4 = Triple Exponential Moving Average (TEMA),
               5 = Triangular Moving Average (TRIMA), 6 = T3 Moving Average, 7 = Kaufman Adaptive Moving Average (KAMA),
               8 = MESA Adaptive Moving Average (MAMA).
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        PPO values in the specified format (dict or str).
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "series_type": series_type,
        "datatype": datatype,
    }
    if month:
        params["month"] = month
    if fastperiod is not None:
        params["fastperiod"] = str(fastperiod)
    if slowperiod is not None:
        params["slowperiod"] = str(slowperiod)
    if matype is not None:
        params["matype"] = str(matype)

    return _make_api_request("PPO", params)


@tool
def mom(
    symbol: str,
    interval: str,
    time_period: int,
    series_type: str,
    month: str = None,
    datatype: str = "csv",
) -> dict[str, str] | str:
    """Returns the momentum (MOM) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        time_period: Number of data points used to calculate each MOM value. Positive integers are accepted (e.g., time_period=60, time_period=200)
        series_type: The desired price type in the time series. Four types are supported: close, open, high, low
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min) for the equity markets.
              By default, this parameter is not set and the technical indicator values will be calculated based on the most recent 30 days of intraday data.
              You can use the month parameter (in YYYY-MM format) to compute intraday technical indicators for a specific month in history.
              For example, month=2009-01. Any month equal to or later than 2000-01 (January 2000) is supported.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        Momentum values in the specified format (dict or str).
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

    return _make_api_request("MOM", params)


@tool
def bop(
    symbol: str, interval: str, month: str = None, datatype: str = "csv"
) -> dict[str, str] | str:
    """Returns the balance of power (BOP) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min) for the equity markets.
              By default, this parameter is not set and the technical indicator values will be calculated based on the most recent 30 days of intraday data.
              You can use the month parameter (in YYYY-MM format) to compute intraday technical indicators for a specific month in history.
              For example, month=2009-01. Any month equal to or later than 2000-01 (January 2000) is supported.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        Balance of power values in the specified format (dict or str).
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "datatype": datatype,
    }
    if month:
        params["month"] = month

    return _make_api_request("BOP", params)


@tool
def cci(
    symbol: str, interval: str, time_period: int, month: str = None, datatype: str = "csv"
) -> dict[str, str] | str:
    """Returns the commodity channel index (CCI) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        time_period: Number of data points used to calculate each CCI value. Positive integers are accepted (e.g., time_period=60, time_period=200)
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min) for the equity markets.
              By default, this parameter is not set and the technical indicator values will be calculated based on the most recent 30 days of intraday data.
              You can use the month parameter (in YYYY-MM format) to compute intraday technical indicators for a specific month in history.
              For example, month=2009-01. Any month equal to or later than 2000-01 (January 2000) is supported.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        Commodity channel index values in the specified format (dict or str).
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "time_period": str(time_period),
        "datatype": datatype,
    }
    if month:
        params["month"] = month

    return _make_api_request("CCI", params)


@tool
def cmo(
    symbol: str,
    interval: str,
    time_period: int,
    series_type: str,
    month: str = None,
    datatype: str = "csv",
) -> dict[str, str] | str:
    """Returns the Chande momentum oscillator (CMO) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        time_period: Number of data points used to calculate each CMO value. Positive integers are accepted (e.g., time_period=60, time_period=200)
        series_type: The desired price type in the time series. Four types are supported: close, open, high, low
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min) for the equity markets.
              By default, this parameter is not set and the technical indicator values will be calculated based on the most recent 30 days of intraday data.
              You can use the month parameter (in YYYY-MM format) to compute intraday technical indicators for a specific month in history.
              For example, month=2009-01. Any month equal to or later than 2000-01 (January 2000) is supported.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        Chande momentum oscillator values in the specified format (dict or str).
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

    return _make_api_request("CMO", params)


@tool
def roc(
    symbol: str,
    interval: str,
    time_period: int,
    series_type: str,
    month: str = None,
    datatype: str = "csv",
) -> dict[str, str] | str:
    """Returns the rate of change (ROC) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        time_period: Number of data points used to calculate each ROC value. Positive integers are accepted (e.g., time_period=60, time_period=200)
        series_type: The desired price type in the time series. Four types are supported: close, open, high, low
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min) for the equity markets.
              By default, this parameter is not set and the technical indicator values will be calculated based on the most recent 30 days of intraday data.
              You can use the month parameter (in YYYY-MM format) to compute intraday technical indicators for a specific month in history.
              For example, month=2009-01. Any month equal to or later than 2000-01 (January 2000) is supported.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        Rate of change values in the specified format (dict or str).
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

    return _make_api_request("ROC", params)


@tool
def rocr(
    symbol: str,
    interval: str,
    time_period: int,
    series_type: str,
    month: str = None,
    datatype: str = "csv",
) -> dict[str, str] | str:
    """Returns the rate of change ratio (ROCR) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        time_period: Number of data points used to calculate each ROCR value. Positive integers are accepted (e.g., time_period=60, time_period=200)
        series_type: The desired price type in the time series. Four types are supported: close, open, high, low
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min) for the equity markets.
              By default, this parameter is not set and the technical indicator values will be calculated based on the most recent 30 days of intraday data.
              You can use the month parameter (in YYYY-MM format) to compute intraday technical indicators for a specific month in history.
              For example, month=2009-01. Any month equal to or later than 2000-01 (January 2000) is supported.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        Rate of change ratio values in the specified format (dict or str).
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

    return _make_api_request("ROCR", params)


@tool
def aroon(
    symbol: str, interval: str, time_period: int, month: str = None, datatype: str = "csv"
) -> dict[str, str] | str:
    """Returns the Aroon (AROON) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        time_period: Number of data points used to calculate each AROON value. Positive integers are accepted (e.g., time_period=60, time_period=200)
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min) for the equity markets.
              By default, this parameter is not set and the technical indicator values will be calculated based on the most recent 30 days of intraday data.
              You can use the month parameter (in YYYY-MM format) to compute intraday technical indicators for a specific month in history.
              For example, month=2009-01. Any month equal to or later than 2000-01 (January 2000) is supported.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        Aroon values in the specified format (dict or str).
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "time_period": str(time_period),
        "datatype": datatype,
    }
    if month:
        params["month"] = month

    return _make_api_request("AROON", params)


@tool
def aroonosc(
    symbol: str, interval: str, time_period: int, month: str = None, datatype: str = "csv"
) -> dict[str, str] | str:
    """Returns the Aroon oscillator (AROONOSC) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        time_period: Number of data points used to calculate each AROONOSC value. Positive integers are accepted (e.g., time_period=60, time_period=200)
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min) for the equity markets.
              By default, this parameter is not set and the technical indicator values will be calculated based on the most recent 30 days of intraday data.
              You can use the month parameter (in YYYY-MM format) to compute intraday technical indicators for a specific month in history.
              For example, month=2009-01. Any month equal to or later than 2000-01 (January 2000) is supported.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        Aroon oscillator values in the specified format (dict or str).
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "time_period": str(time_period),
        "datatype": datatype,
    }
    if month:
        params["month"] = month

    return _make_api_request("AROONOSC", params)
