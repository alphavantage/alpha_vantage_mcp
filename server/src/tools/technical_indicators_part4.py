from src.common import _make_api_request
from src.tools.registry import tool


@tool
def ad(
    symbol: str, interval: str, month: str = None, datatype: str = "csv"
) -> dict[str, str] | str:
    """Returns the Chaikin A/D line (AD) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
               for the equity markets. The daily/weekly/monthly intervals are agnostic to this parameter.
               By default, this parameter is not set and the technical indicator values will be calculated based on
               the most recent 30 days of intraday data. You can use the month parameter (in YYYY-MM format) to compute
               intraday technical indicators for a specific month in history. For example, month=2009-01.
               Any month equal to or later than 2000-01 (January 2000) is supported.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV
                 (comma separated value) file.

    Returns:
        The Chaikin A/D line values in the specified format.
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "datatype": datatype,
    }
    if month:
        params["month"] = month

    return _make_api_request("AD", params)


@tool
def adosc(
    symbol: str,
    interval: str,
    month: str = None,
    fastperiod: int = 3,
    slowperiod: int = 10,
    datatype: str = "csv",
) -> dict[str, str] | str:
    """Returns the Chaikin A/D oscillator (ADOSC) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
               for the equity markets. The daily/weekly/monthly intervals are agnostic to this parameter.
               By default, this parameter is not set and the technical indicator values will be calculated based on
               the most recent 30 days of intraday data. You can use the month parameter (in YYYY-MM format) to compute
               intraday technical indicators for a specific month in history. For example, month=2009-01.
               Any month equal to or later than 2000-01 (January 2000) is supported.
        fastperiod: The time period of the fast EMA. Positive integers are accepted. By default, fastperiod=3.
        slowperiod: The time period of the slow EMA. Positive integers are accepted. By default, slowperiod=10.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV
                 (comma separated value) file.

    Returns:
        The Chaikin A/D oscillator values in the specified format.
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "datatype": datatype,
    }
    if month:
        params["month"] = month
    if fastperiod != 3:
        params["fastperiod"] = str(fastperiod)
    if slowperiod != 10:
        params["slowperiod"] = str(slowperiod)

    return _make_api_request("ADOSC", params)


@tool
def obv(
    symbol: str, interval: str, month: str = None, datatype: str = "csv"
) -> dict[str, str] | str:
    """Returns the on balance volume (OBV) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
               for the equity markets. The daily/weekly/monthly intervals are agnostic to this parameter.
               By default, this parameter is not set and the technical indicator values will be calculated based on
               the most recent 30 days of intraday data. You can use the month parameter (in YYYY-MM format) to compute
               intraday technical indicators for a specific month in history. For example, month=2009-01.
               Any month equal to or later than 2000-01 (January 2000) is supported.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV
                 (comma separated value) file.

    Returns:
        The on balance volume values in the specified format.
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "datatype": datatype,
    }
    if month:
        params["month"] = month

    return _make_api_request("OBV", params)


@tool
def ht_trendline(
    symbol: str, interval: str, series_type: str, month: str = None, datatype: str = "csv"
) -> dict[str, str] | str:
    """Returns the Hilbert transform, instantaneous trendline (HT_TRENDLINE) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        series_type: The desired price type in the time series. Four types are supported: close, open, high, low
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
               for the equity markets. The daily/weekly/monthly intervals are agnostic to this parameter.
               By default, this parameter is not set and the technical indicator values will be calculated based on
               the most recent 30 days of intraday data. You can use the month parameter (in YYYY-MM format) to compute
               intraday technical indicators for a specific month in history. For example, month=2009-01.
               Any month equal to or later than 2000-01 (January 2000) is supported.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV
                 (comma separated value) file.

    Returns:
        The Hilbert transform instantaneous trendline values in the specified format.
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "series_type": series_type,
        "datatype": datatype,
    }
    if month:
        params["month"] = month

    return _make_api_request("HT_TRENDLINE", params)


