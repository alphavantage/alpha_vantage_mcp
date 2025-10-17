from src.common import _make_api_request
from src.tools.registry import tool


@tool
def company_overview(symbol: str) -> dict[str, str] | str:
    """Returns company information, financial ratios, and key metrics for the specified equity.

    Data is generally refreshed on the same day a company reports its latest earnings and financials.

    Args:
        symbol: The symbol of the ticker of your choice. For example: symbol=IBM.

    Returns:
        Company overview data in JSON format or error message.
    """

    params = {
        "symbol": symbol,
    }

    return _make_api_request("OVERVIEW", params)


@tool
def etf_profile(symbol: str) -> dict[str, str] | str:
    """Returns key ETF metrics and holdings with allocation by asset types and sectors.

    Includes net assets, expense ratio, turnover, and corresponding ETF holdings/constituents.

    Args:
        symbol: The symbol of the ticker of your choice. For example: symbol=QQQ.

    Returns:
        ETF profile data in JSON format or error message.
    """

    params = {
        "symbol": symbol,
    }

    return _make_api_request("ETF_PROFILE", params)


@tool
def dividends(symbol: str, datatype: str = "csv") -> dict[str, str] | str:
    """Returns historical and future (declared) dividend distributions.

    Args:
        symbol: The symbol of the ticker of your choice. For example: symbol=IBM.
        datatype: By default, datatype=csv. Strings json and csv are accepted.
                 json returns the data in JSON format; csv returns as CSV file.

    Returns:
        Dividend data in specified format or error message.
    """

    params = {
        "symbol": symbol,
        "datatype": datatype,
    }

    return _make_api_request("DIVIDENDS", params)


@tool
def splits(symbol: str, datatype: str = "csv") -> dict[str, str] | str:
    """Returns historical split events.

    Args:
        symbol: The symbol of the ticker of your choice. For example: symbol=IBM.
        datatype: By default, datatype=csv. Strings json and csv are accepted.
                 json returns the data in JSON format; csv returns as CSV file.

    Returns:
        Split data in specified format or error message.
    """

    params = {
        "symbol": symbol,
        "datatype": datatype,
    }

    return _make_api_request("SPLITS", params)


@tool
def income_statement(symbol: str) -> dict[str, str] | str:
    """Returns annual and quarterly income statements with normalized fields.

    Fields are mapped to GAAP and IFRS taxonomies of the SEC. Data is generally refreshed
    on the same day a company reports its latest earnings and financials.

    Args:
        symbol: The symbol of the ticker of your choice. For example: symbol=IBM.

    Returns:
        Income statement data in JSON format or error message.
    """

    params = {
        "symbol": symbol,
    }

    return _make_api_request("INCOME_STATEMENT", params)


@tool
def balance_sheet(symbol: str) -> dict[str, str] | str:
    """Returns annual and quarterly balance sheets with normalized fields.

    Fields are mapped to GAAP and IFRS taxonomies of the SEC. Data is generally refreshed
    on the same day a company reports its latest earnings and financials.

    Args:
        symbol: The symbol of the ticker of your choice. For example: symbol=IBM.

    Returns:
        Balance sheet data in JSON format or error message.
    """

    params = {
        "symbol": symbol,
    }

    return _make_api_request("BALANCE_SHEET", params)


@tool
def cash_flow(symbol: str) -> dict[str, str] | str:
    """Returns annual and quarterly cash flow with normalized fields.

    Fields are mapped to GAAP and IFRS taxonomies of the SEC. Data is generally refreshed
    on the same day a company reports its latest earnings and financials.

    Args:
        symbol: The symbol of the ticker of your choice. For example: symbol=IBM.

    Returns:
        Cash flow data in JSON format or error message.
    """

    params = {
        "symbol": symbol,
    }

    return _make_api_request("CASH_FLOW", params)


@tool
def earnings(symbol: str) -> dict[str, str] | str:
    """Returns annual and quarterly earnings (EPS) for the company.

    Quarterly data also includes analyst estimates and surprise metrics.

    Args:
        symbol: The symbol of the ticker of your choice. For example: symbol=IBM.

    Returns:
        Earnings data in JSON format or error message.
    """

    params = {
        "symbol": symbol,
    }

    return _make_api_request("EARNINGS", params)


@tool
def earnings_estimates(symbol: str) -> dict[str, str] | str:
    """Returns annual and quarterly EPS and revenue estimates with analyst data.

    Includes analyst count and revision history.

    Args:
        symbol: The symbol of the ticker of your choice. For example: symbol=IBM.

    Returns:
        Earnings estimates data in JSON format or error message.
    """

    params = {
        "symbol": symbol,
    }

    return _make_api_request("EARNINGS_ESTIMATES", params)


@tool
def listing_status(date: str = None, state: str = "active") -> dict[str, str] | str:
    """Returns a list of active or delisted US stocks and ETFs.

    Can return data as of the latest trading day or at a specific time in history.
    Facilitates equity research on asset lifecycle and survivorship.

    Args:
        date: If no date is set, returns symbols as of the latest trading day.
             If set, "travels back" to return symbols on that date in history.
             Any YYYY-MM-DD date later than 2010-01-01 is supported. For example: date=2013-08-03
        state: By default, state=active returns actively traded stocks and ETFs.
              Set state=delisted to query delisted assets.

    Returns:
        Listing status data in CSV format or error message.
    """

    params = {
        "state": state,
    }
    if date:
        params["date"] = date

    return _make_api_request("LISTING_STATUS", params)


@tool
def earnings_calendar(symbol: str = None, horizon: str = "3month") -> dict[str, str] | str:
    """Returns a list of company earnings expected in the next 3, 6, or 12 months.

    Args:
        symbol: By default, no symbol is set and returns full list of scheduled earnings.
               If set, returns expected earnings for that specific symbol. For example: symbol=IBM
        horizon: By default, horizon=3month returns earnings in the next 3 months.
                Set horizon=6month or horizon=12month for 6 or 12 months respectively.

    Returns:
        Earnings calendar data in CSV format or error message.
    """

    params = {
        "horizon": horizon,
    }
    if symbol:
        params["symbol"] = symbol

    return _make_api_request("EARNINGS_CALENDAR", params)


@tool
def ipo_calendar() -> dict[str, str] | str:
    """Returns a list of IPOs expected in the next 3 months.

    Returns:
        IPO calendar data in CSV format or error message.
    """

    params = {}

    return _make_api_request("IPO_CALENDAR", params)
