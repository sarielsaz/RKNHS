from __future__ import annotations

import os
import re
from dataclasses import dataclass, field


@dataclass
class WireGuardConfig:
    interface_lines: list[str] = field(default_factory=list)
    peer_lines: list[str] = field(default_factory=list)
    static_allowed_ips: list[str] = field(default_factory=list)


_SECTION_RE = re.compile(r"^\s*\[(Interface|Peer)\]\s*$", re.I)
_ALLOWED_IPS_RE = re.compile(r"^\s*AllowedIPs\s*=\s*(.+)\s*$", re.I)


def parse_wireguard_config(path: str) -> WireGuardConfig:
    with open(path, "r", encoding="utf-8-sig", errors="ignore") as handle:
        lines = handle.readlines()

    result = WireGuardConfig()
    section = ""
    for raw in lines:
        line = raw.rstrip("\n").lstrip("\ufeff")
        match = _SECTION_RE.match(line)
        if match:
            section = match.group(1).lower()
            if section == "interface":
                result.interface_lines.append(line)
            elif section == "peer":
                result.peer_lines.append(line)
            continue

        allowed = _ALLOWED_IPS_RE.match(line)
        if allowed and section == "peer":
            chunk = str(allowed.group(1) or "").strip()
            if chunk:
                for part in chunk.split(","):
                    value = part.strip()
                    if value:
                        result.static_allowed_ips.append(value)
            result.peer_lines.append(line)
            continue

        if section == "interface":
            result.interface_lines.append(line)
        elif section == "peer":
            result.peer_lines.append(line)

    return result


def write_wireguard_config(
    path: str,
    *,
    source: WireGuardConfig,
    dynamic_allowed_ips: list[str],
) -> None:
    if not source.interface_lines:
        raise ValueError(
            f"В .conf нет секции [Interface] (PrivateKey/Address). "
            f"Проверьте исходный файл AmneziaWG: {path}"
        )

    merged: list[str] = []
    seen: set[str] = set()
    for value in [*source.static_allowed_ips, *dynamic_allowed_ips]:
        item = str(value or "").strip()
        if not item or item in seen:
            continue
        seen.add(item)
        merged.append(item)

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        for line in source.interface_lines:
            handle.write(f"{line}\n")
        handle.write("\n")
        for line in source.peer_lines:
            if _ALLOWED_IPS_RE.match(line):
                continue
            handle.write(f"{line}\n")
        if merged:
            handle.write(f"AllowedIPs = {', '.join(merged)}\n")
