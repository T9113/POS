from pos_app.database import get_db
from datetime import datetime

class ProductModel:
    @staticmethod
    def get_by_id(product_id: int):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.*, c.name as category_name 
                FROM products p 
                LEFT JOIN categories c ON p.category_id = c.id 
                WHERE p.id = ?
            """, (product_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_by_barcode_or_sku(code: str):
        if not code:
            return None
        code = code.strip()
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.*, c.name as category_name 
                FROM products p 
                LEFT JOIN categories c ON p.category_id = c.id 
                WHERE p.is_active = 1 AND (p.barcode = ? OR p.sku = ?)
            """, (code, code))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_favorites(limit: int = 12):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.*, c.name as category_name
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.is_active = 1 AND p.is_favorite = 1
                ORDER BY p.name ASC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def toggle_favorite(product_id: int):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE products 
                SET is_favorite = CASE WHEN is_favorite = 1 THEN 0 ELSE 1 END
                WHERE id = ?
            """, (product_id,))
            cursor.execute("SELECT is_favorite FROM products WHERE id = ?", (product_id,))
            row = cursor.fetchone()
            return row["is_favorite"] if row else 0

    @staticmethod
    def search_products(query: str = "", category_id: int = None, active_only: bool = True,
                        limit: int = 50, offset: int = 0, sort_by: str = "name", sort_order: str = "ASC"):
        valid_sort_cols = {
            "name": "p.name",
            "selling_price": "p.selling_price",
            "current_stock": "p.current_stock",
            "category": "c.name",
            "id": "p.id"
        }
        order_col = valid_sort_cols.get(sort_by, "p.name")
        order_dir = "DESC" if sort_order.upper() == "DESC" else "ASC"

        conditions = []
        params = []

        if active_only:
            conditions.append("p.is_active = 1")
        if category_id:
            conditions.append("p.category_id = ?")
            params.append(category_id)
        if query and query.strip():
            q = f"%{query.strip()}%"
            conditions.append("(p.name LIKE ? OR p.barcode LIKE ? OR p.sku LIKE ? OR c.name LIKE ?)")
            params.extend([q, q, q, q])

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

        sql = f"""
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            {where_clause}
            ORDER BY {order_col} {order_dir}
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_all(limit: int = 1000):
        return ProductModel.search_products(limit=limit)

    list_all = get_all

    @staticmethod
    def count_products(query: str = "", category_id: int = None, active_only: bool = True):
        conditions = []
        params = []
        if active_only:
            conditions.append("p.is_active = 1")
        if category_id:
            conditions.append("p.category_id = ?")
            params.append(category_id)
        if query and query.strip():
            q = f"%{query.strip()}%"
            conditions.append("(p.name LIKE ? OR p.barcode LIKE ? OR p.sku LIKE ? OR c.name LIKE ?)")
            params.extend([q, q, q, q])

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        sql = f"""
            SELECT COUNT(*)
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            {where_clause}
        """
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return cursor.fetchone()[0]

    @staticmethod
    def create(data: dict):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO products (
                    name, sku, barcode, category_id, parent_product_id, unit, cost_price,
                    selling_price, wholesale_price, min_stock, current_stock,
                    image_path, description, is_favorite, is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["name"].strip(),
                data.get("sku", "").strip() or None,
                data.get("barcode", "").strip() or None,
                data.get("category_id"),
                data.get("parent_product_id"),
                data.get("unit", "piece"),
                float(data.get("cost_price", 0.0)),
                float(data.get("selling_price", 0.0)),
                float(data.get("wholesale_price", 0.0)),
                float(data.get("min_stock", 5.0)),
                float(data.get("current_stock", 0.0)),
                data.get("image_path"),
                data.get("description", ""),
                int(data.get("is_favorite", 0)),
                int(data.get("is_active", 1)),
                now, now
            ))
            return cursor.lastrowid

    @staticmethod
    def update(product_id: int, data: dict):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE products SET
                    name = ?, sku = ?, barcode = ?, category_id = ?, parent_product_id = ?, unit = ?,
                    cost_price = ?, selling_price = ?, wholesale_price = ?,
                    min_stock = ?, current_stock = ?, image_path = ?,
                    description = ?, is_favorite = ?, is_active = ?, updated_at = ?
                WHERE id = ?
            """, (
                data["name"].strip(),
                data.get("sku", "").strip() or None,
                data.get("barcode", "").strip() or None,
                data.get("category_id"),
                data.get("parent_product_id"),
                data.get("unit", "piece"),
                float(data.get("cost_price", 0.0)),
                float(data.get("selling_price", 0.0)),
                float(data.get("wholesale_price", 0.0)),
                float(data.get("min_stock", 5.0)),
                float(data.get("current_stock", 0.0)),
                data.get("image_path"),
                data.get("description", ""),
                int(data.get("is_favorite", 0)),
                int(data.get("is_active", 1)),
                now,
                product_id
            ))
            return cursor.rowcount > 0

    @staticmethod
    def update_stock(product_id: int, delta: float):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE products 
                SET current_stock = current_stock + ?, updated_at = ?
                WHERE id = ?
            """, (delta, now, product_id))
            return cursor.rowcount > 0

    @staticmethod
    def set_stock(product_id: int, new_stock: float):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE products 
                SET current_stock = ?, updated_at = ?
                WHERE id = ?
            """, (new_stock, now, product_id))
            return cursor.rowcount > 0

    @staticmethod
    def soft_delete(product_id: int):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE products SET is_active = 0 WHERE id = ?", (product_id,))
            return cursor.rowcount > 0

    @staticmethod
    def get_low_stock_products(limit: int = 50):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.*, c.name as category_name
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.is_active = 1 AND p.current_stock <= p.min_stock
                ORDER BY p.current_stock ASC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_low_stock_count():
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM products WHERE is_active = 1 AND current_stock <= min_stock")
            return cursor.fetchone()[0]

    @staticmethod
    def get_stock_valuation():
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_items,
                    SUM(current_stock) as total_units,
                    SUM(current_stock * cost_price) as total_cost_value,
                    SUM(current_stock * selling_price) as total_retail_value
                FROM products
                WHERE is_active = 1
            """)
            row = cursor.fetchone()
            return dict(row) if row else {
                "total_items": 0, "total_units": 0, "total_cost_value": 0.0, "total_retail_value": 0.0
            }

    @staticmethod
    def bulk_update_prices(product_ids: list, adjustment_type: str, value: float):
        if not product_ids:
            return 0
        placeholders = ",".join("?" for _ in product_ids)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with get_db() as conn:
            cursor = conn.cursor()
            if adjustment_type == "percent":
                multiplier = 1.0 + (value / 100.0)
                cursor.execute(f"""
                    UPDATE products 
                    SET selling_price = ROUND(selling_price * ?, 2), updated_at = ?
                    WHERE id IN ({placeholders})
                """, [multiplier, now] + product_ids)
            else:
                cursor.execute(f"""
                    UPDATE products 
                    SET selling_price = MAX(0, ROUND(selling_price + ?, 2)), updated_at = ?
                    WHERE id IN ({placeholders})
                """, [value, now] + product_ids)
            return cursor.rowcount

    @staticmethod
    def get_all_for_export():
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id, p.name, p.sku, p.barcode, c.name as category,
                       p.unit, p.cost_price, p.selling_price, p.wholesale_price,
                       p.min_stock, p.current_stock, p.description, p.is_active
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                ORDER BY p.id ASC
            """)
            return [dict(row) for row in cursor.fetchall()]
