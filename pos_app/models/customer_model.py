from pos_app.database import get_db

class CustomerModel:
    @staticmethod
    def get_by_id(customer_id: int):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def list_all(search_query: str = "", limit: int = 100, offset: int = 0, search: str = None):
        if search is not None:
            search_query = search
        select = """
            SELECT c.*,
                   (SELECT COUNT(*) FROM orders o WHERE o.customer_id = c.id AND o.status != 'cancelled') AS total_orders,
                   (SELECT COALESCE(SUM(o.total), 0.0) FROM orders o WHERE o.customer_id = c.id AND o.status != 'cancelled') AS total_spent
            FROM customers c
        """
        with get_db() as conn:
            cursor = conn.cursor()
            if search_query and search_query.strip():
                q = f"%{search_query.strip()}%"
                cursor.execute(select + """
                    WHERE c.name LIKE ? OR c.phone LIKE ? OR c.email LIKE ?
                    ORDER BY c.name ASC
                    LIMIT ? OFFSET ?
                """, (q, q, q, limit, offset))
            else:
                cursor.execute(select + " ORDER BY c.name ASC LIMIT ? OFFSET ?", (limit, offset))
            return [dict(row) for row in cursor.fetchall()]

    get_all = list_all

    @staticmethod
    def count(search_query: str = ""):
        with get_db() as conn:
            cursor = conn.cursor()
            if search_query and search_query.strip():
                q = f"%{search_query.strip()}%"
                cursor.execute("""
                    SELECT COUNT(*) FROM customers 
                    WHERE name LIKE ? OR phone LIKE ? OR email LIKE ?
                """, (q, q, q))
            else:
                cursor.execute("SELECT COUNT(*) FROM customers")
            return cursor.fetchone()[0]

    @staticmethod
    def create(name: str, phone: str = "", email: str = "", address: str = "", notes: str = "", balance: float = 0.0, loyalty_points: float = 0.0):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO customers (name, phone, email, address, notes, balance, loyalty_points)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name.strip(), phone.strip(), email.strip(), address.strip(), notes.strip(), float(balance), float(loyalty_points)))
            return cursor.lastrowid

    @staticmethod
    def update(customer_id: int, name: str, phone: str = "", email: str = "", address: str = "", notes: str = ""):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE customers 
                SET name = ?, phone = ?, email = ?, address = ?, notes = ?
                WHERE id = ?
            """, (name.strip(), phone.strip(), email.strip(), address.strip(), notes.strip(), customer_id))
            return cursor.rowcount > 0

    @staticmethod
    def update_balance(customer_id: int, new_balance: float):
        """Sets customer's due balance directly."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE customers SET balance = ? WHERE id = ?", (float(new_balance), customer_id))
            return cursor.rowcount > 0

    @staticmethod
    def adjust_balance(customer_id: int, amount: float):
        """Add to customer's due balance (positive = more due, negative = payment received)"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE customers SET balance = balance + ? WHERE id = ?", (amount, customer_id))
            return cursor.rowcount > 0

    @staticmethod
    def pay_due(customer_id: int, payment_amount: float, user_id: int = None, note: str = ""):
        """Records a Khata collection in the ledger and deducts it from the due balance."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT balance FROM customers WHERE id = ?", (customer_id,))
            row = cursor.fetchone()
            if not row:
                return False
            applied = min(float(payment_amount), max(0.0, float(row["balance"] or 0.0)))
            if applied <= 0:
                return False
            cursor.execute("UPDATE customers SET balance = balance - ? WHERE id = ?", (applied, customer_id))
            cursor.execute(
                "INSERT INTO customer_payments (customer_id, user_id, amount, note, created_at) VALUES (?, ?, ?, ?, datetime('now', 'localtime'))",
                (customer_id, user_id, applied, note)
            )
            return True

    @staticmethod
    def list_payments(customer_id: int, limit: int = 50):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM customer_payments WHERE customer_id = ? ORDER BY created_at DESC LIMIT ?",
                (customer_id, limit)
            )
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def add_loyalty_points(customer_id: int, points: float):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE customers SET loyalty_points = loyalty_points + ? WHERE id = ?", (points, customer_id))
            return cursor.rowcount > 0

    @staticmethod
    def redeem_loyalty_points(customer_id: int, points: float):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE customers SET loyalty_points = MAX(0.0, loyalty_points - ?) WHERE id = ?", (points, customer_id))
            return cursor.rowcount > 0

    @staticmethod
    def delete(customer_id: int):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
            return cursor.rowcount > 0

    @staticmethod
    def get_purchase_history(customer_id: int, limit: int = 50):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT o.*, u.full_name as cashier_name
                FROM orders o
                LEFT JOIN users u ON o.user_id = u.id
                WHERE o.customer_id = ?
                ORDER BY o.created_at DESC
                LIMIT ?
            """, (customer_id, limit))
            return [dict(row) for row in cursor.fetchall()]
