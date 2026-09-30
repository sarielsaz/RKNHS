"""Формат ключа RKNHS-L1 (совместим с license-generator)."""

from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone

LICENSE_PREFIX = "RKNHS-L1"
LICENSE_NAME_RE = re.compile(r"^[A-Za-zА-Яа-яЁё]{1,20}$")
PERPETUAL_EXP_TS = 0


@dataclass(frozen=True, slots=True)
class LicensePayload:
    name: str
    machine_id: str
    perpetual: bool = False
    expires_at: date | None = None

    def to_dict(self) -> dict:
        if self.perpetual:
            exp_ts = PERPETUAL_EXP_TS
        else:
            assert self.expires_at is not None
            exp_ts = int(
                datetime(
                    self.expires_at.year,
                    self.expires_at.month,
                    self.expires_at.day,
                    23,
                    59,
                    59,
                    tzinfo=timezone.utc,
                ).timestamp()
            )
        return {"v": 1, "n": self.name, "exp": exp_ts, "mid": self.machine_id}

    @staticmethod
    def from_dict(data: dict) -> LicensePayload:
        name = str(data.get("n") or "")
        exp_ts = int(data.get("exp") or 0)
        machine_id = str(data.get("mid") or "")
        perpetual = exp_ts == PERPETUAL_EXP_TS
        expires_at = None
        if not perpetual:
            expires_at = datetime.fromtimestamp(exp_ts, tz=timezone.utc).date()
        return LicensePayload(
            name=name,
            machine_id=machine_id,
            perpetual=perpetual,
            expires_at=expires_at,
        )


def canonical_payload_bytes(payload: LicensePayload) -> bytes:
    body = payload.to_dict()
    return json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8")


def decode_license_key(key: str) -> tuple[LicensePayload, bytes]:
    text = (key or "").strip()
    if not text.startswith(LICENSE_PREFIX + "."):
        raise ValueError("Неверный формат лицензионного ключа.")
    parts = text.split(".")
    if len(parts) != 3:
        raise ValueError("Неверный формат лицензионного ключа.")
    payload_raw = _b64_pad(parts[1])
    sig_raw = _b64_pad(parts[2])
    payload = LicensePayload.from_dict(json.loads(payload_raw.decode("utf-8")))
    return payload, sig_raw


def _b64_pad(value: str) -> bytes:
    pad = "=" * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode(value + pad)


__all__ = [
    "LICENSE_PREFIX",
    "PERPETUAL_EXP_TS",
    "LicensePayload",
    "canonical_payload_bytes",
    "decode_license_key",
]
