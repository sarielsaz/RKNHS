from __future__ import annotations

import os
import shutil
import time
from dataclasses import dataclass

from config.config import MAIN_DIRECTORY
from log.log import log
from settings.store import (
    add_vpn_split_rule,
    get_vpn_split_config_path,
    get_vpn_split_enabled,
    get_vpn_split_rules,
    set_vpn_split_cli_tunnel_installed,
    set_vpn_split_rules,
)
from vpn_split.config_parser import parse_wireguard_config, write_wireguard_config
from vpn_split.domain_import import parse_domain_lines
from vpn_split.domain_resolver import resolve_domain_ips
from vpn_split.ipset_writer import clear_vpn_ipset, write_vpn_ipset
from vpn_split.tunnel import (
    deactivate_tunnel_adapters,
    get_tunnel_status,
    reload_tunnel,
    stop_running_tunnel_services,
    stop_tunnel,
)


@dataclass(frozen=True, slots=True)
class VpnSplitSyncResult:
    ok: bool
    message: str
    ip_count: int = 0
    domain_count: int = 0
    active_config_path: str = ""
    telegram_routes_ok: bool | None = None
    tunnel_active: bool | None = None


# Known Telegram IPv4 prefixes used in AmneziaWG AllowedIPs examples.
_TELEGRAM_ROUTE_MARKERS = ("149.154.", "91.108.", "95.161.")


def _has_telegram_routes(ips: list[str]) -> bool:
    blob = ",".join(str(ip or "") for ip in ips)
    return any(marker in blob for marker in _TELEGRAM_ROUTE_MARKERS)


def _format_post_apply_status(
    *,
    domain_count: int,
    domain_ip_count: int,
    out_path: str,
    ipset_path: str,
    all_allowed_ips: list[str],
    reload_tunnel_service: bool,
    tunnel_ok: bool | None,
    tunnel_message: str = "",
) -> tuple[str, bool, bool]:
    telegram_ok = _has_telegram_routes(all_allowed_ips)
    tunnel_status = get_tunnel_status()
    tunnel_active = bool(tunnel_status.is_active) or bool(tunnel_ok)

    lines = [
        f"Готово: {domain_count} сайт(ов), +{domain_ip_count} IP из списка.",
        f"• Конфиг записан: {out_path}",
        f"• DPI-исключения: {ipset_path}",
    ]
    if telegram_ok:
        lines.append("• Маршруты Telegram: есть в AllowedIPs")
    else:
        lines.append(
            "• Маршруты Telegram: не найдены — добавьте CIDR Telegram в исходный .conf "
            "или домен через список сайтов"
        )

    if reload_tunnel_service and tunnel_ok:
        lines.append(
            f"• Туннель: CLI-служба поднята ({tunnel_message or 'ok'}). "
            "AmneziaWG GUI может показывать «отключено»."
        )
    elif tunnel_active:
        lines.append("• Туннель: активен (адаптер/служба видны системе)")
    else:
        lines.append(
            "• Туннель: не подхватил conf — обновите/переподключите туннель в AmneziaWG"
        )

    lines.append("DPI-исключения действуют только пока VPN подключён.")
    return "\n".join(lines), telegram_ok, tunnel_active


def _vpn_settings_dir() -> str:
    path = os.path.join(MAIN_DIRECTORY, "settings", "vpn")
    os.makedirs(path, exist_ok=True)
    return path


def active_config_path() -> str:
    return os.path.join(_vpn_settings_dir(), "active.conf")


def resolve_domain_rule(domain: str) -> tuple[str, list[str]]:
    from vpn_split.domain_patterns import normalize_domain_pattern

    clean = normalize_domain_pattern(domain) or str(domain or "").strip().lower()
    ips = resolve_domain_ips(clean)
    return clean, ips


