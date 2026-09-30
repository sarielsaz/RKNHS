"""Стили pre-main окон: ultra-tech dark (см. DESIGN.md)."""

from __future__ import annotations

from PyQt6.QtWidgets import QWidget

from qfluentwidgets import isDarkTheme


def startup_palette() -> dict[str, str]:
    if isDarkTheme():
        return {
            "window": "#0A0C10",
            "card": "#12151C",
            "primary": "rgba(235, 242, 250, 0.94)",
            "secondary": "rgba(180, 194, 210, 0.72)",
            "muted": "rgba(140, 156, 176, 0.48)",
            "input_bg": "#181C26",
            "input_text": "rgba(235, 242, 250, 0.94)",
            "border": "rgba(255, 255, 255, 0.10)",
            "accent": "#5CD6FF",
        }
    return {
        "window": "#F3F5F8",
        "card": "#ffffff",
        "primary": "#0C121C",
        "secondary": "#333333",
        "muted": "#555555",
        "input_bg": "#ffffff",
        "input_text": "#0C121C",
        "border": "rgba(0, 0, 0, 0.10)",
        "accent": "#0090A8",
    }


def apply_label_style(widget: QWidget, *, role: str = "primary") -> None:
    palette = startup_palette()
    color = palette.get(role, palette["primary"])
    widget.setStyleSheet(f"color: {color}; background: transparent;")


def apply_window_style(widget: QWidget) -> None:
    palette = startup_palette()
    widget.setStyleSheet(f"background-color: {palette['window']};")


def apply_card_style(widget: QWidget) -> None:
    palette = startup_palette()
    widget.setStyleSheet(
        f"CardWidget {{ background-color: {palette['card']}; "
        f"border: 1px solid {palette['border']}; border-radius: 4px; }}"
    )


def apply_line_edit_style(widget: QWidget) -> None:
    palette = startup_palette()
    widget.setStyleSheet(
        "LineEdit {"
        f"color: {palette['input_text']};"
        f"background-color: {palette['input_bg']};"
        f"border: 1px solid {palette['border']};"
        "border-radius: 2px;"
        "padding: 6px 10px;"
        "}"
        "LineEdit:focus {"
        f"border: 1px solid {palette['accent']};"
        "}"
    )


__all__ = [
    "apply_card_style",
    "apply_label_style",
    "apply_line_edit_style",
    "apply_window_style",
    "startup_palette",
]
