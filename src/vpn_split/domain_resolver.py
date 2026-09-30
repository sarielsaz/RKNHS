from __future__ import annotations

import ipaddress
import socket

from vpn_split.domain_patterns import hosts_to_resolve, normalize_domain_pattern


def resolve_domain_ips(domain: str, *, timeout: float = 4.0) -> list[str]:
    """Resolve a host or wildcard pattern (*.cursor.sh) to CIDR routes."""
    pattern = normalize_domain_pattern(domain)
    hosts = hosts_to_resolve(pattern or str(domain or ""))
    if not hosts:
        return []

    previous = socket.getdefaulttimeout()
    found: set[str] = set()

    try:
        socket.setdefaulttimeout(max(0.5, float(timeout)))
        for candidate in hosts:
            try:
                for info in socket.getaddrinfo(candidate, None, socket.AF_UNSPEC, socket.SOCK_STREAM):
                    addr = info[4][0]
                    ip = ipaddress.ip_address(str(addr))
                    if ip.version == 4:
                        found.add(f"{ip}/32")
                    elif ip.version == 6:
                        found.add(f"{ip}/128")
            except socket.gaierror:
                continue
    finally:
        socket.setdefaulttimeout(previous)

    return sorted(found)
