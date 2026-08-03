"""Coverage for the COMPANY_LOGO MCP tool."""

from unittest.mock import patch

from av_api.registry import get_tool_schema
from av_api.tools.fundamental_data import company_logo
from av_mcp.decorators import setup_custom_tool_decorator
from av_mcp.stdio_server import build_tools
from av_mcp.tools.registry import register_all_tools


class _FakeMCP:
    def __init__(self):
        self.tools = {}
        self.tool_implementations = {}


def test_company_logo_is_exposed_over_both_transports():
    stdio_tools = {tool.name: tool for tool in build_tools()}

    mcp = _FakeMCP()
    setup_custom_tool_decorator(mcp)
    register_all_tools(mcp)

    assert "COMPANY_LOGO" in stdio_tools
    assert "COMPANY_LOGO" in mcp.tools


def test_company_logo_schema_requires_symbol_and_documents_example():
    schema = get_tool_schema("COMPANY_LOGO")

    assert schema["parameters"]["required"] == ["symbol"]
    assert (
        "symbol=IBM" in schema["parameters"]["properties"]["symbol"]["description"]
    )


@patch("av_api.tools.fundamental_data._make_api_request")
def test_company_logo_calls_expected_endpoint(make_api_request):
    make_api_request.return_value = {
        "symbol": "IBM",
        "logo_url_png": "https://cdn.alphavantage.co/logos/IBM.png",
        "logo_url_svg": "https://cdn.alphavantage.co/logos/IBM.svg",
    }

    result = company_logo("IBM")

    assert result == make_api_request.return_value
    make_api_request.assert_called_once_with("COMPANY_LOGO", {"symbol": "IBM"})


@patch("av_api.tools.fundamental_data._make_api_request")
def test_company_logo_forwards_symbol_verbatim_without_normalization(
    make_api_request,
):
    company_logo("ibm")

    make_api_request.assert_called_once_with("COMPANY_LOGO", {"symbol": "ibm"})
