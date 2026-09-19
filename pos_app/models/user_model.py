from pos_app.database import get_db
from pos_app.utils.security import hash_password, verify_password

class UserModel:
    @staticmethod
    def get_by_id(user_id: int):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_by_username(username: str):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (username,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def authenticate(username: str, password: str):
        user = UserModel.get_by_username(username)
        if not user or not user.get("is_active"):
            return None
        if verify_password(user["password_hash"], password):
            return user
        return None

    @staticmethod
    def list_all():
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, full_name, role, is_active, created_at FROM users ORDER BY id ASC")
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def create(username: str, password: str, full_name: str, role: str):
        pwd_hash = hash_password(password)
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password_hash, full_name, role, is_active) VALUES (?, ?, ?, ?, 1)",
                (username.strip(), pwd_hash, full_name.strip(), role)
            )
            return cursor.lastrowid

    @staticmethod
    def update(user_id: int, full_name: str, role: str, is_active: int, password: str = None):
        with get_db() as conn:
            cursor = conn.cursor()
            if password and password.strip():
                pwd_hash = hash_password(password.strip())
                cursor.execute(
                    "UPDATE users SET full_name = ?, role = ?, is_active = ?, password_hash = ? WHERE id = ?",
                    (full_name.strip(), role, is_active, pwd_hash, user_id)
                )
            else:
                cursor.execute(
                    "UPDATE users SET full_name = ?, role = ?, is_active = ? WHERE id = ?",
                    (full_name.strip(), role, is_active, user_id)
                )
            return cursor.rowcount > 0
