from datetime import datetime
from pos_app.database import get_db

class ExpenseModel:
    CATEGORIES = [
        "Rent", "Electricity & Utilities", "Salary & Wages", 
        "Transport & Fuel", "Store Supplies", "Repairs & Maintenance",
        "Marketing & Ads", "Tax & Licenses", "Other"
    ]

    @staticmethod
    def create(category: str, amount: float, description: str, date: str, user_id: int):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO expenses (category, amount, description, date, user_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (category, float(amount), description.strip(), date, user_id, now))
            return cursor.lastrowid

    @staticmethod
    def list_all(category: str = None, date_from: str = None, date_to: str = None, limit: int = 100, offset: int = 0):
        conditions = []
        params = []
        if category and category != "All":
            conditions.append("e.category = ?")
            params.append(category)
        if date_from:
            conditions.append("e.date >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("e.date <= ?")
            params.append(date_to)

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        sql = f"""
            SELECT e.*, u.full_name as user_name
            FROM expenses e
            LEFT JOIN users u ON e.user_id = u.id
            {where_clause}
            ORDER BY e.date DESC, e.id DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_total_expenses(date_from: str = None, date_to: str = None):
        conditions = []
        params = []
        if date_from:
            conditions.append("date >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("date <= ?")
            params.append(date_to)

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        sql = f"SELECT COALESCE(SUM(amount), 0.0) FROM expenses {where_clause}"

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return cursor.fetchone()[0]

    @staticmethod
    def delete(expense_id: int):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            return cursor.rowcount > 0
