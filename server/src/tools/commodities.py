from src.common import _make_api_request
from src.tools.registry import tool


@tool
def wti(interval: str = "monthly", datatype: str = "csv") -> dict[str, str] | str:
    """
    This API returns the West Texas Intermediate (WTI) crude oil prices in daily, weekly, and monthly horizons.

    Args:
        interval: By default, monthly. Strings daily, weekly, and monthly are accepted.
        datatype: By default, csv. Strings json and csv are accepted with the following specifications:
                 json returns the time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        WTI crude oil price data in the specified format.
    """

    params = {
        "interval": interval,
        "datatype": datatype,
    }

    return _make_api_request("WTI", params)


@tool
def brent(interval: str = "monthly", datatype: str = "csv") -> dict[str, str] | str:
    """
    This API returns the Brent (Europe) crude oil prices in daily, weekly, and monthly horizons.

    Args:
        interval: By default, monthly. Strings daily, weekly, and monthly are accepted.
        datatype: By default, csv. Strings json and csv are accepted with the following specifications:
                 json returns the time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        Brent crude oil price data in the specified format.
    """

    params = {
        "interval": interval,
        "datatype": datatype,
    }

    return _make_api_request("BRENT", params)


@tool
def natural_gas(interval: str = "monthly", datatype: str = "csv") -> dict[str, str] | str:
    """
    This API returns the Henry Hub natural gas spot prices in daily, weekly, and monthly horizons.

    Args:
        interval: By default, monthly. Strings daily, weekly, and monthly are accepted.
        datatype: By default, csv. Strings json and csv are accepted with the following specifications:
                 json returns the time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        Natural gas price data in the specified format.
    """

    params = {
        "interval": interval,
        "datatype": datatype,
    }

    return _make_api_request("NATURAL_GAS", params)


@tool
def copper(interval: str = "monthly", datatype: str = "csv") -> dict[str, str] | str:
    """
    This API returns the global price of copper in monthly, quarterly, and annual horizons.

    Args:
        interval: By default, monthly. Strings monthly, quarterly, and annual are accepted.
        datatype: By default, csv. Strings json and csv are accepted with the following specifications:
                 json returns the time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        Copper price data in the specified format.
    """

    params = {
        "interval": interval,
        "datatype": datatype,
    }

    return _make_api_request("COPPER", params)


@tool
def aluminum(interval: str = "monthly", datatype: str = "csv") -> dict[str, str] | str:
    """
    This API returns the global price of aluminum in monthly, quarterly, and annual horizons.

    Args:
        interval: By default, monthly. Strings monthly, quarterly, and annual are accepted.
        datatype: By default, csv. Strings json and csv are accepted with the following specifications:
                 json returns the time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        Aluminum price data in the specified format.
    """

    params = {
        "interval": interval,
        "datatype": datatype,
    }

    return _make_api_request("ALUMINUM", params)


@tool
def wheat(interval: str = "monthly", datatype: str = "csv") -> dict[str, str] | str:
    """
    This API returns the global price of wheat in monthly, quarterly, and annual horizons.

    Args:
        interval: By default, monthly. Strings monthly, quarterly, and annual are accepted.
        datatype: By default, csv. Strings json and csv are accepted with the following specifications:
                 json returns the time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        Wheat price data in the specified format.
    """

    params = {
        "interval": interval,
        "datatype": datatype,
    }

    return _make_api_request("WHEAT", params)


@tool
def corn(interval: str = "monthly", datatype: str = "csv") -> dict[str, str] | str:
    """
    This API returns the global price of corn in monthly, quarterly, and annual horizons.

    Args:
        interval: By default, monthly. Strings monthly, quarterly, and annual are accepted.
        datatype: By default, csv. Strings json and csv are accepted with the following specifications:
                 json returns the time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        Corn price data in the specified format.
    """

    params = {
        "interval": interval,
        "datatype": datatype,
    }

    return _make_api_request("CORN", params)


@tool
def cotton(interval: str = "monthly", datatype: str = "csv") -> dict[str, str] | str:
    """
    This API returns the global price of cotton in monthly, quarterly, and annual horizons.

    Args:
        interval: By default, monthly. Strings monthly, quarterly, and annual are accepted.
        datatype: By default, csv. Strings json and csv are accepted with the following specifications:
                 json returns the time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        Cotton price data in the specified format.
    """

    params = {
        "interval": interval,
        "datatype": datatype,
    }

    return _make_api_request("COTTON", params)


@tool
def sugar(interval: str = "monthly", datatype: str = "csv") -> dict[str, str] | str:
    """
    This API returns the global price of sugar in monthly, quarterly, and annual horizons.

    Args:
        interval: By default, monthly. Strings monthly, quarterly, and annual are accepted.
        datatype: By default, csv. Strings json and csv are accepted with the following specifications:
                 json returns the time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        Sugar price data in the specified format.
    """

    params = {
        "interval": interval,
        "datatype": datatype,
    }

    return _make_api_request("SUGAR", params)


@tool
def coffee(interval: str = "monthly", datatype: str = "csv") -> dict[str, str] | str:
    """
    This API returns the global price of coffee in monthly, quarterly, and annual horizons.

    Args:
        interval: By default, monthly. Strings monthly, quarterly, and annual are accepted.
        datatype: By default, csv. Strings json and csv are accepted with the following specifications:
                 json returns the time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        Coffee price data in the specified format.
    """

    params = {
        "interval": interval,
        "datatype": datatype,
    }

    return _make_api_request("COFFEE", params)


@tool
def all_commodities(interval: str = "monthly", datatype: str = "csv") -> dict[str, str] | str:
    """
    This API returns the global price index of all commodities in monthly, quarterly, and annual temporal dimensions.

    Args:
        interval: By default, monthly. Strings monthly, quarterly, and annual are accepted.
        datatype: By default, csv. Strings json and csv are accepted with the following specifications:
                 json returns the time series in JSON format; csv returns the time series as a CSV (comma separated value) file.

    Returns:
        All commodities price index data in the specified format.
    """

    params = {
        "interval": interval,
        "datatype": datatype,
    }

    return _make_api_request("ALL_COMMODITIES", params)
