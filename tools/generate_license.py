"""
OnesDev POS - Private Vendor License Key Generator Tool.
STRICTLY FOR VENDOR / DEVELOPER USE ONLY. DO NOT DISTRIBUTE TO CLIENTS.
Uses the Master Ed25519 Private Key to generate tamper-resistant hardware-locked licenses.
"""
import sys
import os
import json
import base64
import argparse
from datetime import datetime

from cryptography.hazmat.primitives.asymmetric import ed25519

# Master Ed25519 Private Key (Kept solely on developer's machine)
PRIVATE_KEY_HEX = "d79687431930fe61a118319757364e0016b8a642e29c58dacc1b5a2d82287920"


def generate_license(hwid: str, client_name: str, expiry: str = "lifetime", license_type: str = "Lifetime Commercial") -> str:
    """Signs a hardware ID and client payload using the master Ed25519 private key."""
    hwid = hwid.strip().upper()
    client_name = client_name.strip()
    expiry = expiry.strip() if expiry else "lifetime"

    payload_dict = {
        "hwid": hwid,
        "client": client_name,
        "type": license_type,
        "issued": datetime.now().strftime("%Y-%m-%d"),
        "expiry": expiry
    }

    payload_bytes = json.dumps(payload_dict, separators=(",", ":")).encode("utf-8")

    # Load master private key and compute Ed25519 digital signature
    priv_bytes = bytes.fromhex(PRIVATE_KEY_HEX)
    private_key = ed25519.Ed25519PrivateKey.from_private_bytes(priv_bytes)
    signature_bytes = private_key.sign(payload_bytes)

    # Combine into clean base64 token: PAYLOAD.SIGNATURE
    b64_payload = base64.b64encode(payload_bytes).decode("utf-8")
    b64_sig = base64.b64encode(signature_bytes).decode("utf-8")

    license_key = f"{b64_payload}.{b64_sig}"
    return license_key


def main():
    parser = argparse.ArgumentParser(description="Generate Hardware-Locked License Keys for OnesDev POS")
    parser.add_argument("--hwid", help="Client Machine ID (e.g. ONES-XXXX-XXXX-XXXX-XXXX)")
    parser.add_argument("--client", help="Client / Store Name (e.g. Al-Madina Superstore)")
    parser.add_argument("--expiry", default="lifetime", help="Expiry date (YYYY-MM-DD) or 'lifetime'")
    parser.add_argument("--out", help="Optional output path to save license.lic file")

    args = parser.parse_args()

    print("\n" + "=" * 65)
    print("        OnesDev POS - Master License Key Generator")
    print("=" * 65)

    hwid = args.hwid
    client = args.client
    expiry = args.expiry

    if not hwid or not client:
        print("\n[*] Please provide customer activation details:\n")
        if not client:
            client = input("Enter Client / Store Name: ").strip()
        if not hwid:
            hwid = input("Enter Customer Machine ID (e.g. ONES-7B2F-9A4E-C810-D35F): ").strip()
        exp_input = input("Enter Expiry (Press Enter for 'lifetime' or YYYY-MM-DD): ").strip()
        if exp_input:
            expiry = exp_input

    if not hwid or not client:
        print("\n[ERROR] Both Machine ID and Client Name are required!")
        sys.exit(1)

    lic_key = generate_license(hwid, client, expiry)

    print("\n" + "-" * 65)
    print(" [OK] LICENSE GENERATED SUCCESSFULLY!")
    print("-" * 65)
    print(f" Client:     {client}")
    print(f" Machine ID: {hwid}")
    print(f" Expiry:     {expiry}")
    print(f" Issued:     {datetime.now().strftime('%Y-%m-%d')}")
    print("-" * 65)
    print("\n>>> OFFICIAL LICENSE KEY (SEND THIS TO CUSTOMER):\n")
    print(lic_key)
    print("\n" + "-" * 65)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(lic_key)
        print(f"Saved license file to: {args.out}\n")
    else:
        save_file = input("Save to 'license.lic' file? (y/N): ").strip().lower()
        if save_file == "y":
            out_file = "license.lic"
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(lic_key)
            print(f"Saved to: {os.path.abspath(out_file)}\n")


if __name__ == "__main__":
    main()
