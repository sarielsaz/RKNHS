"""Watch VPN tunnel state and restart winws2 when it changes."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PyQt6.QtCore import QTimer

from log.log import log
from settings.store import get_vpn_split_enabled
from vpn_split.tunnel import is_vpn_tunnel_active

RestartWinws = Callable[[], bool]


class VpnTunnelWatcher:
    def __init__(self, *, restart_winws: RestartWinws, parent: Any = None) -> None:
        self._restart_winws = restart_winws
        self._last_active: bool | None = None
        self._poll_timer = QTimer(parent)
        self._poll_timer.setInterval(3000)
        self._poll_timer.timeout.connect(self._poll)
        self._debounce_timer = QTimer(parent)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(2000)
        self._debounce_timer.timeout.connect(self._restart_after_change)

    def start(self) -> None:
        self._last_active = is_vpn_tunnel_active() if get_vpn_split_enabled() else None
        self._poll_timer.start()
        if get_vpn_split_enabled():
            state = "up" if self._last_active else "down"
            log(f"VPN tunnel watcher started (tunnel={state})", "DEBUG")

    def stop(self) -> None:
        self._poll_timer.stop()
        self._debounce_timer.stop()

    def _poll(self) -> None:
        if not get_vpn_split_enabled():
            self._last_active = None
            return

        active = is_vpn_tunnel_active()
        if self._last_active is None:
            self._last_active = active
            return
        if active == self._last_active:
            return

        self._last_active = active
        state = "подключён" if active else "отключён"
        log(f"VPN туннель {state} — перезапуск winws2 через 2 с", "INFO")
        if not self._debounce_timer.isActive():
            self._debounce_timer.start()

    def _restart_after_change(self) -> None:
        try:
            if self._restart_winws():
                log("winws2 перезапущен после смены состояния VPN", "INFO")
            else:
                log("winws2 не запущен — перезапуск после VPN не требуется", "DEBUG")
        except Exception as exc:
            log(f"Не удалось перезапустить winws2 после VPN: {exc}", "WARNING")


_watcher: VpnTunnelWatcher | None = None


def install_vpn_tunnel_watcher(*, restart_winws: RestartWinws, parent: Any = None) -> VpnTunnelWatcher:
    global _watcher
    if _watcher is not None:
        return _watcher
    _watcher = VpnTunnelWatcher(restart_winws=restart_winws, parent=parent)
    _watcher.start()
    return _watcher


__all__ = ["VpnTunnelWatcher", "install_vpn_tunnel_watcher"]
