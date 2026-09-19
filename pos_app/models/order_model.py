import json
from datetime import datetime
from pos_app.database import get_db

class OrderModel:
    @staticmethod
    def generate_order_number():
        date_str = datetime.now().strftime("%Y%m%d")
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM orders WHERE order_number LIKE ?", (f"ORD-{date_str}-%",))
            count = cursor.fetchone()[0] + 1
            return f"ORD-{date_str}-{count:04d}"

    @staticmethod
    def create_order(order_data: dict, items: list):
        """
        Creates an order and order items atomically, decrements inventory,
        and adjusts customer balance if on credit.
        """
        order_number = order_data.get("order_number") or OrderModel.generate_order_number()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO orders (
                    order_number, customer_id, user_id, subtotal,
                    discount_amount, discount_percent, tax_amount, total,
                    amount_paid, change_due, payment_method, payment_status,
                    note, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                order_number,
                order_data.get("customer_id"),
                order_data.get("user_id"),
                float(order_data.get("subtotal", 0.0)),
                float(order_data.get("discount_amount", 0.0)),
                float(order_data.get("discount_percent", 0.0)),
                float(order_data.get("tax_amount", 0.0)),
                float(order_data.get("total", 0.0)),
                float(order_data.get("amount_paid", 0.0)),
                float(order_data.get("change_due", 0.0)),
                order_data.get("payment_method", "cash"),
                order_data.get("payment_status", "paid"),
                order_data.get("note", ""),
                order_data.get("status", "completed"),
                now
            ))
            order_id = cursor.lastrowid

            for item in items:
                cursor.execute("""
                    INSERT INTO order_items (
                        order_id, product_id, product_name, quantity,
                        unit_price, discount, total, cost_price
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    order_id,
                    item.get("product_id"),
                    item.get("product_name"),
                    float(item.get("quantity", 1)),
                    float(item.get("unit_price", 0.0)),
                    float(item.get("discount", 0.0)),
                    float(item.get("total", 0.0)),
                    float(item.get("cost_price", 0.0))
                ))
                # Decrement inventory stock
                if item.get("product_id"):
                    cursor.execute("""
                        UPDATE products 
                        SET current_stock = current_stock - ?, updated_at = ?
                        WHERE id = ?
                    """, (float(item.get("quantity", 1)), now, item["product_id"]))

            # If payment method is Credit/Due or customer has unpaid balance
            customer_id = order_data.get("customer_id")
            total = float(order_data.get("total", 0.0))
            paid = float(order_data.get("amount_paid", 0.0))
            due = total - paid
            if customer_id and due > 0:
                cursor.execute("UPDATE customers SET balance = balance + ? WHERE id = ?", (due, customer_id))

            return order_id, order_number

    @staticmethod
    def get_order_by_id(order_id: int):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT o.*, c.name as customer_name, c.phone as customer_phone, u.full_name as cashier_name
                FROM orders o
                LEFT JOIN customers c ON o.customer_id = c.id
                LEFT JOIN users u ON o.user_id = u.id
                WHERE o.id = ?
            """, (order_id,))
            order = cursor.fetchone()
            if not order:
                return None
            order_dict = dict(order)

            cursor.execute("""
                SELECT oi.*, p.barcode, p.sku
                FROM order_items oi
                LEFT JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = ?
            """, (order_id,))
            order_dict["items"] = [dict(row) for row in cursor.fetchall()]
            return order_dict

    @staticmethod
    def list_orders(query: str = "", date_from: str = None, date_to: str = None,
                    payment_method: str = None, limit: int = 50, offset: int = 0):
        conditions = []
        params = []
        if query and query.strip():
            q = f"%{query.strip()}%"
            conditions.append("(o.order_number LIKE ? OR c.name LIKE ? OR c.phone LIKE ?)")
            params.extend([q, q, q])
        if date_from:
            conditions.append("date(o.created_at) >= date(?)")
            params.append(date_from)
        if date_to:
            conditions.append("date(o.created_at) <= date(?)")
            params.append(date_to)
        if payment_method and payment_method != "all":
            conditions.append("o.payment_method = ?")
            params.append(payment_method)

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        sql = f"""
            SELECT o.*, c.name as customer_name, u.full_name as cashier_name
            FROM orders o
            LEFT JOIN customers c ON o.customer_id = c.id
            LEFT JOIN users u ON o.user_id = u.id
            {where_clause}
            ORDER BY o.created_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def count_orders(query: str = "", date_from: str = None, date_to: str = None, payment_method: str = None):
        conditions = []
        params = []
        if query and query.strip():
            q = f"%{query.strip()}%"
            conditions.append("(o.order_number LIKE ? OR c.name LIKE ? OR c.phone LIKE ?)")
            params.extend([q, q, q])
        if date_from:
            conditions.append("date(o.created_at) >= date(?)")
            params.append(date_from)
        if date_to:
            conditions.append("date(o.created_at) <= date(?)")
            params.append(date_to)
        if payment_method and payment_method != "all":
            conditions.append("o.payment_method = ?")
            params.append(payment_method)

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        sql = f"""
            SELECT COUNT(*)
            FROM orders o
            LEFT JOIN customers c ON o.customer_id = c.id
            {where_clause}
        """
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return cursor.fetchone()[0]

    # Held Orders functionality
    @staticmethod
    def hold_order(cart_data: dict, customer_id: int = None, user_id: int = None, note: str = ""):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO held_orders (cart_data_json, customer_id, user_id, note)
                VALUES (?, ?, ?, ?)
            """, (json.dumps(cart_data), customer_id, user_id, note))
            return cursor.lastrowid

    @staticmethod
    def list_held_orders():
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT h.*, c.name as customer_name, u.full_name as cashier_name
                FROM held_orders h
                LEFT JOIN customers c ON h.customer_id = c.id
                LEFT JOIN users u ON h.user_id = u.id
                ORDER BY h.created_at DESC
            """)
            orders = []
            for row in cursor.fetchall():
                d = dict(row)
                d["cart_data"] = json.loads(d["cart_data_json"])
                orders.append(d)
            return orders

    @staticmethod
    def delete_held_order(held_id: int):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM held_orders WHERE id = ?", (held_id,))
            return cursor.rowcount > 0

    # Returns / Refunds
    @staticmethod
    def process_return(order_id: int, user_id: int, returned_items: list, total_refund: float, reason: str):
        """
        Records return, restocks inventory, logs return record.
        returned_items: list of dicts with {product_id, quantity, refund_amount}
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO returns (order_id, user_id, items_json, total_refund, reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (order_id, user_id, json.dumps(returned_items), total_refund, reason, now))
            return_id = cursor.lastrowid

            # Restock items
            for item in returned_items:
                pid = item.get("product_id")
                qty = float(item.get("quantity", 0))
                if pid and qty > 0:
                    cursor.execute("""
                        UPDATE products 
                        SET current_stock = current_stock + ?, updated_at = ?
                        WHERE id = ?
                    """, (qty, now, pid))

            cursor.execute("UPDATE orders SET status = 'returned' WHERE id = ?", (order_id,))
            return return_id

    # Today Dashboard Metrics
    @staticmethod
    def get_today_metrics():
        today_date = datetime.now().strftime("%Y-%m-%d")
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_orders,
                    COALESCE(SUM(total), 0.0) as total_sales
                FROM orders
                WHERE date(created_at) = date(?) AND status != 'cancelled'
            """, (today_date,))
            sales_row = cursor.fetchone()

            # Today's profit = revenue of order items minus cost of order items
            cursor.execute("""
                SELECT 
                    COALESCE(SUM((oi.unit_price - oi.discount) * oi.quantity - (oi.cost_price * oi.quantity)), 0.0) as gross_profit
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                WHERE date(o.created_at) = date(?) AND o.status != 'cancelled'
            """, (today_date,))
            profit_row = cursor.fetchone()

            # Top 5 products today
            cursor.execute("""
                SELECT oi.product_name, SUM(oi.quantity) as total_qty, SUM(oi.total) as total_revenue
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                WHERE date(o.created_at) = date(?) AND o.status != 'cancelled'
                GROUP BY oi.product_name
                ORDER BY total_qty DESC
                LIMIT 5
            """, (today_date,))
            top_products = [dict(row) for row in cursor.fetchall()]

            return {
                "total_orders": sales_row["total_orders"] if sales_row else 0,
                "total_sales": sales_row["total_sales"] if sales_row else 0.0,
                "gross_profit": profit_row["gross_profit"] if profit_row else 0.0,
                "top_products": top_products
            }
