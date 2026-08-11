"""Tests for the Microsoft 365 Copilot Cowork connector package."""

import json
import shutil
import zipfile
from pathlib import Path

import pytest

from av_mcp.stdio_server import META_TOOLS, build_tools
from av_mcp.cowork_connector.export_tools import TOOL_FIELDS, write_tool_descriptions
from av_mcp.cowork_connector.package import PACKAGE_FILES, PackageConfig, build_package
from av_mcp.cowork_connector.validate import PackageValidationError, validate_package


ROOT = Path(__file__).parents[1]
ASSETS = ROOT / "src" / "av_mcp" / "cowork_connector" / "assets"
SCHEMA = ROOT / "tests" / "fixtures" / "MicrosoftTeams.v1.28.schema.json"


@pytest.fixture
def config() -> PackageConfig:
    return PackageConfig(
        app_id="5e9e1313-2d69-4576-9d1b-3fa0737a0f95",
        auth_config_id="alpha-vantage-oauth-plugin-vault",
        version="1.0.0",
        terms_url="https://www.alphavantage.co/terms/",
        color_icon=ASSETS / "dev-color.png",
        outline_icon=ASSETS / "dev-outline.png",
    )


def test_exported_tools_match_deployed_catalog(tmp_path):
    tools = write_tool_descriptions(tmp_path / "tools.json")

    assert {tool["name"] for tool in tools} == {
        tool.name for tool in build_tools() + META_TOOLS
    }
    assert all(
        all(tool.get(field) is not None for field in TOOL_FIELDS) for tool in tools
    )
    assert json.loads((tmp_path / "tools.json").read_text()) == tools


def test_package_is_reproducible_and_valid(tmp_path, config):
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"

    build_package(first, config)
    build_package(second, config)

    assert first.read_bytes() == second.read_bytes()
    with zipfile.ZipFile(first) as archive:
        assert archive.namelist() == list(PACKAGE_FILES)
    validate_package(first, development=True, schema_location=SCHEMA)


def test_validation_rejects_placeholder_ids_outside_development(tmp_path, config):
    package = tmp_path / "development.zip"
    development_config = PackageConfig(
        app_id="00000000-0000-4000-8000-000000000000",
        auth_config_id="DEVELOPMENT-AUTH-CONFIG-ID",
        version=config.version,
        terms_url=config.terms_url,
        color_icon=config.color_icon,
        outline_icon=config.outline_icon,
        development=True,
    )
    build_package(package, development_config)

    with pytest.raises(PackageValidationError, match="placeholder"):
        validate_package(package, schema_location=SCHEMA)
    validate_package(package, development=True, schema_location=SCHEMA)


def test_validation_rejects_development_icons_outside_development(tmp_path, config):
    package = tmp_path / "development-icons.zip"
    build_package(package, config)

    with pytest.raises(PackageValidationError, match="development placeholder"):
        validate_package(package, schema_location=SCHEMA)


def test_validation_rejects_malformed_tool_description(tmp_path, config):
    package = tmp_path / "package.zip"
    malformed = tmp_path / "malformed.zip"
    build_package(package, config)

    with zipfile.ZipFile(package) as source, zipfile.ZipFile(
        malformed, "w"
    ) as destination:
        for name in source.namelist():
            content = source.read(name)
            if name == "tools/alpha-vantage-tools.json":
                tools = json.loads(content)
                del tools[0]["annotations"]
                content = json.dumps(tools).encode()
            destination.writestr(name, content)

    with pytest.raises(PackageValidationError, match="every tool"):
        validate_package(malformed, development=True, schema_location=SCHEMA)


def test_validation_rejects_bad_version(tmp_path, config):
    package = tmp_path / "package.zip"
    malformed = tmp_path / "malformed.zip"
    build_package(package, config)

    with zipfile.ZipFile(package) as source, zipfile.ZipFile(
        malformed, "w"
    ) as destination:
        for name in source.namelist():
            content = source.read(name)
            if name == "manifest.json":
                manifest = json.loads(content)
                manifest["version"] = "not-a-version"
                content = json.dumps(manifest).encode()
            destination.writestr(name, content)

    with pytest.raises(PackageValidationError, match="semantic versioning"):
        validate_package(malformed, development=True, schema_location=SCHEMA)


def test_validation_rejects_extra_archive_content(tmp_path, config):
    package = tmp_path / "package.zip"
    malformed = tmp_path / "malformed.zip"
    build_package(package, config)
    shutil.copyfile(package, malformed)
    with zipfile.ZipFile(malformed, "a") as archive:
        archive.writestr(".env", "secret")

    with pytest.raises(PackageValidationError, match="expected files"):
        validate_package(malformed, schema_location=SCHEMA)
