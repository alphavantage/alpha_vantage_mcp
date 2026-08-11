"""Validate Microsoft 365 Copilot Cowork connector app packages."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import urllib.request
import uuid
import zipfile
from pathlib import Path
from typing import Any

import jsonschema

from av_mcp.cowork_connector.export_tools import TOOL_FIELDS
from av_mcp.cowork_connector.package import (
    MANIFEST_SCHEMA,
    MCP_SERVER_URL,
    PACKAGE_FILES,
    PLACEHOLDER_APP_ID,
)


class PackageValidationError(ValueError):
    """Raised when a Cowork connector package fails local validation."""


DEVELOPMENT_ICON_DIGESTS = {
    "color.png": "5ea01bb43018c95f62d25ee72eb9a681cef9eebc82d10a9e08fcbb596a9c43bd",
    "outline.png": "245a82e115217ea58a29329710f13d48617347f30d71db98f8c7657ad7b696d5",
}


def _png_properties(data: bytes) -> tuple[int, int, int, int]:
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise PackageValidationError("icon is not a PNG")
    width, height, bit_depth, color_type = struct.unpack(">IIBB", data[16:26])
    return width, height, bit_depth, color_type


def _load_schema(schema_location: str | Path) -> dict[str, Any]:
    location = str(schema_location)
    if location.startswith(("https://", "http://")):
        with urllib.request.urlopen(location, timeout=30) as response:
            return json.load(response)
    return json.loads(Path(location).read_text(encoding="utf-8"))


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PackageValidationError(message)


def validate_package(
    package: Path,
    *,
    development: bool = False,
    schema_location: str | Path = MANIFEST_SCHEMA,
) -> None:
    """Validate a generated Cowork connector ZIP and all companion files."""
    with zipfile.ZipFile(package) as archive:
        names = archive.namelist()
        _require(
            names == list(PACKAGE_FILES), "ZIP must contain only the expected files"
        )
        _require(
            all(
                not name.startswith("/") and ".." not in Path(name).parts
                for name in names
            ),
            "ZIP entries must be package-relative",
        )
        manifest = json.loads(archive.read("manifest.json"))
        tools = json.loads(archive.read("tools/alpha-vantage-tools.json"))
        color_icon = archive.read("color.png")
        outline_icon = archive.read("outline.png")

    try:
        jsonschema.Draft4Validator(_load_schema(schema_location)).validate(manifest)
    except jsonschema.ValidationError as error:
        raise PackageValidationError(
            f"manifest schema validation failed: {error.message}"
        ) from error

    try:
        uuid.UUID(manifest["id"])
    except (KeyError, ValueError, AttributeError) as error:
        raise PackageValidationError("manifest id must be a UUID") from error

    connectors = manifest.get("agentConnectors", [])
    _require(len(connectors) == 1, "manifest must contain exactly one agent connector")
    connector = connectors[0]
    remote_server = connector.get("toolSource", {}).get("remoteMcpServer", {})
    _require(
        remote_server.get("mcpServerUrl") == MCP_SERVER_URL,
        "MCP URL must be the production HTTPS URL",
    )
    _require(
        remote_server.get("mcpToolDescription", {}).get("file")
        == "tools/alpha-vantage-tools.json",
        "manifest must reference the packaged tool description",
    )
    # Cowork-managed DCR: authorization must be absent so Microsoft provisions the client.
    _require(
        "authorization" not in remote_server,
        "manifest must omit remoteMcpServer.authorization for Cowork-managed DCR",
    )
    _require(
        manifest["icons"] == {"color": "color.png", "outline": "outline.png"},
        "manifest icon references must match packaged icons",
    )

    if not development:
        _require(
            manifest["id"] != PLACEHOLDER_APP_ID,
            "placeholder app ID is only allowed in development",
        )
        for name, icon in (("color.png", color_icon), ("outline.png", outline_icon)):
            _require(
                hashlib.sha256(icon).hexdigest() != DEVELOPMENT_ICON_DIGESTS[name],
                f"development placeholder {name} is only allowed in development",
            )

    _require(
        isinstance(tools, list) and tools,
        "tool description must be a non-empty JSON array",
    )
    for tool in tools:
        _require(
            isinstance(tool, dict)
            and all(tool.get(field) is not None for field in TOOL_FIELDS),
            "every tool must contain name, description, inputSchema, and annotations",
        )
        _require(
            isinstance(tool["name"], str) and tool["name"],
            "every tool name must be a non-empty string",
        )
        _require(
            isinstance(tool["description"], str),
            "every tool description must be a string",
        )
        _require(
            isinstance(tool["inputSchema"], dict),
            "every tool inputSchema must be an object",
        )
        _require(
            isinstance(tool["annotations"], dict),
            "every tool annotations value must be an object",
        )

    _require(
        re.fullmatch(
            r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?",
            manifest["version"],
        )
        is not None,
        "manifest version must use semantic versioning",
    )

    color_width, color_height, color_depth, color_type = _png_properties(color_icon)
    _require((color_width, color_height) == (192, 192), "color icon must be 192x192")
    _require(
        color_depth == 8 and color_type in (2, 6),
        "color icon must be an 8-bit RGB or RGBA PNG",
    )
    outline_width, outline_height, outline_depth, outline_type = _png_properties(
        outline_icon
    )
    _require((outline_width, outline_height) == (32, 32), "outline icon must be 32x32")
    _require(
        outline_depth == 8 and outline_type == 6,
        "outline icon must be an 8-bit RGBA PNG",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate a Cowork connector app package"
    )
    parser.add_argument("package", type=Path)
    parser.add_argument("--development", action="store_true")
    parser.add_argument("--schema", default=MANIFEST_SCHEMA)
    args = parser.parse_args()
    try:
        validate_package(
            args.package, development=args.development, schema_location=args.schema
        )
    except (
        OSError,
        json.JSONDecodeError,
        zipfile.BadZipFile,
        PackageValidationError,
    ) as error:
        raise SystemExit(f"package validation failed: {error}") from error


if __name__ == "__main__":
    main()
