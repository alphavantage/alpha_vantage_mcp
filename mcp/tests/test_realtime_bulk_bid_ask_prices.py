"""Coverage for the REALTIME_BULK_BID_ASK_PRICES MCP tool."""

from unittest.mock import patch

from av_api.registry import get_tool_schema
from av_api.tools.core_stock_apis import realtime_bulk_bid_ask_prices
from av_mcp.decorators import setup_custom_tool_decorator
from av_mcp.stdio_server import build_tools
from av_mcp.tools.registry import register_all_tools


class _FakeMCP:
    def __init__(self):
        self.tools = {}
        self.tool_implementations = {}


def test_realtime_bulk_bid_ask_prices_is_exposed_over_both_transports():
    stdio_tools = {tool.name: tool for tool in build_tools()}

    mcp = _FakeMCP()
    setup_custom_tool_decorator(mcp)
    register_all_tools(mcp)

    assert "REALTIME_BULK_BID_ASK_PRICES" in stdio_tools
    assert "REALTIME_BULK_BID_ASK_PRICES" in mcp.tools


def test_realtime_bulk_bid_ask_prices_schema_documents_cap_and_datatype_default():
    schema = get_tool_schema("REALTIME_BULK_BID_ASK_PRICES")

    assert (
        "only the first 100 symbols"
        in schema["parameters"]["properties"]["symbol"]["description"]
    )
    assert (
        "By default, datatype=json"
        in schema["parameters"]["properties"]["datatype"]["description"]
    )


@patch("av_api.tools.core_stock_apis._make_api_request")
def test_realtime_bulk_bid_ask_prices_passes_more_than_100_symbols_through(
    make_api_request,
):
    symbols = ",".join(f"SYM{index}" for index in range(101))

    realtime_bulk_bid_ask_prices(symbols)

    make_api_request.assert_called_once_with(
        "REALTIME_BULK_BID_ASK_PRICES",
        {"symbol": symbols, "datatype": "json"},
    )


@patch("av_api.tools.core_stock_apis._make_api_request")
def test_realtime_bulk_bid_ask_prices_calls_expected_endpoint(make_api_request):
    make_api_request.return_value = {"data": []}

    result = realtime_bulk_bid_ask_prices("MSFT,AAPL,IBM")

    assert result == {"data": []}
    make_api_request.assert_called_once_with(
        "REALTIME_BULK_BID_ASK_PRICES",
        {"symbol": "MSFT,AAPL,IBM", "datatype": "json"},
    )
