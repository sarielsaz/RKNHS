from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TunnelActionResult:
    ok: bool
    message: str


@dataclass(frozen=True, slots=True)
class TunnelServiceInfo:
    name: str
    status: str
    display_name: str


@dataclass(frozen=True, slots=True)
class TunnelStatus:
    adapter_up: bool
    adapter_names: tuple[str, ...]
    services: tuple[TunnelServiceInfo, ...]

    @property
    def has_running_service(self) -> bool:
        return any(item.status.lower() == "running" for item in self.services)

    @property
    def is_active(self) -> bool:
        return self.adapter_up or self.has_running_service


def _candidate_binaries() -> list[str]:
    names = (
        "amneziawg.exe",
        "wireguard.exe",
        "wg.exe",
    )
    paths: list[str] = []
    for name in names:
        found = shutil.which(name)
        if found:
            paths.append(found)
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    local_app = os.environ.get("LOCALAPPDATA", "")
    for sub in (
        os.path.join(program_files, "AmneziaWG", "amneziawg.exe"),
        os.path.join(program_files, "WireGuard", "wireguard.exe"),
        os.path.join(program_files_x86, "AmneziaWG", "amneziawg.exe"),
        os.path.join(local_app, "Programs", "AmneziaWG", "amneziawg.exe"),
        os.path.join(local_app, "AmneziaWG", "amneziawg.exe"),
    ):
        if os.path.isfile(sub):
            paths.append(sub)
    return paths


def tunnel_name_from_config(config_path: str) -> str:
    base = os.path.basename(str(config_path or "").strip())
    if base.lower().endswith(".conf"):
        base = base[:-5]
    return base or "tunnel"


def _run_powershell(script: str, *, timeout: int = 8) -> str:
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True,
        text=True,
        timeout=timeout,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    return str(completed.stdout or "")


def list_tunnel_services() -> list[TunnelServiceInfo]:
    if sys.platform != "win32":
        return []
    try:
        output = _run_powershell(
            "Get-Service -ErrorAction SilentlyContinue | "
            "Where-Object { $_.Name -match 'AmneziaWGTunnel|WireGuardTunnel' } | "
            "ForEach-Object { \"$($_.Name)|$($_.Status)|$($_.DisplayName)\" }"
        )
    except Exception:
        return []

    services: list[TunnelServiceInfo] = []
    for line in output.splitlines():
        parts = [part.strip() for part in line.split("|", 2)]
        if len(parts) != 3 or not parts[0]:
            continue
        services.append(TunnelServiceInfo(name=parts[0], status=parts[1], display_name=parts[2]))
    return services


def get_tunnel_status() -> TunnelStatus:
    adapter_names: list[str] = []
    adapter_up = False
    if sys.platform == "win32":
        try:
            output = _run_powershell(
                "Get-NetAdapter -ErrorAction SilentlyContinue | "
                "Where-Object { $_.InterfaceDescription -match 'WireGuard|Amnezia' } | "
                "ForEach-Object { \"$($_.Name)|$($_.Status)\" }"
            )
            for line in output.splitlines():
                parts = [part.strip() for part in line.split("|", 1)]
                if len(parts) != 2:
                    continue
                adapter_names.append(parts[0])
                if parts[1].lower() == "up":
                    adapter_up = True
        except Exception:
            pass
    return TunnelStatus(
        adapter_up=adapter_up,
        adapter_names=tuple(adapter_names),
        services=tuple(list_tunnel_services()),
    )


def is_vpn_tunnel_active() -> bool:
    return get_tunnel_status().is_active


def format_tunnel_status(status: TunnelStatus | None = None) -> str:
    status = status or get_tunnel_status()
    if not status.is_active:
        return "Системный туннель: не активен"

    parts: list[str] = []
    if status.adapter_up:
        names = ", ".join(status.adapter_names) or "WireGuard"
        parts.append(f"адаптер {names} — Up")
    running = [svc.display_name or svc.name for svc in status.services if svc.status.lower() == "running"]
    if running:
        parts.append("служба: " + "; ".join(running))
    detail = "; ".join(parts) if parts else "активен"
    return (
        f"Системный туннель: {detail}. "
        "AmneziaWG может показывать «отключено», если туннель поднят через RKNHS CLI."
    )


