"""Отпечаток устройства для привязки лицензии."""

from __future__ import annotations

import hashlib
import platform
import subprocess
import uuid


def _pepper() -> bytes:
    return bytes((0x7A, 0x65, 0x72, 0x6F))


def collect_windows_fingerprint() -> str:
    chunks: list[str] = []

    if platform.system().lower() != "windows":
        chunks.append(platform.node().lower())
        chunks.append(str(uuid.getnode()))
        return "|".join(chunks)

    try:
        out = subprocess.check_output(
            ["wmic", "csproduct", "get", "uuid"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=8,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        for line in out.splitlines():
            line = line.strip()
            if line and line.lower() != "uuid":
                chunks.append(line)
    except Exception:
        pass

    try:
        out = subprocess.check_output(
            ["wmic", "diskdrive", "get", "serialnumber"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=8,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        serials = [ln.strip() for ln in out.splitlines() if ln.strip() and "serial" not in ln.lower()]
        if serials:
            chunks.append(serials[0])
    except Exception:
        pass

    chunks.append(str(uuid.getnode()))
    chunks.append(platform.node().lower())
    return "|".join(chunks)


def fingerprint_to_machine_id(raw_fingerprint: str) -> str:
    material = (raw_fingerprint.strip().lower() + "|").encode("utf-8") + _pepper()
    return hashlib.sha256(material).hexdigest()


def get_local_machine_id() -> str:
    return fingerprint_to_machine_id(collect_windows_fingerprint())


def normalize_machine_id(value: str) -> str:
    cleaned = value.strip().lower()
    if len(cleaned) != 64 or any(c not in "0123456789abcdef" for c in cleaned):
        raise ValueError("Некорректный отпечаток устройства.")
    return cleaned


__all__ = [
    "collect_windows_fingerprint",
    "fingerprint_to_machine_id",
    "get_local_machine_id",
    "normalize_machine_id",
]
