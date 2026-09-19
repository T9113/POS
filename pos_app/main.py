import os
import sys

# Ensure root directory is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import customtkinter as ctk
from pos_app.config import APP_NAME, APP_VERSION
from pos_app.database import init_database
from pos_app.models.settings_model import SettingsModel
from pos_app.controllers.auth_controller import AuthController
from pos_app.views.theme import apply_theme
from pos_app.views.login_view import LoginView
from pos_app.views.main_window import MainWindow

class SwiftPOSApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Auto-create database and tables on first run
        init_database()

        # One-time desktop shortcut creation on first install / launch in background thread
        try:
            import threading
            from pos_app.utils.shortcut_helper import setup_first_run_shortcut
            threading.Thread(target=setup_first_run_shortcut, daemon=True).start()
        except Exception:
            pass

        # Load appearance theme from settings
        theme = SettingsModel.get("theme_mode", "dark")
        apply_theme(theme)

        self.title(f"{APP_NAME} v{APP_VERSION} - Offline Desktop POS")
        self.geometry("1280x780")
        self.minsize(1024, 640)

        # Center on screen
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max(0, (sw - 1280) // 2)
        y = max(0, (sh - 780) // 2)
        self.geometry(f"+{x}+{y}")

        self.current_view = None
        self._show_login()

    def _show_login(self):
        if self.current_view:
            self.current_view.destroy()
        self.current_view = LoginView(self, on_login_success=self._on_login_success)
        self.current_view.pack(fill="both", expand=True)

    def _on_login_success(self):
        if self.current_view:
            self.current_view.destroy()
        self.current_view = MainWindow(self, on_logout=self._show_login)
        self.current_view.pack(fill="both", expand=True)

def main():
    # Set Windows App ID for taskbar grouping
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(f"OnesDevPOS.App.{APP_VERSION}")
        except Exception:
            pass

    app = SwiftPOSApp()
    app.mainloop()

if __name__ == "__main__":
    main()