def _run_tunnel_cli(binary_args: list[str]) -> TunnelActionResult:
    errors: list[str] = []
    for binary in _candidate_binaries():
        try:
            completed = subprocess.run(
                [binary, *binary_args],
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if completed.returncode == 0:
                return TunnelActionResult(True, f"OK через {os.path.basename(binary)}")
            stderr = str(completed.stderr or completed.stdout or "").strip()
            if stderr:
                errors.append(stderr[:160])
        except Exception as exc:
            errors.append(str(exc)[:160])
            continue

    detail = errors[0] if errors else "CLI AmneziaWG/WireGuard не найден"
    return TunnelActionResult(False, detail)


def reload_tunnel(config_path: str) -> TunnelActionResult:
    """Переустанавливает Windows-службу туннеля из .conf.

    AmneziaWG: /installtunnelservice CONFIG_PATH,
    /uninstalltunnelservice TUNNEL_NAME (имя файла без .conf).
    """
    config_path = os.path.abspath(str(config_path or ""))
    if not os.path.isfile(config_path):
        return TunnelActionResult(False, f"Конфиг не найден: {config_path}")

    tunnel_name = tunnel_name_from_config(config_path)
    # Сначала снимаем старую службу по имени — иначе AllowedIPs не обновляются.
    _run_tunnel_cli(["/uninstalltunnelservice", tunnel_name])
    installed = _run_tunnel_cli(["/installtunnelservice", config_path])
    if installed.ok:
        return TunnelActionResult(
            True,
            f"Туннель «{tunnel_name}» установлен через {installed.message}",
        )
    return TunnelActionResult(False, f"Не удалось установить туннель: {installed.message}")


def stop_tunnel(config_path: str) -> TunnelActionResult:
    """Останавливает и удаляет Windows-службу туннеля для указанного .conf."""
    config_path = os.path.abspath(str(config_path or ""))
    tunnel_name = tunnel_name_from_config(config_path)
    result = _run_tunnel_cli(["/uninstalltunnelservice", tunnel_name])
    if result.ok:
        return TunnelActionResult(True, f"Туннель «{tunnel_name}» остановлен")

    if sys.platform != "win32":
        return result

    for service_name in (
        f"AmneziaWGTunnel${tunnel_name}",
        f"WireGuardTunnel${tunnel_name}",
    ):
        try:
            completed = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    f"Stop-Service -Name '{service_name}' -Force -ErrorAction Stop",
                ],
                capture_output=True,
                text=True,
                timeout=20,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if completed.returncode == 0:
                return TunnelActionResult(True, f"Служба {service_name} остановлена")
        except Exception:
            continue

    return result


def stop_running_tunnel_services() -> TunnelActionResult:
    if sys.platform != "win32":
        return TunnelActionResult(False, "Только Windows")

    stopped: list[str] = []
    for service in list_tunnel_services():
        if service.status.lower() != "running":
            continue
        try:
            completed = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    f"Stop-Service -Name '{service.name}' -Force -ErrorAction Stop",
                ],
                capture_output=True,
                text=True,
                timeout=20,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if completed.returncode == 0:
                stopped.append(service.name)
        except Exception:
            continue

    if stopped:
        return TunnelActionResult(True, "Остановлены службы: " + ", ".join(stopped))
    return TunnelActionResult(False, "Нет запущенных служб туннеля")


def deactivate_tunnel_adapters() -> TunnelActionResult:
    if sys.platform != "win32":
        return TunnelActionResult(False, "Только Windows")

    try:
        output = _run_powershell(
            "$names = @(); "
            "Get-NetAdapter -ErrorAction SilentlyContinue | "
            "Where-Object { $_.InterfaceDescription -match 'WireGuard|Amnezia' -and $_.Status -eq 'Up' } | "
            "ForEach-Object { "
            "Disable-NetAdapter -Name $_.Name -Confirm:$false -ErrorAction SilentlyContinue; "
            "$names += $_.Name "
            "}; "
            "$names -join ','",
            timeout=20,
        ).strip()
    except Exception as exc:
        return TunnelActionResult(False, str(exc)[:160])

    if output:
        names = ", ".join(part.strip() for part in output.split(",") if part.strip())
        return TunnelActionResult(True, f"VPN-адаптеры отключены: {names}")
    return TunnelActionResult(False, "Нет активных VPN-адаптеров")
