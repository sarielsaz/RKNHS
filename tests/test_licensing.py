from __future__ import annotations

import unittest
from datetime import date

import base64

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from licensing.format import LICENSE_PREFIX, LicensePayload, canonical_payload_bytes, decode_license_key
from licensing.machine_id import fingerprint_to_machine_id
from licensing.public_key import LICENSE_VERIFY_PUBLIC_KEY_HEX


class LicensingFormatTests(unittest.TestCase):
    def test_perpetual_payload_roundtrip(self) -> None:
        payload = LicensePayload(
            name="TestUser",
            machine_id="a" * 64,
            perpetual=True,
        )
        raw = payload.to_dict()
        self.assertEqual(raw["exp"], 0)
        restored = LicensePayload.from_dict(raw)
        self.assertTrue(restored.perpetual)
        self.assertIsNone(restored.expires_at)

    def test_machine_id_stable(self) -> None:
        mid = fingerprint_to_machine_id("demo-fingerprint")
        self.assertEqual(len(mid), 64)
        self.assertEqual(mid, fingerprint_to_machine_id("demo-fingerprint"))


class LicensingSignatureTests(unittest.TestCase):
    def test_decode_and_verify_with_test_key(self) -> None:
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        payload = LicensePayload(
            name="Demo",
            machine_id=fingerprint_to_machine_id("unit-test"),
            perpetual=False,
            expires_at=date(2099, 12, 31),
        )
        signature = private_key.sign(canonical_payload_bytes(payload))
        payload_b64 = base64.urlsafe_b64encode(canonical_payload_bytes(payload)).decode("ascii").rstrip("=")
        sig_b64 = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")
        key = f"{LICENSE_PREFIX}.{payload_b64}.{sig_b64}"
        decoded, sig = decode_license_key(key)
        public_key.verify(sig, canonical_payload_bytes(decoded))
        self.assertEqual(decoded.name, "Demo")

    def test_embedded_public_key_length(self) -> None:
        self.assertEqual(len(bytes.fromhex(LICENSE_VERIFY_PUBLIC_KEY_HEX)), 32)


if __name__ == "__main__":
    unittest.main()
