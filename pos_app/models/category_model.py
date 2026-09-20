from pos_app.database import get_db

class CategoryModel:
    @staticmethod
    def list_all(active_only: bool = False):
        with get_db() as conn:
            cursor = conn.cursor()
            if active_only:
                cursor.execute("SELECT * FROM categories WHERE is_active = 1 ORDER BY sort_order ASC, name ASC")
            else:
                cursor.execute("SELECT * FROM categories ORDER BY sort_order ASC, name ASC")
            return [dict(row) for row in cursor.fetchall()]

    get_all = list_all

    @staticmethod
    def get_by_id(category_id: int):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_or_create(name: str):
        name = name.strip()
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM categories WHERE LOWER(name) = LOWER(?)", (name,))
            row = cursor.fetchone()
            if row:
                return row["id"]
            cursor.execute("INSERT INTO categories (name, sort_order, is_active) VALUES (?, 0, 1)", (name,))
            return cursor.lastrowid

    @staticmethod
    def create(name: str, sort_order: int = 0):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO categories (name, sort_order, is_active) VALUES (?, ?, 1)", (name.strip(), sort_order))
            return cursor.lastrowid

    @staticmethod
    def update(category_id: int, name: str, sort_order: int = 0, is_active: int = 1):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE categories SET name = ?, sort_order = ?, is_active = ? WHERE id = ?",
                (name.strip(), sort_order, is_active, category_id)
            )
            return cursor.rowcount > 0

    @staticmethod
    def delete(category_id: int):
        with get_db() as conn:
            cursor = conn.cursor()
            # Soft delete
            cursor.execute("UPDATE categories SET is_active = 0 WHERE id = ?", (category_id,))
            return cursor.rowcount > 0
