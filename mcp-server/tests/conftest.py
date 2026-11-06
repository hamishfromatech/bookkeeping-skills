from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


def extract(result: Any) -> Any:
    """Normalise a tool call result across fastmcp versions.

    Older versions return a list of content blocks; newer versions return a
    CallToolResult with a ``.data`` attribute.
    """
    data = getattr(result, "data", None)
    if data is not None:
        return data

    blocks = result if isinstance(result, list) else getattr(result, "content", [])
    if not blocks:
        return None
    text = getattr(blocks[0], "text", None)
    if text is None:
        return blocks
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


async def call(client, name: str, arguments: dict | None = None) -> Any:
    return extract(await client.call_tool(name, arguments or {}))
