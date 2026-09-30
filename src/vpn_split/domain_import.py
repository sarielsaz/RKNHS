from __future__ import annotations

from vpn_split.domain_patterns import normalize_domain_pattern


def parse_domain_lines(text: str) -> list[str]:
    """Parse pasted/import lines. Supports plain hosts and *.parent.tld wildcards."""
    seen: set[str] = set()
    domains: list[str] = []
    for raw in str(text or "").splitlines():
        token = str(raw or "").strip()
        if not token or token.startswith("#"):
            continue
        # Allow comma-separated tokens on one line
        parts = token.replace(";", " ").replace(",", " ").split()
        for part in parts:
            clean = normalize_domain_pattern(part)
            if not clean or clean in seen:
                continue
            seen.add(clean)
            domains.append(clean)
    return domains