def refresh_all_domain_ips(*, only_enabled: bool = True) -> VpnSplitSyncResult:
    rules = list(get_vpn_split_rules())
    if not rules:
        return VpnSplitSyncResult(False, "Нет доменов для обновления")

    updated_rules: list[dict] = []
    resolved_domains = 0
    total_ips = 0

    for raw in rules:
        item = dict(raw or {})
        if only_enabled and not bool(item.get("enabled", True)):
            updated_rules.append(item)
            continue
        domain = str(item.get("domain") or "").strip().lower()
        if not domain:
            updated_rules.append(item)
            continue
        domain, ips = resolve_domain_rule(domain)
        item["domain"] = domain
        item["ips"] = ips
        item["updated_at"] = int(time.time())
        updated_rules.append(item)
        if ips:
            resolved_domains += 1
            total_ips += len(ips)

    set_vpn_split_rules(updated_rules)
    message = (
        f"IP обновлены: {resolved_domains} домен(ов), {total_ips} адресов. "
        "Нажмите «Применить», чтобы синхронизировать DPI и active.conf."
    )
    log(message, "INFO")
    return VpnSplitSyncResult(
        True,
        message,
        ip_count=total_ips,
        domain_count=resolved_domains,
    )


def import_vpn_split_domains(text: str, *, resolve_ips: bool = True) -> VpnSplitSyncResult:
    domains = parse_domain_lines(text)
    if not domains:
        return VpnSplitSyncResult(False, "Список доменов пуст")

    added = 0
    skipped = 0
    for domain in domains:
        if add_vpn_split_rule(domain):
            added += 1
        else:
            skipped += 1

    message = f"Импорт: добавлено {added}, уже были {skipped}"
    if resolve_ips and (added or skipped):
        refresh = refresh_all_domain_ips()
        message = f"{message}. {refresh.message}"
        return VpnSplitSyncResult(
            refresh.ok or added > 0,
            message,
            ip_count=refresh.ip_count,
            domain_count=added,
        )
    return VpnSplitSyncResult(True, message, domain_count=added)


def stop_vpn_system_tunnel(*, config_path: str | None = None) -> VpnSplitSyncResult:
    path = os.path.abspath(str(config_path or active_config_path()))
    if not os.path.isfile(path):
        set_vpn_split_cli_tunnel_installed(False)
        return VpnSplitSyncResult(False, f"Конфиг туннеля не найден: {path}")

    result = stop_tunnel(path)
    if result.ok:
        set_vpn_split_cli_tunnel_installed(False)
        log(result.message, "INFO")
        return VpnSplitSyncResult(True, result.message, active_config_path=path)
    log(result.message, "WARNING")
    return VpnSplitSyncResult(False, result.message, active_config_path=path)


def _collect_tunnel_config_paths() -> list[str]:
    paths: list[str] = []
    for candidate in (active_config_path(), get_vpn_split_config_path()):
        path = os.path.abspath(str(candidate or ""))
        if path and os.path.isfile(path) and path not in paths:
            paths.append(path)
    return paths


def stop_vpn_tunnel_for_exit() -> VpnSplitSyncResult:
    """Останавливает VPN-туннель при полном закрытии приложения."""
    if not get_tunnel_status().is_active:
        return VpnSplitSyncResult(True, "VPN туннель не активен")

    messages: list[str] = []
    for path in _collect_tunnel_config_paths():
        result = stop_tunnel(path)
        if result.ok:
            messages.append(result.message)
            set_vpn_split_cli_tunnel_installed(False)
        if not get_tunnel_status().is_active:
            break

    if get_tunnel_status().is_active:
        service_result = stop_running_tunnel_services()
        if service_result.ok:
            messages.append(service_result.message)

    if get_tunnel_status().is_active:
        adapter_result = deactivate_tunnel_adapters()
        if adapter_result.ok:
            messages.append(adapter_result.message)

    if not get_tunnel_status().is_active:
        set_vpn_split_cli_tunnel_installed(False)
        try:
            clear_vpn_ipset()
        except Exception as exc:
            log(f"Не удалось очистить VPN ipset при закрытии: {exc}", "DEBUG")
        message = messages[0] if messages else "VPN туннель остановлен"
        log(f"При закрытии приложения: {message}", "INFO")
        return VpnSplitSyncResult(True, message)

    detail = messages[-1] if messages else "Не удалось остановить VPN туннель"
    log(f"При закрытии приложения VPN остался активен: {detail}", "WARNING")
    return VpnSplitSyncResult(False, detail)


def disable_vpn_split(*, stop_system_tunnel: bool = True) -> VpnSplitSyncResult:
    clear_vpn_ipset()
    message = "VPN Split выключен, DPI-исключения сброшены"
    if stop_system_tunnel:
        stop_result = stop_vpn_system_tunnel()
        if stop_result.ok:
            message = f"{message}. {stop_result.message}"
        elif get_tunnel_status().is_active:
            message = (
                f"{message}. Не удалось остановить CLI-туннель: {stop_result.message}. "
                "Нажмите «Остановить CLI-туннель» на вкладке VPN Split."
            )
    return VpnSplitSyncResult(True, message)


