import os
import shutil
from datetime import datetime
from pos_app.config import DB_PATH, BACKUPS_DIR
from pos_app.models.settings_model import SettingsModel
from pos_app.models.activity_model import ActivityModel
from pos_app.controllers.auth_controller import AuthController

class SettingsController:
    @staticmethod
    def get_all_settings():
        return SettingsModel.get_all()

    @staticmethod
    def save_settings(settings_dict: dict) -> tuple[bool, str]:
        SettingsModel.update_many(settings_dict)
        user = AuthController.get_current_user()
        user_id = user["id"] if user else None
        ActivityModel.log(user_id, "SETTINGS_CHANGE", "Updated application settings")
        return True, "Settings saved successfully"

    @staticmethod
    def backup_database(destination_dir: str = None) -> tuple[bool, str]:
        target_dir = destination_dir or BACKUPS_DIR
        os.makedirs(target_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"pos_backup_{timestamp}.db"
        dest_file = os.path.join(target_dir, backup_filename)

        try:
            # Use SQLite backup API for clean lockless atomic backup
            import sqlite3
            source_conn = sqlite3.connect(DB_PATH)
            dest_conn = sqlite3.connect(dest_file)
            with dest_conn:
                source_conn.backup(dest_conn)
            source_conn.close()
            dest_conn.close()

            user = AuthController.get_current_user()
            user_id = user["id"] if user else None
            ActivityModel.log(user_id, "BACKUP", f"Database backed up to {backup_filename}")
            return True, f"Backup created successfully: {dest_file}"
        except Exception as e:
            return False, f"Failed to backup database: {e}"

    @staticmethod
    def restore_database(backup_file_path: str) -> tuple[bool, str]:
        if not os.path.exists(backup_file_path):
            return False, "Backup file does not exist"

        try:
            # First create a safety backup of current db
            safety_backup = DB_PATH + ".safety_bak"
            shutil.copy2(DB_PATH, safety_backup)

            shutil.copy2(backup_file_path, DB_PATH)
            user = AuthController.get_current_user()
            user_id = user["id"] if user else None
            ActivityModel.log(user_id, "RESTORE", f"Database restored from {os.path.basename(backup_file_path)}")
            return True, "Database restored successfully. Please restart the application."
        except Exception as e:
            return False, f"Failed to restore database: {e}"

    @staticmethod
    def clear_sales_history() -> tuple[bool, str]:
        try:
            SettingsModel.clear_sales_data()
            user = AuthController.get_current_user()
            user_id = user["id"] if user else None
            ActivityModel.log(user_id, "DATA_RESET", "Cleared all sales history while preserving catalog")
            return True, "All sales history and orders cleared successfully."
        except Exception as e:
            return False, f"Failed to clear sales: {e}"

    @staticmethod
    def factory_reset() -> tuple[bool, str]:
        try:
            SettingsModel.factory_reset()
            return True, "System reset to factory defaults. Please login with admin/admin."
        except Exception as e:
            return False, f"Factory reset failed: {e}"
