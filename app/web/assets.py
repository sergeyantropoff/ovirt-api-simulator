"""Static web console assets."""

from __future__ import annotations

from pathlib import Path

_WEB_ROOT = Path(__file__).parent
_CONSOLE_HTML = _WEB_ROOT / "index.html"
_STATIC = _WEB_ROOT / "static"


def console_html() -> str:
    """Return the latest console markup from disk."""

    return _CONSOLE_HTML.read_text(encoding="utf-8")


def static_path(name: str) -> Path | None:
    path = _STATIC / name
    return path if path.is_file() else None
