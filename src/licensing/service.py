"""Активация и проверка лицензии в RKNHS."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from licensing.format import LicensePayload, canonical_payload_bytes, decode_license_key
from licensing.machine_id import get_local_machine_id, normalize_machine_id
from licensing.public_key import license_public_key_bytes
from settings.store import clear_license_record, get_license_record, set_license_record


@dataclass(frozen=True, slots=True)
class LicenseStatus:
    valid: bool
    name: str
    perpetual: bool
    expires_at: date | None
    machine_id: str
    message: str

    @property
    def expiry_label(self) -> str:
        if self.perpetual:
            return "бессрочно"
        if self.expires_at is None:
            return "—"
        return self.expires_at.strftime("%d.%m.%Y")


def _public_key() -> Ed25519PublicKey:
    return Ed25519PublicKey.from_public_bytes(license_public_key_bytes())


def _verify_signature(payload: LicensePayload, signature: bytes) -> bool:
    try:
        _public_key().verify(signature, canonical_payload_bytes(payload))
        return True
    except Exception:
        return False


def _is_expired(payload: LicensePayload, *, now: date | None = None) -> bool:
    if payload.perpetual or payload.expires_at is None:
        return False
    today = now or datetime.now(timezone.utc).date()
    return today > payload.expires_at


def evaluate_license_key(key: str, *, local_machine_id: str | None = None) -> LicenseStatus:
    local_mid = normalize_machine_id(local_machine_id or get_local_machine_id())
    try:
        payload, signature = decode_license_key(key)
    except Exception as exc:
        return LicenseStatus(
            valid=False,
            name="",
            perpetual=False,
            expires_at=None,
            machine_id=local_mid,
            message=str(exc),
        )

    if not _verify_signature(payload, signature):
        return LicenseStatus(
            valid=False,
            name=payload.name,
            perpetual=payload.perpetual,
            expires_at=payload.expires_at,
            machine_id=local_mid,
            message="Подпись лицензии недействительна.",
        )

    if payload.machine_id != local_mid:
        return LicenseStatus(
            valid=False,
            name=payload.name,
            perpetual=payload.perpetual,
            expires_at=payload.expires_at,
            machine_id=local_mid,
            message="Ключ выпущен для другого устройства.",
        )

    if _is_expired(payload):
        return LicenseStatus(
            valid=False,
            name=payload.name,
            perpetual=False,
            expires_at=payload.expires_at,
            machine_id=local_mid,
            message="Срок действия лицензии истёк.",
        )

    return LicenseStatus(
        valid=True,
        name=payload.name,
        perpetual=payload.perpetual,
        expires_at=payload.expires_at,
        machine_id=local_mid,
        message="Лицензия активна.",
    )


def activate_license_key(key: str) -> LicenseStatus:
    status = evaluate_license_key(key)
    if not status.valid:
        return status
    set_license_record(
        key=key.strip(),
        name=status.name,
        perpetual=status.perpetual,
        expires_at=status.expires_at.isoformat() if status.expires_at else None,
        machine_id=status.machine_id,
    )
    return status


def deactivate_license() -> None:
    clear_license_record()


def get_current_license_status() -> LicenseStatus:
    record = get_license_record()
    key = str(record.get("key") or "").strip()
    if not key:
        return LicenseStatus(
            valid=False,
            name="",
            perpetual=False,
            expires_at=None,
            machine_id=get_local_machine_id(),
            message="Лицензия не активирована.",
        )
    return evaluate_license_key(key)


def is_license_valid() -> bool:
    return get_current_license_status().valid


__all__ = [
    "LicenseStatus",
    "activate_license_key",
    "deactivate_license",
    "evaluate_license_key",
    "get_current_license_status",
    "get_local_machine_id",
    "is_license_valid",
]
