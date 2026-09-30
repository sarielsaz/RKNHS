from __future__ import annotations

from main.post_startup_gate import bind_startup_gate, is_startup_host_alive


def install_vpn_tunnel_watcher_startup(startup_host, *, runtime_feature, log_startup_metric) -> None:
    def _install() -> None:
        if not is_startup_host_alive(startup_host):
            return
        log_startup_metric("StartupVpnTunnelWatcherQueued", "post-init")
        try:
            from vpn_split.watcher import install_vpn_tunnel_watcher

            def restart_winws() -> bool:
                return bool(runtime_feature.restart(force_full_stop=False))

            install_vpn_tunnel_watcher(
                restart_winws=restart_winws,
                parent=startup_host._window,
            )
        except Exception as exc:
            from log.log import log

            log(f"VPN tunnel watcher startup failed: {exc}", "DEBUG")

    bind_startup_gate(
        startup_host.startup_post_init_ready,
        _install,
        is_ready=lambda: bool(startup_host.startup_state.post_init_ready),
    )


__all__ = ["install_vpn_tunnel_watcher_startup"]
