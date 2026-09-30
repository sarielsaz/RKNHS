"""Split-tunnel VPN (AmneziaWG) integration alongside winws2 DPI bypass."""

from vpn_split.sync import apply_vpn_split_sync, resolve_domain_rule

__all__ = ["apply_vpn_split_sync", "resolve_domain_rule"]
