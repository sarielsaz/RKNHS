"""Terminal / operator typography helpers (DESIGN.md)."""

from __future__ import annotations


def format_terminal_heading(text: str) -> str:
    """Prefix section/page titles as console headings: // TITLE."""
    raw = " ".join(str(text or "").split())
    if not raw:
        return ""
    if raw.startswith("//") or raw.startswith("["):
        return raw
    return f"// {raw.upper()}"


def format_hud_label(text: str) -> str:
    raw = " ".join(str(text or "").split())
    return raw.upper() if raw else ""


__all__ = ["format_hud_label", "format_terminal_heading"]
