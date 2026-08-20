from av_api.client import _make_api_request
from av_api.registry import tool


@tool
def congress_trades(
    symbol: str = None, bioguide_id: str = None, datatype: str = "json"
) -> dict[str, str] | str:
    """Returns the latest and historical stock trades disclosed by US congressional representatives.

    Args:
        symbol: Stock ticker symbol to filter trades. Example: "AAPL". Required unless the politician's BioGuide ID is given.
        bioguide_id: BioGuide ID of the politician to filter trades. Example: "S000510". Use POLITICIAN_METADATA for the complete mapping. Required unless a stock symbol is given.
        datatype: By default, json. Strings json and csv are accepted.

    Returns:
        Congressional stock trade records matching the given symbol and/or bioguide_id.
    """
    symbol = (symbol or "").strip()
    bioguide_id = (bioguide_id or "").strip()
    if not symbol and not bioguide_id:
        raise ValueError("At least one of symbol or bioguide_id is required.")

    normalized_datatype = (datatype or "").strip().lower()
    if normalized_datatype not in ("json", "csv"):
        raise ValueError("datatype must be 'json' or 'csv'.")

    params = {"datatype": normalized_datatype}
    if symbol:
        params["symbol"] = symbol
    if bioguide_id:
        params["bioguide_id"] = bioguide_id

    return _make_api_request("CONGRESS_TRADES", params)


@tool
def politician_metadata() -> dict[str, str] | str:
    """Returns key metadata for US congressional representatives, such as bioguide_id, district, and time in service.

    Args:
        None.

    Returns:
        Complete roster of congressional representatives with their metadata.
    """

    params = {}

    return _make_api_request("POLITICIAN_METADATA", params)
