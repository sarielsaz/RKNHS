"""Shared short-TTL cache for DPI / VPN status probes.

Keeps tray + Control + VPN Split from repeatedly spawning process/PowerShell
checks while the UI is idle. Mutations should call invalidate_* / force=True.
"""

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vpn_split.tunnel import TunnelStatus

_DPI_TTL_S = 1.5
_TUNNEL_TTL_S = 1.5

_lock = threading.Lock()
_dpi_running: bool | None = None
_dpi_fetched_at = 0.0
_tunnel_status: TunnelStatus | None = None
_tunnel_fetched_at = 0.0


def invalidate_dpi_status_cache() -> None:
    global _dpi_running, _dpi_fetched_at
    with _lock:
        _dpi_running = None
        _dpi_fetched_at = 0.0


def invalidate_tunnel_status_cache() -> None:
    global _tunnel_status, _tunnel_fetched_at
    with _lock:
        _tunnel_status = None
        _tunnel_fetched_at = 0.0


def invalidate_runtime_status_cache() -> None:
    invalidate_dpi_status_cache()
    invalidate_tunnel_status_cache()


def get_cached_dpi_running(*, force: bool = False) -> bool:
    global _dpi_running, _dpi_fetched_at
    now = time.monotonic()
    with _lock:
        if (
            not force
            and _dpi_running is not None
            and (now - _dpi_fetched_at) < _DPI_TTL_S
        ):
            return bool(_dpi_running)

    try:
        from tray_status_icon import is_winws2_running as _probe

        running = bool(_probe())
    except Exception:
        running = False

    with _lock:
        _dpi_running = running
        _dpi_fetched_at = time.monotonic()
        return running


def get_cached_tunnel_status(*, force: bool = False):
    global _tunnel_status, _tunnel_fetched_at
    now = time.monotonic()
    with _lock:
        if (
            not force
            and _tunnel_status is not None
            and (now - _tunnel_fetched_at) < _TUNNEL_TTL_S
        ):
            return _tunnel_status

    from vpn_split.tunnel import get_tunnel_status as _probe

    status = _probe()
    with _lock:
        _tunnel_status = status
        _tunnel_fetched_at = time.monotonic()
        return status


__all__ = [
    "get_cached_dpi_running",
    "get_cached_tunnel_status",
    "invalidate_dpi_status_cache",
    "invalidate_runtime_status_cache",
    "invalidate_tunnel_status_cache",
]
