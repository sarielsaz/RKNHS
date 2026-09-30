"""Traffic route map: where traffic goes — DPI / VPN Split / hosts / plain internet."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TrafficLane:
    lane_id: str
    title: str
    state_label: str
    detail: str
    active: bool


@dataclass(frozen=True, slots=True)
class TrafficMapSnapshot:
    lanes: tuple[TrafficLane, ...]
    summary: str


def _plain_label(*, language: str) -> str:
    return "Обычный интернет" if language == "ru" else "Plain internet"


def build_traffic_map_snapshot(
    *,
    dpi_running: bool,
    dpi_scope_label: str = "",
    preset_name: str = "",
    vpn_enabled: bool = False,
    vpn_tunnel_active: bool = False,
    vpn_domain_count: int = 0,
    hosts_domain_count: int = 0,
    language: str = "ru",
) -> TrafficMapSnapshot:
    ru = language == "ru"
    scope = str(dpi_scope_label or "").strip()
    preset = str(preset_name or "").strip()

    if dpi_running:
        dpi_state = "Работает" if ru else "Running"
        dpi_detail_parts = [p for p in (scope, preset) if p]
        dpi_detail = " · ".join(dpi_detail_parts) if dpi_detail_parts else (
            "Обход по спискам" if ru else "Bypass via lists"
        )
    else:
        dpi_state = "Выкл" if ru else "Off"
        dpi_detail = "Не перехватывает трафик" if ru else "Not intercepting traffic"

    if vpn_enabled and vpn_tunnel_active:
        vpn_state = "Активен" if ru else "Active"
        vpn_detail = (
            f"{vpn_domain_count} доменов через VPN"
            if ru
            else f"{vpn_domain_count} domains via VPN"
        )
    elif vpn_enabled:
        vpn_state = "Настроен" if ru else "Configured"
        vpn_detail = (
            "Туннель не поднят" if ru else "Tunnel is down"
        )
    else:
        vpn_state = "Выкл" if ru else "Off"
        vpn_detail = (
            "Домены не уводятся в VPN" if ru else "No domains routed to VPN"
        )

    if hosts_domain_count > 0:
        hosts_state = "Есть записи" if ru else "Active"
        hosts_detail = (
            f"{hosts_domain_count} адресов в hosts"
            if ru
            else f"{hosts_domain_count} hosts entries"
        )
    else:
        hosts_state = "Пусто" if ru else "Empty"
        hosts_detail = (
            "Программа не меняет hosts" if ru else "No program hosts entries"
        )

    plain_state = "Остальное" if ru else "Everything else"
    plain_detail = (
        "Сайты вне DPI / VPN / hosts идут как обычно"
        if ru
        else "Sites outside DPI / VPN / hosts go normally"
    )

    lanes = (
        TrafficLane(
            lane_id="dpi",
            title="Через обход" if ru else "Through bypass",
            state_label=dpi_state,
            detail=dpi_detail,
            active=bool(dpi_running),
        ),
        TrafficLane(
            lane_id="vpn",
            title="Через VPN Split" if ru else "Through VPN Split",
            state_label=vpn_state,
            detail=vpn_detail,
            active=bool(vpn_enabled and vpn_tunnel_active),
        ),
        TrafficLane(
            lane_id="hosts",
            title="Через hosts" if ru else "Through hosts",
            state_label=hosts_state,
            detail=hosts_detail,
            active=hosts_domain_count > 0,
        ),
        TrafficLane(
            lane_id="plain",
            title=_plain_label(language=language),
            state_label=plain_state,
            detail=plain_detail,
            active=True,
        ),
    )

    active_bits: list[str] = []
    if dpi_running:
        active_bits.append("обход" if ru else "bypass")
    if vpn_enabled and vpn_tunnel_active:
        active_bits.append("VPN")
    if hosts_domain_count > 0:
        active_bits.append("hosts")
    if not active_bits:
        summary = (
            "Сейчас всё идёт обычным интернетом"
            if ru
            else "Everything uses plain internet right now"
        )
    else:
        joined = " + ".join(active_bits)
        summary = (
            f"Сейчас задействовано: {joined}"
            if ru
            else f"Active now: {joined}"
        )

    return TrafficMapSnapshot(lanes=lanes, summary=summary)


def collect_traffic_map_inputs(*, dpi_running: bool = False, language: str = "ru") -> dict:
    """Gather live inputs for the traffic map (safe defaults on errors)."""
    from presets.preset_clarity import build_preset_hud_clarity, scope_label
    from settings.dpi.strategy_settings import get_strategy_launch_method
    from settings.store import (
        get_selected_source_preset_file_name,
        get_vpn_split_enabled,
        get_vpn_split_rules,
    )

    preset_name = ""
    scope_tag = ""
    try:
        method = get_strategy_launch_method()
        preset_name = str(get_selected_source_preset_file_name(method) or "").strip()
        clarity = build_preset_hud_clarity(
            file_name=preset_name,
            dpi_running=bool(dpi_running),
            language=language,
        )
        scope_tag = scope_label(clarity.scope, language=language)
    except Exception:
        pass

    vpn_enabled = False
    vpn_tunnel_active = False
    vpn_domain_count = 0
    try:
        vpn_enabled = bool(get_vpn_split_enabled())
        rules = get_vpn_split_rules() or []
        vpn_domain_count = sum(
            1 for item in rules if bool((item or {}).get("enabled", True)) and str((item or {}).get("domain") or "").strip()
        )
        if vpn_enabled:
            from vpn_split.tunnel import is_vpn_tunnel_active

            vpn_tunnel_active = bool(is_vpn_tunnel_active())
    except Exception:
        pass

    hosts_domain_count = 0
    try:
        from hosts.commands import get_hosts_state

        state = get_hosts_state()
        hosts_domain_count = len(getattr(state, "active_domains", ()) or ())
    except Exception:
        pass

    return {
        "dpi_running": bool(dpi_running),
        "dpi_scope_label": scope_tag,
        "preset_name": preset_name,
        "vpn_enabled": vpn_enabled,
        "vpn_tunnel_active": vpn_tunnel_active,
        "vpn_domain_count": int(vpn_domain_count),
        "hosts_domain_count": int(hosts_domain_count),
        "language": language,
    }


__all__ = [
    "TrafficLane",
    "TrafficMapSnapshot",
    "build_traffic_map_snapshot",
    "collect_traffic_map_inputs",
]
