from __future__ import annotations

import os
import re

_LABEL_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


def _strip_host_noise(value: str) -> str:
    text = str(value or "").strip().lower()
    for prefix in ("https://", "http://"):
        if text.startswith(prefix):
            text = text[len(prefix) :]
    text = text.split("/", 1)[0]
    text = text.split("?", 1)[0]
    text = text.split("#", 1)[0]
    # Host:port → host
    if text.count(":") == 1 and not text.startswith("["):
        host, _, port = text.partition(":")
        if port.isdigit():
            text = host
    return text.strip().strip("/")


def is_plain_domain(value: str) -> bool:
    text = str(value or "").strip().lower().strip(".")
    if not text or len(text) > 253 or "*" in text:
        return False
    labels = text.split(".")
    if len(labels) < 2:
        return False
    if any(not _LABEL_RE.match(label) for label in labels):
        return False
    return len(labels[-1]) >= 2 and any(ch.isalpha() for ch in labels[-1])


def normalize_domain_pattern(value: str) -> str:
    """
    Accept plain hosts and wildcard forms:
      cursor.sh
      *.cursor.sh
      .cursor.sh   → *.cursor.sh
    """
    text = _strip_host_noise(value)
    if not text:
        return ""

    wildcard = False
    if text.startswith("*."):
        wildcard = True
        text = text[2:]
    elif text.startswith("."):
        wildcard = True
        text = text[1:]
    elif text.startswith("*"):
        # Reject bare *cursor.sh / *
        return ""

    text = text.strip().strip(".")
    if not is_plain_domain(text):
        return ""
    return f"*.{text}" if wildcard else text


def pattern_base_domain(pattern: str) -> str:
    clean = normalize_domain_pattern(pattern)
    if not clean:
        return ""
    return clean[2:] if clean.startswith("*.") else clean


def host_matches_pattern(host: str, pattern: str) -> bool:
    """True if host equals base or is a subdomain of base for *.base."""
    clean_host = normalize_domain_pattern(host)
    clean_pattern = normalize_domain_pattern(pattern)
    if not clean_host or not clean_pattern or clean_host.startswith("*."):
        return False
    if clean_pattern.startswith("*."):
        base = clean_pattern[2:]
        return clean_host == base or clean_host.endswith("." + base)
    return clean_host == clean_pattern


def discover_hosts_for_base(base: str, *, lists_dirs: list[str] | None = None) -> list[str]:
    """Collect concrete hosts from lists/*.txt that match *.base (plus apex)."""
    base = pattern_base_domain(base) or str(base or "").strip().lower().strip(".")
    if not base or not is_plain_domain(base):
        return []

    found: set[str] = {base, f"www.{base}"}
    dirs = lists_dirs or []
    if not dirs:
        try:
            from config.config import MAIN_DIRECTORY

            dirs = [os.path.join(MAIN_DIRECTORY, "lists")]
        except Exception:
            dirs = []

    for folder in dirs:
        if not folder or not os.path.isdir(folder):
            continue
        try:
            names = os.listdir(folder)
        except OSError:
            continue
        for name in names:
            if not name.lower().endswith(".txt"):
                continue
            path = os.path.join(folder, name)
            try:
                with open(path, encoding="utf-8", errors="ignore") as handle:
                    for raw in handle:
                        token = normalize_domain_pattern(raw.split("#", 1)[0])
                        if not token or token.startswith("*."):
                            continue
                        if host_matches_pattern(token, f"*.{base}"):
                            found.add(token)
            except OSError:
                continue

    # Well-known Cursor agent/CDN hosts when lists are incomplete.
    if base in {"cursor.sh", "cursor.com", "cursorapi.com", "cursor-cdn.com"}:
        extras = {
            "cursor.sh": (
                "api2.cursor.sh",
                "api2direct.cursor.sh",
                "api2geo.cursor.sh",
                "api3.cursor.sh",
                "api4.cursor.sh",
                "api5.cursor.sh",
                "agent.api5.cursor.sh",
                "agentn.api5.cursor.sh",
                "agent.us.api5.cursor.sh",
                "agentn.us.api5.cursor.sh",
                "agent.global.api5.cursor.sh",
                "agentn.global.api5.cursor.sh",
                "grpc.cursor.sh",
                "auth.cursor.sh",
                "authenticate.cursor.sh",
                "authenticator.cursor.sh",
                "authentication.cursor.sh",
                "prod.authentication.cursor.sh",
                "metrics.cursor.sh",
                "repo42.cursor.sh",
            ),
            "cursor.com": (
                "www.cursor.com",
                "docs.cursor.com",
                "api.cursor.com",
                "downloads.cursor.com",
            ),
            "cursorapi.com": ("marketplace.cursorapi.com",),
            "cursor-cdn.com": ("www.cursor-cdn.com",),
        }
        found.update(extras.get(base, ()))

    return sorted(found)


def hosts_to_resolve(pattern: str, *, lists_dirs: list[str] | None = None) -> list[str]:
    clean = normalize_domain_pattern(pattern)
    if not clean:
        return []
    if clean.startswith("*."):
        return discover_hosts_for_base(clean[2:], lists_dirs=lists_dirs)
    hosts = [clean]
    if not clean.startswith("www."):
        hosts.append(f"www.{clean}")
    return hosts
