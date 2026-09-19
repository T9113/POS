from datetime import datetime
from pos_app.database import get_db

class InventoryModel:
    @staticmethod
    def adjust_stock(product_id: int, user_id: int, quantity_change: float, reason: str, note: str = ""):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO stock_adjustments (product_id, user_id, quantity_change, reason, note, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (product_id, user_id, float(quantity_change), reason, note.strip(), now))
            adjust_id = cursor.lastrowid

            cursor.execute("""
                UPDATE products 
                SET current_stock = current_stock + ?, updated_at = ?
                WHERE id = ?
            """, (float(quantity_change), now, product_id))
            return adjust_id

    @staticmethod
    def list_adjustments(limit: int = 50, offset: int = 0):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sa.*, p.name as product_name, p.sku, u.full_name as user_name
                FROM stock_adjustments sa
                JOIN products p ON sa.product_id = p.id
                LEFT JOIN users u ON sa.user_id = u.id
                ORDER BY sa.created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            return [dict(row) for row in cursor.fetchall()]
