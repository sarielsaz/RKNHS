"""Надёжное копирование в буфер обмена (Windows + Qt)."""

from __future__ import annotations

import subprocess

from PyQt6.QtGui import QClipboard, QGuiApplication
from PyQt6.QtWidgets import QApplication


def copy_text_to_clipboard(text: str) -> bool:
    value = str(text or "").strip()
    if not value:
        return False

    app = QApplication.instance() or QGuiApplication.instance()
    if app is not None:
        clipboard = app.clipboard()
        if clipboard is not None:
            clipboard.clear(mode=QClipboard.Mode.Clipboard)
            clipboard.setText(value, mode=QClipboard.Mode.Clipboard)
            app.processEvents()
            if clipboard.text(QClipboard.Mode.Clipboard).strip() == value:
                return True

    try:
        subprocess.run(
            ["cmd", "/c", "clip"],
            input=value.encode("utf-8"),
            check=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return True
    except Exception:
        return False


__all__ = ["copy_text_to_clipboard"]
