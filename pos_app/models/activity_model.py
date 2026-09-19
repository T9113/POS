from datetime import datetime
from pos_app.database import get_db

class ActivityModel:
    @staticmethod
    def log(user_id: int, action: str, detail: str = ""):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO activity_log (user_id, action, detail, created_at)
                VALUES (?, ?, ?, ?)
            """, (user_id, action, detail, now))
            return cursor.lastrowid

    @staticmethod
    def list_all(limit: int = 100, offset: int = 0):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT a.*, u.full_name as user_name, u.username
                FROM activity_log a
                LEFT JOIN users u ON a.user_id = u.id
                ORDER BY a.created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            return [dict(row) for row in cursor.fetchall()]
