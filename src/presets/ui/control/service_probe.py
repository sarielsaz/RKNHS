"""Reachability probes for the service dashboard."""

from __future__ import annotations

import socket
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Literal

ServiceStatusKind = Literal["ok", "vpn", "fail"]

_PROBE_TIMEOUT_SEC = 5.0
_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) RKNHS-ServiceCheck/1.0"


@dataclass(frozen=True, slots=True)
class ServiceDefinition:
    service_id: str
    title: str
    host: str
    requires_vpn: bool = False
    https_path: str = "/"


def _probe_host_dns(host: str, *, timeout: float = 1.2) -> tuple[bool, str]:
    previous_timeout = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(max(0.5, float(timeout)))
        socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        return True, "DNS OK"
    except socket.gaierror as exc:
        return False, f"DNS: {exc.args[0] if exc.args else 'error'}"
    except OSError as exc:
        return False, str(exc)[:48]
    finally:
        socket.setdefaulttimeout(previous_timeout)


def probe_service_dns(defn: ServiceDefinition) -> tuple[ServiceStatusKind, str]:
    ok, detail = _probe_host_dns(defn.host)
    if not ok:
        return "fail", detail
    if defn.requires_vpn:
        return "vpn", "DNS OK · нужен VPN"
    return "ok", detail


def probe_service_https(defn: ServiceDefinition) -> tuple[ServiceStatusKind, str]:
    url = f"https://{defn.host}{defn.https_path or '/'}"
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": _USER_AGENT, "Accept": "*/*"},
    )
    context = ssl.create_default_context()
    try:
        with urllib.request.urlopen(request, timeout=_PROBE_TIMEOUT_SEC, context=context) as response:
            code = int(getattr(response, "status", 200) or 200)
        if code < 400:
            return "ok", f"HTTP {code}"
        if defn.requires_vpn and code in (403, 451):
            return "vpn", f"HTTP {code} · нужен VPN"
        return "fail", f"HTTP {code}"
    except urllib.error.HTTPError as exc:
        code = int(getattr(exc, "code", 0) or 0)
        if code < 400:
            return "ok", f"HTTP {code}"
        if defn.requires_vpn and code in (403, 451, 400):
            return "vpn", f"HTTP {code} · нужен VPN"
        return "fail", f"HTTP {code}"
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        return "fail", str(reason)[:56]
    except Exception as exc:
        return "fail", str(exc)[:56]
