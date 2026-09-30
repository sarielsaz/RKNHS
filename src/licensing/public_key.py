"""Встроенный публичный ключ Ed25519 (из license-generator/keys/verify.pub)."""

from __future__ import annotations

# 32 bytes Ed25519 public key — обновлять при смене пары ключей генератора.
LICENSE_VERIFY_PUBLIC_KEY_HEX = (
    "6a8f1be00908a46be4f01c058cca55a162f56a5e29110b6e707e419109a1d106"
)


def license_public_key_bytes() -> bytes:
    raw = bytes.fromhex(LICENSE_VERIFY_PUBLIC_KEY_HEX)
    if len(raw) != 32:
        raise ValueError("Некорректный публичный ключ лицензирования.")
    return raw


__all__ = ["LICENSE_VERIFY_PUBLIC_KEY_HEX", "license_public_key_bytes"]
