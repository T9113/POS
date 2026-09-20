from pos_app.database import get_db

class SupplierModel:
    @staticmethod
    def get_by_id(supplier_id: int):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM suppliers WHERE id = ?", (supplier_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def list_all(search_query: str = "", limit: int = 100, offset: int = 0):
        with get_db() as conn:
            cursor = conn.cursor()
            if search_query and search_query.strip():
                q = f"%{search_query.strip()}%"
                cursor.execute("""
                    SELECT * FROM suppliers 
                    WHERE name LIKE ? OR phone LIKE ? OR email LIKE ?
                    ORDER BY name ASC
                    LIMIT ? OFFSET ?
                """, (q, q, q, limit, offset))
            else:
                cursor.execute("SELECT * FROM suppliers ORDER BY name ASC LIMIT ? OFFSET ?", (limit, offset))
            return [dict(row) for row in cursor.fetchall()]

    get_all = list_all

    @staticmethod
    def create(name: str, phone: str = "", email: str = "", address: str = "", notes: str = ""):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO suppliers (name, phone, email, address, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (name.strip(), phone.strip(), email.strip(), address.strip(), notes.strip()))
            return cursor.lastrowid

    @staticmethod
    def update(supplier_id: int, name: str, phone: str = "", email: str = "", address: str = "", notes: str = ""):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE suppliers 
                SET name = ?, phone = ?, email = ?, address = ?, notes = ?
                WHERE id = ?
            """, (name.strip(), phone.strip(), email.strip(), address.strip(), notes.strip(), supplier_id))
            return cursor.rowcount > 0

    @staticmethod
    def delete(supplier_id: int):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM suppliers WHERE id = ?", (supplier_id,))
            return cursor.rowcount > 0
