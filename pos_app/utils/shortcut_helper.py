import os
import sys
import subprocess

def get_target_executable() -> tuple[str, str, str]:
    """Returns (target_path, working_dir, icon_path) for desktop shortcut."""
    if getattr(sys, "frozen", False):
        exe_path = os.path.abspath(sys.executable)
        working_dir = os.path.dirname(exe_path)
        icon_path = exe_path
    else:
        # Development mode
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        exe_path = os.path.abspath(sys.argv[0])
        working_dir = base_dir
        candidate_icon = os.path.join(base_dir, "app_icon.ico")
        icon_path = candidate_icon if os.path.exists(candidate_icon) else exe_path

    return exe_path, working_dir, icon_path

def create_desktop_shortcut(name: str = "OnesDev POS.lnk") -> tuple[bool, str]:
    """Creates a Windows Desktop shortcut pointing to the application executable."""
    try:
        user_profile = os.environ.get("USERPROFILE") or os.path.expanduser("~")
        desktop_dir = os.path.join(user_profile, "Desktop")
        if not os.path.exists(desktop_dir):
            os.makedirs(desktop_dir, exist_ok=True)

        shortcut_path = os.path.join(desktop_dir, name)
        exe_path, working_dir, icon_path = get_target_executable()

        # Try Method 1: win32com.client
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.TargetPath = exe_path
            shortcut.WorkingDirectory = working_dir
            shortcut.Description = "OnesDev POS - Desktop Point of Sale"
            if icon_path and os.path.exists(icon_path):
                shortcut.IconLocation = f"{icon_path},0"
            shortcut.Save()
            if os.path.exists(shortcut_path):
                return True, shortcut_path
        except Exception:
            pass

        # Try Method 2: Native Windows VBScript fallback
        vbs_script = os.path.join(working_dir, "_make_shortcut_temp.vbs")
        vbs_code = f'''Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{shortcut_path}"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{exe_path}"
oLink.WorkingDirectory = "{working_dir}"
oLink.Description = "OnesDev POS - Desktop Point of Sale"
oLink.Save
'''
        with open(vbs_script, "w", encoding="utf-8") as f:
            f.write(vbs_code)

        cflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        subprocess.run(["cscript", "//nologo", vbs_script], check=True, capture_output=True, timeout=3, creationflags=cflags)
        if os.path.exists(vbs_script):
            try:
                os.remove(vbs_script)
            except OSError:
                pass

        if os.path.exists(shortcut_path):
            return True, shortcut_path

        return False, "Failed to create shortcut file."
    except Exception as e:
        return False, str(e)

def setup_first_run_shortcut():
    """Checks if shortcut creation has run on first install/launch and creates it once."""
    from pos_app.models.settings_model import SettingsModel
    already_created = SettingsModel.get("desktop_shortcut_created", "0")
    if already_created != "1":
        ok, _ = create_desktop_shortcut()
        if ok:
            SettingsModel.set("desktop_shortcut_created", "1")
        return ok
    return True