@tool
def ht_sine(
    symbol: str, interval: str, series_type: str, month: str = None, datatype: str = "csv"
) -> dict[str, str] | str:
    """Returns the Hilbert transform, sine wave (HT_SINE) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        series_type: The desired price type in the time series. Four types are supported: close, open, high, low
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
               for the equity markets. The daily/weekly/monthly intervals are agnostic to this parameter.
               By default, this parameter is not set and the technical indicator values will be calculated based on
               the most recent 30 days of intraday data. You can use the month parameter (in YYYY-MM format) to compute
               intraday technical indicators for a specific month in history. For example, month=2009-01.
               Any month equal to or later than 2000-01 (January 2000) is supported.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV
                 (comma separated value) file.

    Returns:
        The Hilbert transform sine wave values in the specified format.
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "series_type": series_type,
        "datatype": datatype,
    }
    if month:
        params["month"] = month

    return _make_api_request("HT_SINE", params)


@tool
def ht_trendmode(
    symbol: str, interval: str, series_type: str, month: str = None, datatype: str = "csv"
) -> dict[str, str] | str:
    """Returns the Hilbert transform, trend vs cycle mode (HT_TRENDMODE) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        series_type: The desired price type in the time series. Four types are supported: close, open, high, low
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
               for the equity markets. The daily/weekly/monthly intervals are agnostic to this parameter.
               By default, this parameter is not set and the technical indicator values will be calculated based on
               the most recent 30 days of intraday data. You can use the month parameter (in YYYY-MM format) to compute
               intraday technical indicators for a specific month in history. For example, month=2009-01.
               Any month equal to or later than 2000-01 (January 2000) is supported.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV
                 (comma separated value) file.

    Returns:
        The Hilbert transform trend vs cycle mode values in the specified format.
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "series_type": series_type,
        "datatype": datatype,
    }
    if month:
        params["month"] = month

    return _make_api_request("HT_TRENDMODE", params)


@tool
def ht_dcperiod(
    symbol: str, interval: str, series_type: str, month: str = None, datatype: str = "csv"
) -> dict[str, str] | str:
    """Returns the Hilbert transform, dominant cycle period (HT_DCPERIOD) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        series_type: The desired price type in the time series. Four types are supported: close, open, high, low
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
               for the equity markets. The daily/weekly/monthly intervals are agnostic to this parameter.
               By default, this parameter is not set and the technical indicator values will be calculated based on
               the most recent 30 days of intraday data. You can use the month parameter (in YYYY-MM format) to compute
               intraday technical indicators for a specific month in history. For example, month=2009-01.
               Any month equal to or later than 2000-01 (January 2000) is supported.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV
                 (comma separated value) file.

    Returns:
        The Hilbert transform dominant cycle period values in the specified format.
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "series_type": series_type,
        "datatype": datatype,
    }
    if month:
        params["month"] = month

    return _make_api_request("HT_DCPERIOD", params)


@tool
def ht_dcphase(
    symbol: str, interval: str, series_type: str, month: str = None, datatype: str = "csv"
) -> dict[str, str] | str:
    """Returns the Hilbert transform, dominant cycle phase (HT_DCPHASE) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        series_type: The desired price type in the time series. Four types are supported: close, open, high, low
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
               for the equity markets. The daily/weekly/monthly intervals are agnostic to this parameter.
               By default, this parameter is not set and the technical indicator values will be calculated based on
               the most recent 30 days of intraday data. You can use the month parameter (in YYYY-MM format) to compute
               intraday technical indicators for a specific month in history. For example, month=2009-01.
               Any month equal to or later than 2000-01 (January 2000) is supported.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV
                 (comma separated value) file.

    Returns:
        The Hilbert transform dominant cycle phase values in the specified format.
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "series_type": series_type,
        "datatype": datatype,
    }
    if month:
        params["month"] = month

    return _make_api_request("HT_DCPHASE", params)


@tool
def ht_phasor(
    symbol: str, interval: str, series_type: str, month: str = None, datatype: str = "csv"
) -> dict[str, str] | str:
    """Returns the Hilbert transform, phasor components (HT_PHASOR) values.

    Args:
        symbol: The name of the ticker of your choice. For example: symbol=IBM
        interval: Time interval between two consecutive data points in the time series.
                 The following values are supported: 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
        series_type: The desired price type in the time series. Four types are supported: close, open, high, low
        month: Note: this parameter is ONLY applicable to intraday intervals (1min, 5min, 15min, 30min, and 60min)
               for the equity markets. The daily/weekly/monthly intervals are agnostic to this parameter.
               By default, this parameter is not set and the technical indicator values will be calculated based on
               the most recent 30 days of intraday data. You can use the month parameter (in YYYY-MM format) to compute
               intraday technical indicators for a specific month in history. For example, month=2009-01.
               Any month equal to or later than 2000-01 (January 2000) is supported.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the daily time series in JSON format; csv returns the time series as a CSV
                 (comma separated value) file.

    Returns:
        The Hilbert transform phasor components values in the specified format.
    """

    params = {
        "symbol": symbol,
        "interval": interval,
        "series_type": series_type,
        "datatype": datatype,
    }
    if month:
        params["month"] = month

    return _make_api_request("HT_PHASOR", params)
