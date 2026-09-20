"""
Hardware-Locked Cryptographic Licensing & Anti-Piracy Engine for OnesDev POS.
Binds application execution to unique hardware metrics (Motherboard, BIOS, CPU, Drive, MachineGuid).
Verifies asymmetric Ed25519 digital signatures to prevent unauthorized duplication across PCs.
"""
import os
import sys
import json
import base64
import hashlib
import ctypes
import subprocess
from datetime import datetime
from typing import Tuple, Dict, Any, Optional

try:
    import winreg
except ImportError:
    winreg = None

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

from pos_app.models.settings_model import SettingsModel


# ==============================================================================
# MASTER PUBLIC KEY (Embedded in client app. The private key is held by vendor)
# ==============================================================================
ED25519_PUBLIC_KEY_HEX = "eb436a00fcea382c9e6d493633da55fd0af50bb88a03f29b0462414e727fcd1a"
SALT = "ONESDEV_POS_COMMERCIAL_SALT_K98X4"
REG_KEY_PATH = r"Software\OnesDevPOS"


class LicenseManager:
    """Manages hardware fingerprinting, signature verification, and license persistence."""

    _cached_machine_id: Optional[str] = None
    _cached_verification: Optional[Tuple[bool, str, Dict[str, Any]]] = None

    # --------------------------------------------------------------------------
    # 1. Hardware Fingerprinting (Multi-Source Windows Metrics)
    # --------------------------------------------------------------------------
    @classmethod
    def _get_registry_machine_guid(cls) -> str:
        """Reads Windows MachineGuid generated upon Windows OS installation."""
        if not winreg:
            return "NO_WINREG"
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography") as key:
                val, _ = winreg.QueryValueEx(key, "MachineGuid")
                return str(val).strip()
        except Exception:
            return "GUID_UNAVAILABLE"

    @classmethod
    def _get_volume_serial(cls) -> str:
        """Reads physical volume serial number of system drive C: via Win32 API."""
        try:
            vol_serial = ctypes.c_ulong()
            ctypes.windll.kernel32.GetVolumeInformationW(
                "C:\\", None, 0, ctypes.byref(vol_serial), None, None, None, 0
            )
            return f"{vol_serial.value:08X}"
        except Exception:
            return "VOL_UNAVAILABLE"

    @classmethod
    def _get_wmi_attribute(cls, cim_class: str, property_name: str) -> str:
        """Queries WMI/CIM hardware property using PowerShell CIM instance."""
        try:
            cmd = f"(Get-CimInstance -ClassName {cim_class} -ErrorAction SilentlyContinue).{property_name}"
            res = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
                capture_output=True, text=True, timeout=2
            )
            val = res.stdout.strip()
            return val if val else f"{property_name}_EMPTY"
        except Exception:
            return f"{property_name}_ERROR"

    @classmethod
    def get_machine_id(cls) -> str:
        """
        Calculates a deterministic, unique, salted 20-character Machine Hardware ID.
        Combines:
          1. BIOS / System UUID
          2. Motherboard Serial Number
          3. CPU Processor ID
          4. C: Drive Volume Serial Number
          5. Windows MachineGuid
        """
        if cls._cached_machine_id:
            return cls._cached_machine_id

        bios_uuid = cls._get_wmi_attribute("Win32_ComputerSystemProduct", "UUID")
        mb_serial = cls._get_wmi_attribute("Win32_BaseBoard", "SerialNumber")
        cpu_id = cls._get_wmi_attribute("Win32_Processor", "ProcessorId")
        vol_serial = cls._get_volume_serial()
        mach_guid = cls._get_registry_machine_guid()

        # Combine all 5 metrics with vendor salt
        composite = f"{bios_uuid}|{mb_serial}|{cpu_id}|{vol_serial}|{mach_guid}|{SALT}"
        digest = hashlib.sha256(composite.encode("utf-8")).hexdigest().upper()

        # Format into clean chunks: ONES-XXXX-XXXX-XXXX-XXXX (16 hex chars)
        chunk1 = digest[0:4]
        chunk2 = digest[4:8]
        chunk3 = digest[8:12]
        chunk4 = digest[12:16]

        cls._cached_machine_id = f"ONES-{chunk1}-{chunk2}-{chunk3}-{chunk4}"
        return cls._cached_machine_id

    # --------------------------------------------------------------------------
    # 2. Cryptographic Verification (Asymmetric Ed25519)
    # --------------------------------------------------------------------------
    @classmethod
    def verify_license(cls, license_key_str: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Cryptographically verifies the license key string using the embedded Ed25519 public key.
        Checks:
          1. Base64 formatting and payload structure.
          2. Digital signature authenticity.
          3. Match between signed 'hwid' and current live Machine ID.
          4. License expiration date (if not lifetime).
        """
        if not license_key_str or not license_key_str.strip():
            return False, "No license key provided.", {}

        clean_str = license_key_str.strip()
        # Remove header prefixes or newlines if any
        if clean_str.startswith("ONESDEV-LIC:"):
            clean_str = clean_str.replace("ONESDEV-LIC:", "")

        parts = clean_str.split(".")
        if len(parts) != 2:
            return False, "Malformed license key format.", {}

        try:
            payload_bytes = base64.b64decode(parts[0])
            signature_bytes = base64.b64decode(parts[1])
        except Exception:
            return False, "Invalid base64 encoding in license key.", {}

        # 1. Verify digital signature using Ed25519 Public Key
        try:
            pub_bytes = bytes.fromhex(ED25519_PUBLIC_KEY_HEX)
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
            public_key.verify(signature_bytes, payload_bytes)
        except InvalidSignature:
            return False, "Invalid cryptographic license signature. Key has been modified or forged.", {}
        except Exception as e:
            return False, f"Signature verification error: {str(e)}", {}

        # 2. Parse payload JSON
        try:
            payload = json.loads(payload_bytes.decode("utf-8"))
        except Exception:
            return False, "Unreadable license payload.", {}

        # 3. Check hardware binding (Cross-Machine Copy Protection)
        current_hwid = cls.get_machine_id()
        licensed_hwid = payload.get("hwid", "")

        if licensed_hwid != current_hwid:
            return False, f"Hardware ID mismatch! This license was generated for '{licensed_hwid}', but this PC is '{current_hwid}'. Copying the software to a new PC requires re-registration.", payload

        # 4. Check expiration date if applicable
        expiry = payload.get("expiry", "lifetime")
        if expiry and expiry != "lifetime":
            try:
                exp_date = datetime.strptime(expiry, "%Y-%m-%d").date()
                if datetime.now().date() > exp_date:
                    return False, f"License expired on {expiry}. Please contact OnesDev Support to renew.", payload
            except Exception:
                pass

        return True, "License valid and active.", payload

    # --------------------------------------------------------------------------
    # 3. Dual-Storage Persistence (Registry + SQLite + File)
    # --------------------------------------------------------------------------
    @classmethod
    def save_license(cls, license_key_str: str) -> bool:
        """Saves a verified license across Windows Registry, SQLite settings, and license.lic file."""
        clean_key = license_key_str.strip()

        # 1. Save in SQLite settings table
        try:
            SettingsModel.set("license_key", clean_key)
        except Exception:
            pass

        # 2. Save in Windows Registry (HKCU)
        if winreg:
            try:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH) as key:
                    winreg.SetValueEx(key, "LicenseKey", 0, winreg.REG_SZ, clean_key)
                    winreg.SetValueEx(key, "ActivatedAt", 0, winreg.REG_SZ, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            except Exception:
                pass

        # 3. Save to license.lic file next to database or executable
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            lic_path = os.path.join(base_dir, "license.lic")
            with open(lic_path, "w", encoding="utf-8") as f:
                f.write(clean_key)
        except Exception:
            pass

        # Reset verification cache
        cls._cached_verification = None
        return True

    @classmethod
    def load_license(cls) -> Optional[str]:
        """Loads stored license from Database, Windows Registry, or local license.lic file."""
        # 1. Try SQLite settings
        try:
            db_key = SettingsModel.get("license_key")
            if db_key and db_key.strip():
                return db_key.strip()
        except Exception:
            pass

        # 2. Try Windows Registry
        if winreg:
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH) as key:
                    val, _ = winreg.QueryValueEx(key, "LicenseKey")
                    if val and str(val).strip():
                        return str(val).strip()
            except Exception:
                pass

        # 3. Try local license.lic file
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            lic_path = os.path.join(base_dir, "license.lic")
            if os.path.exists(lic_path):
                with open(lic_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        return content
        except Exception:
            pass

        return None

    @classmethod
    def is_activated(cls) -> bool:
        """Dynamically evaluates if the current PC has a valid, active hardware-locked license."""
        if cls._cached_verification is not None:
            return cls._cached_verification[0]

        license_key = cls.load_license()
        if not license_key:
            cls._cached_verification = (False, "No license found.", {})
            return False

        valid, msg, payload = cls.verify_license(license_key)
        cls._cached_verification = (valid, msg, payload)
        return valid

    @classmethod
    def get_license_info(cls) -> Dict[str, Any]:
        """Returns registration metadata for UI display."""
        valid = cls.is_activated()
        _, _, payload = cls._cached_verification or (False, "", {})
        return {
            "is_activated": valid,
            "machine_id": cls.get_machine_id(),
            "client_name": payload.get("client", "Unregistered Trial / Evaluation"),
            "license_type": payload.get("type", "Lifetime Commercial"),
            "issued_date": payload.get("issued", "-"),
            "expiry": payload.get("expiry", "Lifetime")
        }
