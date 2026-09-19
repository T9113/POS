from datetime import datetime
from pos_app.database import get_db

class PurchaseModel:
    @staticmethod
    def create_purchase(supplier_id: int, user_id: int, total_amount: float, note: str, items: list):
        """
        Creates a purchase order, records purchase items, and increments product current_stock.
        items: list of dicts {product_id, quantity, cost_price, total}
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO purchases (supplier_id, user_id, total_amount, note, status, created_at)
                VALUES (?, ?, ?, ?, 'received', ?)
            """, (supplier_id, user_id, float(total_amount), note.strip(), now))
            purchase_id = cursor.lastrowid

            for item in items:
                cursor.execute("""
                    INSERT INTO purchase_items (purchase_id, product_id, quantity, cost_price, total)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    purchase_id,
                    item["product_id"],
                    float(item["quantity"]),
                    float(item["cost_price"]),
                    float(item["total"])
                ))
                # Update stock and optionally cost price
                cursor.execute("""
                    UPDATE products 
                    SET current_stock = current_stock + ?,
                        cost_price = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (float(item["quantity"]), float(item["cost_price"]), now, item["product_id"]))

            return purchase_id

    @staticmethod
    def list_purchases(limit: int = 50, offset: int = 0):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.*, s.name as supplier_name, u.full_name as user_name
                FROM purchases p
                LEFT JOIN suppliers s ON p.supplier_id = s.id
                LEFT JOIN users u ON p.user_id = u.id
                ORDER BY p.created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_purchase_by_id(purchase_id: int):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.*, s.name as supplier_name, u.full_name as user_name
                FROM purchases p
                LEFT JOIN suppliers s ON p.supplier_id = s.id
                LEFT JOIN users u ON p.user_id = u.id
                WHERE p.id = ?
            """, (purchase_id,))
            purchase = cursor.fetchone()
            if not purchase:
                return None
            res = dict(purchase)
            cursor.execute("""
                SELECT pi.*, pr.name as product_name, pr.barcode, pr.sku
                FROM purchase_items pi
                JOIN products pr ON pi.product_id = pr.id
                WHERE pi.purchase_id = ?
            """, (purchase_id,))
            res["items"] = [dict(row) for row in cursor.fetchall()]
            return res
