from pos_app.database import get_db, init_database
from pos_app.utils.security import hash_password

class SettingsModel:
    @staticmethod
    def get(key: str, default=None):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else default

    @staticmethod
    def get_all():
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM settings")
            return {row["key"]: row["value"] for row in cursor.fetchall()}

    @staticmethod
    def set(key: str, value: str):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (key, str(value)))

    @staticmethod
    def update_many(settings_dict: dict):
        with get_db() as conn:
            cursor = conn.cursor()
            for key, val in settings_dict.items():
                cursor.execute("""
                    INSERT INTO settings (key, value) VALUES (?, ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """, (key, str(val)))

    @staticmethod
    def clear_sales_data():
        """Clears all orders, returns, held orders, and expenses while preserving products, categories, customers, and users."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM order_items")
            cursor.execute("DELETE FROM orders")
            cursor.execute("DELETE FROM returns")
            cursor.execute("DELETE FROM held_orders")
            cursor.execute("DELETE FROM stock_adjustments")
            cursor.execute("DELETE FROM purchase_items")
            cursor.execute("DELETE FROM purchases")
            cursor.execute("DELETE FROM expenses")
            cursor.execute("DELETE FROM activity_log")
            # Reset customer balances
            cursor.execute("UPDATE customers SET balance = 0.0")

    @staticmethod
    def factory_reset(admin_password: str = "admin"):
        """Completely wipes and re-initializes all tables to factory default state."""
        with get_db() as conn:
            cursor = conn.cursor()
            tables = [
                "order_items", "orders", "returns", "held_orders",
                "stock_adjustments", "purchase_items", "purchases",
                "expenses", "activity_log", "customers", "suppliers",
                "products", "categories", "users", "settings"
            ]
            for t in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {t}")
        init_database()
