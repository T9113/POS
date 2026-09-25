import os
import sys
import subprocess

def build():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)

    # Terminate running POS instances to release file locks on Windows
    if sys.platform == "win32":
        try:
            subprocess.run(["powershell", "-Command", "Stop-Process -Name 'OnesDevPOS*','SwiftPOS*' -Force -ErrorAction SilentlyContinue"], capture_output=True, timeout=5)
        except Exception:
            pass

    assets_dir = os.path.join(base_dir, "pos_app", "assets")
    icon_path = os.path.join(base_dir, "app_icon.ico")

    # Target output
    dist_dir = os.path.join(base_dir, "dist")
    build_dir = os.path.join(base_dir, "build")

    print("==================================================")
    print("       Building OnesDev POS Standalone Executable ")
    print("==================================================")
    print(f"Base Directory: {base_dir}")
    print(f"Icon Path: {icon_path}")

    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name=OnesDevPOS",
    ]

    if os.path.exists(icon_path):
        pyinstaller_cmd.append(f"--icon={icon_path}")

    if os.path.exists(assets_dir):
        pyinstaller_cmd.append(f"--add-data={assets_dir};assets")

    pyinstaller_cmd.extend([
        "--hidden-import=PySide6",
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtSvg",
        "--hidden-import=cryptography",
        "--hidden-import=cryptography.hazmat.primitives.asymmetric.ed25519",
        "--hidden-import=openpyxl",
        "--hidden-import=reportlab",
        "--hidden-import=win32print",
        "--hidden-import=win32com",
        "--hidden-import=win32com.client",
        "--hidden-import=sqlite3",
        os.path.join(base_dir, "pos_app", "main.py")
    ])

    print("\nRunning PyInstaller build command:")
    print(" ".join(pyinstaller_cmd))

    ret = subprocess.call(pyinstaller_cmd)
    if ret != 0:
        print("\n[ERROR] Build failed with error code:", ret)
        return False

    exe_path = os.path.join(dist_dir, "OnesDevPOS.exe")
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)

        # Sync pristine demo database next to the executable
        root_db = os.path.join(base_dir, "pos_data.db")
        dist_db = os.path.join(dist_dir, "pos_data.db")
        if os.path.exists(root_db):
            import shutil
            shutil.copy2(root_db, dist_db)
            print(f" [DATABASE] Synced pristine demo database to: {dist_db}")

        # Sync license.lic if present
        root_lic = os.path.join(base_dir, "license.lic")
        app_lic = os.path.join(base_dir, "pos_app", "license.lic")
        dist_lic = os.path.join(dist_dir, "license.lic")
        import shutil
        if os.path.exists(root_lic):
            shutil.copy2(root_lic, dist_lic)
            print(f" [LICENSE] Synced license file to: {dist_lic}")
        elif os.path.exists(app_lic):
            shutil.copy2(app_lic, dist_lic)
            print(f" [LICENSE] Synced license file to: {dist_lic}")

        print("\n==================================================")
        print(" [SUCCESS] OnesDevPOS.exe built successfully!")
        print(f" Executable Path: {exe_path}")
        print(f" File Size: {size_mb:.2f} MB (Hardware-accelerated Qt6)")
        print("==================================================")
        return True
    else:
        print("\n[ERROR] Executable not found in dist folder.")
        return False

if __name__ == "__main__":
    success = build()
    sys.exit(0 if success else 1)
