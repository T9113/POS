"""
Unit and Integration Tests for Hardware-Locked Licensing and Anti-Piracy System.
Verifies cryptographic signature validation, hardware ID calculation,
copy protection mismatch detection, and tamper resistance.
"""
import unittest
import os
import sys

# Ensure root directory is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from pos_app.utils.license_manager import LicenseManager
from tools.generate_license import generate_license


class TestHardwareLicensing(unittest.TestCase):
    """Test suite verifying anti-piracy and hardware-locked license activation."""

    def setUp(self):
        self.current_hwid = LicenseManager.get_machine_id()

    def test_machine_id_format(self):
        """Hardware ID must be a non-empty, 20-character string formatted as ONES-XXXX-XXXX-XXXX-XXXX."""
        self.assertTrue(self.current_hwid.startswith("ONES-"))
        parts = self.current_hwid.split("-")
        self.assertEqual(len(parts), 5, "Hardware ID should have 5 hyphen-separated segments")
        for p in parts[1:]:
            self.assertEqual(len(p), 4, "Each chunk should be 4 hex characters")

    def test_valid_license_activation(self):
        """A cryptographic license signed for the current machine must verify successfully."""
        client_name = "SuperMart Commercial"
        key = generate_license(self.current_hwid, client_name, expiry="lifetime")
        
        valid, msg, payload = LicenseManager.verify_license(key)
        self.assertTrue(valid, f"Valid key failed verification: {msg}")
        self.assertEqual(payload.get("client"), client_name)
        self.assertEqual(payload.get("hwid"), self.current_hwid)
        self.assertEqual(payload.get("expiry"), "lifetime")

    def test_cross_machine_copy_protection(self):
        """Simulate copying database / executable to another computer. Must detect mismatch and lock."""
        different_machine_hwid = "ONES-1111-2222-3333-4444"
        copied_key = generate_license(different_machine_hwid, "Stolen / Copied Instance")

        valid, msg, _ = LicenseManager.verify_license(copied_key)
        self.assertFalse(valid, "License from a different machine should NOT be valid on this PC")
        self.assertIn("mismatch", msg.lower(), "Should explain hardware mismatch")

    def test_tamper_resistance_payload(self):
        """Modifying any character in the license payload must invalidate signature."""
        key = generate_license(self.current_hwid, "Valid Store")
        parts = key.split(".")
        # Corrupt the first character of the payload
        corrupted_payload = ("A" if parts[0][0] != "A" else "B") + parts[0][1:]
        tampered_key = f"{corrupted_payload}.{parts[1]}"

        valid, msg, _ = LicenseManager.verify_license(tampered_key)
        self.assertFalse(valid, "Tampered payload should fail verification")

    def test_tamper_resistance_signature(self):
        """Modifying any character in the cryptographic signature must fail."""
        key = generate_license(self.current_hwid, "Valid Store")
        parts = key.split(".")
        corrupted_sig = parts[1][:-2] + "99"
        tampered_key = f"{parts[0]}.{corrupted_sig}"

        valid, msg, _ = LicenseManager.verify_license(tampered_key)
        self.assertFalse(valid, "Tampered signature should fail verification")

    def test_expired_license(self):
        """A license with an expiry date in the past must be rejected."""
        past_date = "2020-01-01"
        expired_key = generate_license(self.current_hwid, "Expired Client", expiry=past_date)

        valid, msg, _ = LicenseManager.verify_license(expired_key)
        self.assertFalse(valid, "Expired license must be rejected")
        self.assertIn("expired", msg.lower())

    def test_save_and_load_persistence(self):
        """Saving and loading license key must persist and set is_activated to True."""
        key = generate_license(self.current_hwid, "Persistent Client Store")
        saved = LicenseManager.save_license(key)
        self.assertTrue(saved)

        loaded_key = LicenseManager.load_license()
        self.assertEqual(loaded_key, key)
        self.assertTrue(LicenseManager.is_activated())


if __name__ == "__main__":
    unittest.main()
