from src.common import _make_api_request
from src.tools.registry import tool


@tool
def real_gdp(interval: str = "annual", datatype: str = "csv") -> dict[str, str] | str:
    """
    This API returns the annual and quarterly Real GDP of the United States.

    Args:
        interval: By default, interval=annual. Strings quarterly and annual are accepted.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                  json returns the time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        Real GDP time series data in JSON format or CSV string.
    """

    params = {
        "interval": interval,
        "datatype": datatype,
    }

    return _make_api_request("REAL_GDP", params)


@tool
def real_gdp_per_capita(datatype: str = "csv") -> dict[str, str] | str:
    """
    This API returns the quarterly Real GDP per Capita data of the United States.

    Args:
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                  json returns the time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        Real GDP per capita time series data in JSON format or CSV string.
    """

    params = {
        "datatype": datatype,
    }

    return _make_api_request("REAL_GDP_PER_CAPITA", params)


@tool
def treasury_yield(
    interval: str = "monthly", maturity: str = "10year", datatype: str = "csv"
) -> dict[str, str] | str:
    """
    This API returns the daily, weekly, and monthly US treasury yield of a given maturity timeline (e.g., 5 year, 30 year, etc).

    Args:
        interval: By default, interval=monthly. Strings daily, weekly, and monthly are accepted.
        maturity: By default, maturity=10year. Strings 3month, 2year, 5year, 7year, 10year, and 30year are accepted.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                  json returns the time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        Treasury yield time series data in JSON format or CSV string.
    """

    params = {
        "interval": interval,
        "maturity": maturity,
        "datatype": datatype,
    }

    return _make_api_request("TREASURY_YIELD", params)


@tool
def federal_funds_rate(interval: str = "monthly", datatype: str = "csv") -> dict[str, str] | str:
    """
    This API returns the daily, weekly, and monthly federal funds rate (interest rate) of the United States.

    Args:
        interval: By default, interval=monthly. Strings daily, weekly, and monthly are accepted.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                  json returns the time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        Federal funds rate time series data in JSON format or CSV string.
    """

    params = {
        "interval": interval,
        "datatype": datatype,
    }

    return _make_api_request("FEDERAL_FUNDS_RATE", params)


@tool
def cpi(interval: str = "monthly", datatype: str = "csv") -> dict[str, str] | str:
    """
    This API returns the monthly and semiannual consumer price index (CPI) of the United States.
    CPI is widely regarded as the barometer of inflation levels in the broader economy.

    Args:
        interval: By default, interval=monthly. Strings monthly and semiannual are accepted.
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                  json returns the time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        CPI time series data in JSON format or CSV string.
    """

    params = {
        "interval": interval,
        "datatype": datatype,
    }

    return _make_api_request("CPI", params)


@tool
def inflation(datatype: str = "csv") -> dict[str, str] | str:
    """
    This API returns the annual inflation rates (consumer prices) of the United States.

    Args:
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                  json returns the time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        Inflation rate time series data in JSON format or CSV string.
    """

    params = {
        "datatype": datatype,
    }

    return _make_api_request("INFLATION", params)


@tool
def retail_sales(datatype: str = "csv") -> dict[str, str] | str:
    """
    This API returns the monthly Advance Retail Sales: Retail Trade data of the United States.

    Args:
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                  json returns the time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        Retail sales time series data in JSON format or CSV string.
    """

    params = {
        "datatype": datatype,
    }

    return _make_api_request("RETAIL_SALES", params)


@tool
def durables(datatype: str = "csv") -> dict[str, str] | str:
    """
    This API returns the monthly manufacturers' new orders of durable goods in the United States.

    Args:
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                  json returns the time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        Durable goods orders time series data in JSON format or CSV string.
    """

    params = {
        "datatype": datatype,
    }

    return _make_api_request("DURABLES", params)


@tool
def unemployment(datatype: str = "csv") -> dict[str, str] | str:
    """
    This API returns the monthly unemployment data of the United States. The unemployment rate represents the number of
    unemployed as a percentage of the labor force. Labor force data are restricted to people 16 years of age and older,
    who currently reside in 1 of the 50 states or the District of Columbia, who do not reside in institutions
    (e.g., penal and mental facilities, homes for the aged), and who are not on active duty in the Armed Forces.

    Args:
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                  json returns the time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        Unemployment time series data in JSON format or CSV string.
    """

    params = {
        "datatype": datatype,
    }

    return _make_api_request("UNEMPLOYMENT", params)


@tool
def nonfarm_payroll(datatype: str = "csv") -> dict[str, str] | str:
    """
    This API returns the monthly US All Employees: Total Nonfarm (commonly known as Total Nonfarm Payroll),
    a measure of the number of U.S. workers in the economy that excludes proprietors, private household employees,
    unpaid volunteers, farm employees, and the unincorporated self-employed.

    Args:
        datatype: By default, datatype=csv. Strings json and csv are accepted with the following specifications:
                  json returns the time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        Nonfarm payroll time series data in JSON format or CSV string.
    """

    params = {
        "datatype": datatype,
    }

    return _make_api_request("NONFARM_PAYROLL", params)
