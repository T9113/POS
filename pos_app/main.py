"""
Entry point for OnesDev POS Desktop Application.
Hardware-accelerated PySide6 engine with iPhone-smooth animations,
frameless zero-glitch startup, and 100% offline portable SQLite database.
Enforces hardware-locked cryptographic registration and copy protection.
"""
import os
import sys
import threading

# Ensure root directory is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from pos_app.config import APP_NAME, APP_VERSION
from pos_app.database import init_database
from pos_app.qt_theme import GLOBAL_QSS
from pos_app.utils.license_manager import LicenseManager
from pos_app.views.qt_registration_dialog import QtRegistrationWindow
from pos_app.views.qt_login_view import QtLoginWindow
from pos_app.views.qt_main_window import QtMainWindow


class OnesDevPOSApplication:
    """Application controller coordinating registration, authentication, and main window transitions."""

    def __init__(self, app: QApplication):
        self.app = app
        self.reg_window = None
        self.login_window = None
        self.main_window = None

        # 1. Initialize local SQLite tables and default data
        init_database()

        # 2. Setup one-time desktop shortcut in background daemon thread
        try:
            from pos_app.utils.shortcut_helper import setup_first_run_shortcut
            threading.Thread(target=setup_first_run_shortcut, daemon=True).start()
        except Exception:
            pass

        # 3. Apply global hardware-accelerated stylesheet
        self.app.setStyleSheet(GLOBAL_QSS)

        # 4. Check hardware-locked license activation
        if not LicenseManager.is_activated():
            self.show_registration()
        else:
            self.show_login()

    def show_registration(self):
        """Displays hardware-locked registration screen if not registered or copied to new PC."""
        if self.main_window:
            self.main_window.close()
            self.main_window = None
        if self.login_window:
            self.login_window.close()
            self.login_window = None

        self.reg_window = QtRegistrationWindow()
        self.reg_window.activation_successful.connect(self._on_activated)
        self.reg_window.show()

    def _on_activated(self, payload: dict):
        if self.reg_window:
            self.reg_window = None
        self.show_login()

    def show_login(self):
        """Displays login screen if license is valid for this machine."""
        if not LicenseManager.is_activated():
            self.show_registration()
            return

        if self.main_window:
            self.main_window.close()
            self.main_window = None
        if self.reg_window:
            self.reg_window.close()
            self.reg_window = None

        self.login_window = QtLoginWindow(on_login_success=self.show_main_app)
        self.login_window.show()

    def show_main_app(self):
        """Launches primary POS application shell."""
        if not LicenseManager.is_activated():
            self.show_registration()
            return

        if self.login_window:
            self.login_window.close()
            self.login_window = None

        self.main_window = QtMainWindow(on_logout=self.show_login)
        self.main_window.show()


def main():
    # Set Windows App ID for proper taskbar grouping
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(f"OnesDevPOS.App.{APP_VERSION}")
        except Exception:
            pass

    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("OnesDev POS")
    app.setApplicationVersion(APP_VERSION)

    pos_app = OnesDevPOSApplication(app)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
