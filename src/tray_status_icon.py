"""Green/red tray icons reflecting winws2 process state."""

from __future__ import annotations

import os
import sys
import tempfile

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap

from settings.mode import EXE_NAME_WINWS2

_ICON_CACHE: dict[str, str] = {}


def _cache_path(name: str) -> str:
    cached = _ICON_CACHE.get(name)
    if cached and os.path.exists(cached):
        return cached

    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    color = QColor("#22c55e") if name == "running" else QColor("#ef4444")
    painter.setBrush(color)
    painter.setPen(Qt.PenStyle.NoPen)
    margin = 6
    painter.drawEllipse(margin, margin, size - margin * 2, size - margin * 2)
    painter.end()

    folder = os.path.join(tempfile.gettempdir(), "rknhs_tray_icons")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"tray_{name}.ico")
    pixmap.save(path, "ICO")
    _ICON_CACHE[name] = path
    return path


def resolve_status_icon_path(*, running: bool) -> str:
    return _cache_path("running" if running else "stopped")


def is_winws2_running() -> bool:
    try:
        from winws_runtime.health.process_health_check import _check_process_running

        running, _pid = _check_process_running(EXE_NAME_WINWS2)
        return bool(running)
    except Exception:
        return False


def load_status_icon_handle(*, running: bool):
    """Return WinAPI HICON handle for native tray backend."""
    if sys.platform != "win32":
        return None

    import ctypes

    path = resolve_status_icon_path(running=running)
    user32 = ctypes.windll.user32
    IMAGE_ICON = 1
    LR_LOADFROMFILE = 0x0010
    LR_DEFAULTSIZE = 0x0040
    try:
        handle = user32.LoadImageW(
            None,
            path,
            IMAGE_ICON,
            0,
            0,
            LR_LOADFROMFILE | LR_DEFAULTSIZE,
        )
        return handle or None
    except Exception:
        return None