def apply_vpn_split_sync(*, reload_tunnel_service: bool = False) -> VpnSplitSyncResult:
    if not get_vpn_split_enabled():
        return VpnSplitSyncResult(False, "VPN Split выключен в настройках")

    source_path = str(get_vpn_split_config_path() or "").strip()
    if not source_path or not os.path.isfile(source_path):
        return VpnSplitSyncResult(False, "Укажите существующий .conf AmneziaWG")

    out_path = active_config_path()
    if os.path.abspath(source_path) == os.path.abspath(out_path):
        return VpnSplitSyncResult(
            False,
            "В качестве исходного .conf указан active.conf (выходной файл). "
            "Укажите исходный экспорт AmneziaWG (например settings/vpn/base.conf).",
        )

    rules = list(get_vpn_split_rules())
    dynamic_ips: list[str] = []
    updated_rules: list[dict] = []
    domain_count = 0

    for raw in rules:
        item = dict(raw or {})
        if not bool(item.get("enabled", True)):
            updated_rules.append(item)
            continue
        domain = str(item.get("domain") or "").strip().lower()
        if not domain:
            continue
        ips = list(item.get("ips") or [])
        if not ips:
            domain, ips = resolve_domain_rule(domain)
        else:
            domain, _ = resolve_domain_rule(domain)
        item["domain"] = domain
        item["ips"] = ips
        item["updated_at"] = int(time.time())
        updated_rules.append(item)
        if ips:
            domain_count += 1
            dynamic_ips.extend(ips)

    set_vpn_split_rules(updated_rules)

    parsed = parse_wireguard_config(source_path)
    if not parsed.interface_lines:
        return VpnSplitSyncResult(
            False,
            "В исходном .conf нет секции [Interface] (PrivateKey/Address). "
            "Экспортируйте конфиг заново из AmneziaWG.",
        )

    static_ips = list(parsed.static_allowed_ips)
    domain_only_ips = [ip for ip in dynamic_ips if ip not in set(static_ips)]
    ipset_ips = static_ips + domain_only_ips
    ipset_path = write_vpn_ipset(ipset_ips)

    try:
        write_wireguard_config(out_path, source=parsed, dynamic_allowed_ips=domain_only_ips)
    except ValueError as exc:
        return VpnSplitSyncResult(False, str(exc))

    domain_ip_count = len(domain_only_ips)
    all_allowed = static_ips + domain_only_ips
    log(
        f"VPN Split apply: {domain_count} domains, +{domain_ip_count} dynamic IPs → {out_path}",
        "INFO",
    )

    tunnel_ok: bool | None = None
    tunnel_message = ""
    if reload_tunnel_service:
        tunnel = reload_tunnel(out_path)
        tunnel_ok = bool(tunnel.ok)
        tunnel_message = str(tunnel.message or "")
        if tunnel.ok:
            set_vpn_split_cli_tunnel_installed(True)

    message, telegram_ok, tunnel_active = _format_post_apply_status(
        domain_count=domain_count,
        domain_ip_count=domain_ip_count,
        out_path=out_path,
        ipset_path=ipset_path,
        all_allowed_ips=all_allowed,
        reload_tunnel_service=reload_tunnel_service,
        tunnel_ok=tunnel_ok,
        tunnel_message=tunnel_message,
    )
    if reload_tunnel_service and tunnel_ok is False:
        message += f"\n• CLI-служба: не поднялась ({tunnel_message or 'ошибка'})"

    return VpnSplitSyncResult(
        True,
        message,
        ip_count=len(all_allowed),
        domain_count=domain_count,
        active_config_path=out_path,
        telegram_routes_ok=telegram_ok,
        tunnel_active=tunnel_active,
    )


def import_config_file(source_path: str) -> str:
    source_path = os.path.abspath(str(source_path or ""))
    if not os.path.isfile(source_path):
        raise FileNotFoundError(source_path)
    target = os.path.join(_vpn_settings_dir(), "base.conf")
    shutil.copy2(source_path, target)
    return target
