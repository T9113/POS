import os
import sys
import subprocess
import customtkinter

def build():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)

    # Locate customtkinter package directory for bundling its json themes and assets
    ctk_dir = customtkinter.__path__[0]
    assets_dir = os.path.join(base_dir, "pos_app", "assets")
    icon_path = os.path.join(base_dir, "app_icon.ico")

    # Target output
    dist_dir = os.path.join(base_dir, "dist")
    build_dir = os.path.join(base_dir, "build")

    print("==================================================")
    print("       Building OnesDev POS Standalone Executable ")
    print("==================================================")
    print(f"Base Directory: {base_dir}")
    print(f"CustomTkinter Dir: {ctk_dir}")
    print(f"Icon Path: {icon_path}")

    # Separator for PyInstaller --add-data on Windows is ';'
    add_data_ctk = f"{ctk_dir};customtkinter"
    add_data_assets = f"{assets_dir};assets"

    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name=OnesDevPOS",
        f"--icon={icon_path}",
        f"--add-data={add_data_ctk}",
        f"--add-data={add_data_assets}",
        "--hidden-import=customtkinter",
        "--hidden-import=PIL",
        "--hidden-import=PIL._tkinter_finder",
        "--hidden-import=openpyxl",
        "--hidden-import=reportlab",
        "--hidden-import=win32print",
        "--hidden-import=win32com",
        "--hidden-import=win32com.client",
        "--hidden-import=sqlite3",
        os.path.join(base_dir, "pos_app", "main.py")
    ]

    print("\nRunning PyInstaller build command:")
    print(" ".join(pyinstaller_cmd))

    ret = subprocess.call(pyinstaller_cmd)
    if ret != 0:
        print("\n❌ Build failed with error code:", ret)
        return False

    exe_path = os.path.join(dist_dir, "OnesDevPOS.exe")
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print("\n==================================================")
        print(" [SUCCESS] OnesDevPOS.exe built successfully!")
        print(f" Executable Path: {exe_path}")
        print(f" File Size: {size_mb:.2f} MB (Under 50MB limit!)")
        print("==================================================")
        return True
    else:
        print("\n❌ Executable not found in dist folder.")
        return False

if __name__ == "__main__":
    success = build()
    sys.exit(0 if success else 1)
