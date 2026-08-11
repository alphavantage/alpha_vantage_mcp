"""Create deterministic Microsoft 365 Copilot Cowork connector app packages."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from av_mcp.cowork_connector.export_tools import write_tool_descriptions


MANIFEST_SCHEMA = "https://developer.microsoft.com/json-schemas/teams/v1.28/MicrosoftTeams.schema.json"
# Long-term official production endpoint; remains the default for submission packages.
DEFAULT_MCP_SERVER_URL = "https://mcp.alphavantage.co/mcp"
PACKAGE_FILES = (
    "manifest.json",
    "color.png",
    "outline.png",
    "tools/alpha-vantage-tools.json",
)
PLACEHOLDER_APP_ID = "00000000-0000-4000-8000-000000000000"


def resolve_mcp_server_url(cli_url: str | None = None) -> str:
    """Resolve the packaged MCP URL.

    Precedence: ``--mcp-server-url`` > ``DOMAIN_NAME`` env
    (``https://<DOMAIN_NAME>/mcp``, same convention as oauth ``resolve_base_url``) >
    ``DEFAULT_MCP_SERVER_URL`` (``https://mcp.alphavantage.co/mcp``).
    """
    if cli_url:
        if "://" not in cli_url:
            raise SystemExit(
                f"--mcp-server-url must include a scheme (got {cli_url!r}); "
                f"example: {DEFAULT_MCP_SERVER_URL}"
            )
        return cli_url
    domain_name = os.environ.get("DOMAIN_NAME")
    if domain_name:
        return f"https://{domain_name}/mcp"
    return DEFAULT_MCP_SERVER_URL


@dataclass(frozen=True)
class PackageConfig:
    app_id: str
    version: str
    terms_url: str
    color_icon: Path
    outline_icon: Path
    mcp_server_url: str = DEFAULT_MCP_SERVER_URL
    development: bool = False


def _manifest(config: PackageConfig) -> dict[str, Any]:
    # Cowork-managed DCR: omit authorization entirely so Microsoft registers its own client
    # against the server's advertised registration_endpoint.
    return {
        "$schema": MANIFEST_SCHEMA,
        "manifestVersion": "1.28",
        "version": config.version,
        "id": config.app_id,
        "developer": {
            "name": "Alpha Vantage",
            "websiteUrl": "https://www.alphavantage.co/",
            "privacyUrl": "https://www.alphavantage.co/privacy/",
            "termsOfUseUrl": config.terms_url,
        },
        "name": {
            "short": "Alpha Vantage",
            "full": "Alpha Vantage Financial Market Data",
        },
        "description": {
            "short": "Financial market data from Alpha Vantage.",
            "full": (
                "Access Alpha Vantage financial market data for equities, forex, "
                "digital currencies, commodities, economic indicators, and technical analysis."
            ),
        },
        "icons": {"color": "color.png", "outline": "outline.png"},
        "accentColor": "#1A1F71",
        "agentConnectors": [
            {
                "id": "alpha-vantage-mcp",
                "displayName": "Alpha Vantage MCP",
                "description": "Provides Alpha Vantage financial market data tools.",
                "toolSource": {
                    "remoteMcpServer": {
                        "mcpServerUrl": config.mcp_server_url,
                        "mcpToolDescription": {
                            "file": "tools/alpha-vantage-tools.json"
                        },
                    }
                },
            }
        ],
    }


def _write_package_contents(directory: Path, config: PackageConfig) -> None:
    (directory / "manifest.json").write_text(
        json.dumps(_manifest(config), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    shutil.copyfile(config.color_icon, directory / "color.png")
    shutil.copyfile(config.outline_icon, directory / "outline.png")
    write_tool_descriptions(directory / "tools" / "alpha-vantage-tools.json")


def _write_zip(directory: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in PACKAGE_FILES:
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (directory / name).read_bytes())


def build_package(output: Path, config: PackageConfig) -> None:
    """Generate a reproducible connector-only app ZIP at ``output``."""
    with tempfile.TemporaryDirectory() as temporary_directory:
        directory = Path(temporary_directory)
        _write_package_contents(directory, config)
        _write_zip(directory, output)


def _config_from_args(args: argparse.Namespace) -> PackageConfig:
    if args.development:
        app_id = args.app_id or PLACEHOLDER_APP_ID
    else:
        if not args.app_id:
            raise SystemExit("--app-id is required outside --development")
        app_id = args.app_id

    return PackageConfig(
        app_id=app_id,
        version=args.version,
        terms_url=args.terms_url,
        color_icon=Path(args.color_icon),
        outline_icon=Path(args.outline_icon),
        mcp_server_url=resolve_mcp_server_url(args.mcp_server_url),
        development=args.development,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Cowork connector app package")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--app-id")
    parser.add_argument("--version", default="1.0.0")
    parser.add_argument("--terms-url", default="https://www.alphavantage.co/terms/")
    parser.add_argument("--color-icon", type=Path, required=True)
    parser.add_argument("--outline-icon", type=Path, required=True)
    parser.add_argument(
        "--mcp-server-url",
        help=(
            "MCP server URL to embed in the manifest. Overrides DOMAIN_NAME and the "
            f"default ({DEFAULT_MCP_SERVER_URL}). For testing/transition only; "
            "submission packages should keep the official .co default."
        ),
    )
    parser.add_argument("--development", action="store_true")
    args = parser.parse_args()
    build_package(args.output, _config_from_args(args))


if __name__ == "__main__":
    main()
