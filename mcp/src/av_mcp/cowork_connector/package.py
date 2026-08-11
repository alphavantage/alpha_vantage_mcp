"""Create deterministic Microsoft 365 Copilot Cowork connector app packages."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from av_mcp.cowork_connector.export_tools import write_tool_descriptions


MANIFEST_SCHEMA = "https://developer.microsoft.com/json-schemas/teams/v1.28/MicrosoftTeams.schema.json"
MCP_SERVER_URL = "https://mcp.alphavantage.co/mcp"
PACKAGE_FILES = (
    "manifest.json",
    "color.png",
    "outline.png",
    "tools/alpha-vantage-tools.json",
)
PLACEHOLDER_APP_ID = "00000000-0000-4000-8000-000000000000"
PLACEHOLDER_AUTH_CONFIG_ID = "DEVELOPMENT-AUTH-CONFIG-ID"


@dataclass(frozen=True)
class PackageConfig:
    app_id: str
    auth_config_id: str
    version: str
    terms_url: str
    color_icon: Path
    outline_icon: Path
    development: bool = False


def _manifest(config: PackageConfig) -> dict[str, Any]:
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
                        "mcpServerUrl": MCP_SERVER_URL,
                        "mcpToolDescription": {
                            "file": "tools/alpha-vantage-tools.json"
                        },
                        "authorization": {
                            "type": "OAuthPluginVault",
                            "referenceId": config.auth_config_id,
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
        auth_config_id = args.auth_config_id or PLACEHOLDER_AUTH_CONFIG_ID
    else:
        if not args.app_id or not args.auth_config_id:
            raise SystemExit(
                "--app-id and --auth-config-id are required outside --development"
            )
        app_id = args.app_id
        auth_config_id = args.auth_config_id

    return PackageConfig(
        app_id=app_id,
        auth_config_id=auth_config_id,
        version=args.version,
        terms_url=args.terms_url,
        color_icon=Path(args.color_icon),
        outline_icon=Path(args.outline_icon),
        development=args.development,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Cowork connector app package")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--app-id")
    parser.add_argument("--auth-config-id")
    parser.add_argument("--version", default="1.0.0")
    parser.add_argument("--terms-url", default="https://www.alphavantage.co/terms/")
    parser.add_argument("--color-icon", type=Path, required=True)
    parser.add_argument("--outline-icon", type=Path, required=True)
    parser.add_argument("--development", action="store_true")
    args = parser.parse_args()
    build_package(args.output, _config_from_args(args))


if __name__ == "__main__":
    main()
