# OnesDev POS - Deployment & Licensing Step-by-Step Guide

This guide documents the exact steps for deploying **OnesDev POS** to client computers, generating cryptographic hardware-locked licenses, and handling activations and copy protection.

---

## 1. Distribution: What to Give to Clients

When giving or selling the software to a customer, **only provide the compiled release folder**:

### Files to Give to the Customer:
Inside `d:\Cli\POS\dist\`:
* `OnesDevPOS.exe` (The standalone compiled application)
* `pos_data.db` (The SQLite database with pre-configured schema and categories)

*(Optional)* You can zip these two files together into `OnesDevPOS_Setup.zip` or create a desktop shortcut pointing to `OnesDevPOS.exe`.

### Files to NEVER Give to Clients:
* `tools/generate_license.py` *(Contains your private master signing key — keep strictly on your computer!)*
* Source code files (`pos_app/`, `tests/`, etc.)
* `.git/` repository files

---

## 2. Default Login Credentials

Once the software is activated, the default users configured in the database are:

| Role | Username | Default Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin` | Full system access: Sales, Inventory, Reports, Users, Settings, Database Backups |
| **Cashier** | `cashier` | `cashier` | Sales POS terminal, Customer management, Order history |

> **Tip**: Admins can change their passwords or add new staff members at any time in **Users Management**.

---

## 3. First-Time Client Installation Workflow

When the client installs or launches `OnesDevPOS.exe` for the first time on their PC:

```
[ Customer PC ]                         [ Your PC (Vendor) ]
      │                                          │
      ├─ 1. Opens OnesDevPOS.exe                 │
      ├─ 2. Sees "Software Activation Required"  │
      ├─ 3. Clicks "Copy ID" (e.g. ONES-XXXX)    │
      │                                          │
      ├─────────── Sends Machine ID ────────────>│
      │                                          ├─ 4. Runs: python tools/generate_license.py
      │                                          ├─ 5. Generates signed key
      │<────────── Sends License Key ────────────┤
      │                                          │
      ├─ 6. Pastes Key & Clicks "Activate"       │
      └─ 7. POS Unlocks & Opens Login Window     │
```

### Detailed Steps:

### Step 1: Customer opens the application
The customer double-clicks `OnesDevPOS.exe`. Because it is their first time running it on this machine, the app automatically displays the **Software Activation** window.

### Step 2: Customer copies their Machine ID
The customer sees their unique 20-character hardware identifier:
```text
Machine ID: ONES-E7A6-CF01-60FC-C5FC
```
The customer clicks the **"Copy ID"** button and sends this string to you via WhatsApp, Email, or SMS.

### Step 3: You generate their License Key (on your PC)
Open PowerShell or Command Prompt on **your** computer inside `d:\Cli\POS`:

#### Option A: Quick Command Line (Recommended)
```powershell
python tools/generate_license.py --hwid "ONES-E7A6-CF01-60FC-C5FC" --client "Al-Madina Superstore"
```

#### Option B: Interactive Mode
```powershell
python tools/generate_license.py
```
*(The tool will interactively prompt you for Store Name, Machine ID, and Expiry).*

#### Option C: Time-Limited / Subscription License (Optional)
If you want to grant a 1-year license instead of lifetime:
```powershell
python tools/generate_license.py --hwid "ONES-E7A6-CF01-60FC-C5FC" --client "Al-Madina Superstore" --expiry 2027-12-31
```

### Step 4: Send the Key to the Customer
The generator outputs the signed key:
```text
>>> OFFICIAL LICENSE KEY (SEND THIS TO CUSTOMER):
eyJod2lkIjoiT05FUy1FN0E2LUNGMDEtNjBGQy1DNUZDIiwiY2xpZW50IjoiQWwtTWFkaW5hIFN1cGVyc3RvcmUiLCJ0eXBlIjoiTGlmZXRpbWUgQ29tbWVyY2lhbCIsImlzc3VlZCI6IjIwMjYtMDktMjAiLCJleHBpcnkiOiJsaWZldGltZSJ9./vS8IfnNXKgyH4ajoHD3W7irYTBpAMaiq+tCk2L45CzkO/NvT6+/8Hot3xFWb+SMl9tfepf6HgjPQ3dBIF/NAw==
```
Copy and send this text to the customer (or send the generated `license.lic` file).

### Step 5: Customer activates the app
1. The customer pastes the key into the activation box (or clicks **"Load .lic File"**).
2. The customer clicks **"Activate License"**.
3. A success message appears: *"License successfully activated for [Store Name]!"*
4. The activation screen closes and the **Login Screen** appears immediately.

---

## 4. Copy-Protection: What Happens if Copied to a New PC?

If the customer (or anyone else) attempts to:
* Copy the `OnesDevPOS.exe` to a different PC
* Copy the entire folder or the `pos_data.db` database to a USB drive and paste it onto another computer

### The Result:
1. When launched on PC #2, OnesDev POS scans the new computer's hardware (BIOS UUID, Motherboard Serial, CPU Processor ID, C: Drive Volume Serial, Windows Machine GUID).
2. The hardware metrics on PC #2 generate a completely different Machine ID.
3. The app checks the stored license and calculates:
   $$\text{Stored License HWID} \neq \text{New PC HWID}$$
4. The app detects a **Hardware Mismatch Error**, rejects the license, clears the unauthorized cache, and **locks down immediately**.
5. The **Software Activation** window reappears, demanding a valid license specifically generated for PC #2.

---

## 5. Security & Anti-Bypass Architecture

The licensing system was built to prevent common cracks and bypasses:

1. **No Database Flags**:
   The app does *not* rely on a simple `is_registered = 1` row in SQLite. Even if an attacker opens SQLite and changes settings, the application ignores it. On every launch, it dynamically computes live hardware metrics and verifies the mathematical digital signature.
2. **Asymmetric Ed25519 Cryptography**:
   - The customer's executable only contains the **Public Key**.
   - The **Private Signing Key** remains solely on your development machine.
   - It is mathematically impossible for an attacker to generate or forge a valid license key, even if they reverse-engineer or decompile the client software.
3. **Dual Persistence**:
   Valid licenses are safely stored in both the Windows Registry (`HKCU\Software\OnesDevPOS`) and the local database settings table, ensuring the user doesn't need to re-enter their key on every restart.

---

## 6. How to Recompile the Software (Future Updates)

If you modify the Python code in the future and want to build a new `.exe`:

1. Open PowerShell in `d:\Cli\POS`.
2. Run the build script:
   ```powershell
   python build_exe.py
   ```
3. The fresh executable will be generated at:
   ```text
   d:\Cli\POS\dist\OnesDevPOS.exe
   ```
4. Copy `dist/OnesDevPOS.exe` to your customer. Their existing license and database will continue to work seamlessly!
