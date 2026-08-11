"""Export the deployed MCP tool catalog for the Cowork connector package."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from av_mcp.stdio_server import META_TOOLS, build_tools


TOOL_FIELDS = ("name", "description", "inputSchema", "annotations")


def tool_descriptions() -> list[dict[str, Any]]:
    """Return the deployed MCP tools/list catalog in wire shape."""
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.inputSchema,
            "annotations": tool.annotations.model_dump(exclude_none=True),
        }
        for tool in build_tools() + META_TOOLS
    ]


def write_tool_descriptions(path: Path) -> list[dict[str, Any]]:
    """Write a deterministic JSON snapshot of the deployed tool catalog."""
    tools = tool_descriptions()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(tools, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return tools
