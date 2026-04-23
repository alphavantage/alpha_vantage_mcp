from av_api.client import _make_api_request
from av_api.registry import tool

@tool
def realtime_options(
    symbol: str,
    require_greeks: bool = False,
    contract: str = None,
    expiration: str = None,
    datatype: str = "csv"
) -> dict[str, str] | str:
    """Returns realtime US options data with full market coverage.
    
    Option chains are sorted by expiration dates in chronological order. 
    Within the same expiration date, contracts are sorted by strike prices from low to high.

    Args:
        symbol: The name of the equity of your choice. For example: symbol=IBM
        require_greeks: Enable greeks & implied volatility (IV) fields. By default, require_greeks=false. 
                       Set require_greeks=true to enable greeks & IVs in the API response.
        contract: The US options contract ID you would like to specify. By default, the contract parameter
                 is not set and the entire option chain for a given symbol will be returned.
        expiration: The expiration date in YYYY-MM-DD format. The expiration date must be on or after today's date.
                    If not set, the API will return contracts for all expiration dates.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications: 
                 json returns the options data in JSON format; csv returns the data as a CSV (comma separated value) file.

    Returns:
        Realtime options data in JSON format or CSV string based on datatype parameter.
    """

    params = {
        "symbol": symbol,
        "datatype": datatype,
    }
    if require_greeks:
        params["require_greeks"] = "true"
    if contract:
        params["contract"] = contract
    if expiration:
        params["expiration"] = expiration

    return _make_api_request("REALTIME_OPTIONS", params)


@tool
def realtime_options_fmv(
    symbol: str,
    require_greeks: bool = False,
    contract: str = None,
    expiration: str = None,
    datatype: str = "csv"
) -> dict[str, str] | str:
    """Returns realtime FMV (fair market value) mark prices for US options.

    Option chains are sorted by expiration dates in chronological order.
    Within the same expiration date, contracts are sorted by strike prices from low to high.

    Args:
        symbol: The name of the equity of your choice. For example: symbol=IBM
        require_greeks: Enable greeks & implied volatility (IV) fields alongside the FMV mark.
                       By default, require_greeks=false. Set require_greeks=true to enable
                       greeks & IVs in the API response.
        contract: The US options contract ID you would like to specify. By default, the contract parameter
                 is not set and the entire option chain for a given symbol will be returned.
        expiration: The expiration date in YYYY-MM-DD format. The expiration date must be on or after today's date.
                    If not set, the API will return contracts for all expiration dates.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                 json returns the options data in JSON format; csv returns the data as a CSV (comma separated value) file.

    Returns:
        Realtime options FMV data in JSON format or CSV string based on datatype parameter.
    """

    params = {
        "symbol": symbol,
        "datatype": datatype,
    }
    if require_greeks:
        params["require_greeks"] = "true"
    if contract:
        params["contract"] = contract
    if expiration:
        params["expiration"] = expiration

    return _make_api_request("REALTIME_OPTIONS_FMV", params)


@tool
def realtime_put_call_ratio(
    symbol: str,
) -> dict:
    """Returns the realtime put-call ratio for US-traded equities and ETFs.

    The put-call ratio is calculated for the entire option chain as well as for each specific expiration date.
    A put-call ratio equal to or less than 0.6 typically signals a bullish market sentiment,
    while a ratio equal to or greater than 1.0 signals a bearish sentiment.

    Args:
        symbol: The name of the equity of your choice. For example: symbol=IBM

    Returns:
        Realtime put-call ratio data in JSON format.
    """

    params = {
        "symbol": symbol,
    }

    return _make_api_request("REALTIME_PUT_CALL_RATIO", params)


@tool
def realtime_volume_open_interest_ratio(
    symbol: str,
) -> dict:
    """Returns the realtime volume-to-open-interest ratio within an option chain.

    A high ratio (volume much larger than open interest) often suggests heavy trading activity
    relative to existing positions, which can indicate short-term speculation, increased liquidity,
    or possible trend changes. A low ratio (volume small compared to open interest) implies that
    most positions are being held rather than actively traded, signaling more stable or less
    volatile conditions.

    Args:
        symbol: The name of the equity of your choice. For example: symbol=NVDA

    Returns:
        Realtime volume-to-open-interest ratio data in JSON format.
    """

    params = {
        "symbol": symbol,
    }

    return _make_api_request("REALTIME_VOLUME_OPEN_INTEREST_RATIO", params)


@tool
def historical_options(
    symbol: str,
    date: str = None,
    contract: str = None,
    datatype: str = "csv"
) -> dict[str, str] | str:
    """Returns the full historical options chain for a specific symbol on a specific date.

    Covers 15+ years of history. Implied volatility (IV) and common Greeks (e.g., delta, gamma, theta, vega, rho)
    are also returned. Option chains are sorted by expiration dates in chronological order.
    Within the same expiration date, contracts are sorted by strike prices from low to high.

    Args:
        symbol: The name of the equity of your choice. For example: symbol=IBM
        date: By default, the date parameter is not set and the API will return data for the previous trading session.
              Any date later than 2008-01-01 is accepted. For example, date=2017-11-15.
        contract: The US options contract ID you would like to specify. By default, the contract parameter
                 is not set and the entire option chain for a given symbol will be returned.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                  json returns the options data in JSON format; csv returns the data as a CSV (comma separated value) file.

    Returns:
        Historical options data in JSON format or CSV string based on datatype parameter.
    """

    params = {
        "symbol": symbol,
        "datatype": datatype,
    }
    if date:
        params["date"] = date
    if contract:
        params["contract"] = contract

    return _make_api_request("HISTORICAL_OPTIONS", params)


@tool
def historical_put_call_ratio(
    symbol: str,
    date: str = None,
) -> dict:
    """Returns the historical put-call ratio for US-traded equities and ETFs.

    The put-call ratio is calculated for the entire option chain as well as for each specific expiration date.
    Covers data from 2008-01-01 to the previous trading session.

    Args:
        symbol: The name of the equity of your choice. For example: symbol=IBM
        date: The date in YYYY-MM-DD format. Any date later than 2008-01-01 is accepted.
              By default, the API will return data for the previous trading session.

    Returns:
        Historical put-call ratio data in JSON format.
    """

    params = {
        "symbol": symbol,
    }
    if date:
        params["date"] = date

    return _make_api_request("HISTORICAL_PUT_CALL_RATIO", params)


@tool
def historical_volume_open_interest_ratio(
    symbol: str,
    date: str = None,
) -> dict:
    """Returns the historical volume-to-open-interest ratio within an option chain.

    A high ratio (volume much larger than open interest) often suggests heavy trading activity
    relative to existing positions, which can indicate short-term speculation, increased liquidity,
    or possible trend changes. A low ratio (volume small compared to open interest) implies that
    most positions are being held rather than actively traded, signaling more stable or less
    volatile conditions.

    Args:
        symbol: The name of the equity of your choice. For example: symbol=NVDA
        date: The date in YYYY-MM-DD format. Any date later than 2008-01-01 is accepted.
              By default, the API will return data for the previous trading session.

    Returns:
        Historical volume-to-open-interest ratio data in JSON format.
    """

    params = {
        "symbol": symbol,
    }
    if date:
        params["date"] = date

    return _make_api_request("HISTORICAL_VOLUME_OPEN_INTEREST_RATIO", params)

