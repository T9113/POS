from pos_app.database import get_db

class ReportModel:
    @staticmethod
    def get_sales_summary(date_from: str = None, date_to: str = None):
        conditions = ["o.status != 'cancelled'"]
        params = []
        if date_from:
            conditions.append("date(o.created_at) >= date(?)")
            params.append(date_from)
        if date_to:
            conditions.append("date(o.created_at) <= date(?)")
            params.append(date_to)

        where = " WHERE " + " AND ".join(conditions)

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total_orders,
                    COALESCE(SUM(o.total), 0.0) as total_sales,
                    COALESCE(SUM(o.discount_amount), 0.0) as total_discount,
                    COALESCE(SUM(o.tax_amount), 0.0) as total_tax,
                    COALESCE(AVG(o.total), 0.0) as average_order_value
                FROM orders o
                {where}
            """, params)
            summary = dict(cursor.fetchone())

            # Gross profit
            cursor.execute(f"""
                SELECT 
                    COALESCE(SUM((oi.unit_price - oi.discount) * oi.quantity - (oi.cost_price * oi.quantity)), 0.0) as gross_profit
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                {where}
            """, params)
            profit_row = cursor.fetchone()
            summary["gross_profit"] = profit_row["gross_profit"] if profit_row else 0.0

            # Net profit (Gross profit minus expenses)
            exp_conditions = []
            exp_params = []
            if date_from:
                exp_conditions.append("date >= date(?)")
                exp_params.append(date_from)
            if date_to:
                exp_conditions.append("date <= date(?)")
                exp_params.append(date_to)
            exp_where = " WHERE " + " AND ".join(exp_conditions) if exp_conditions else ""
            cursor.execute(f"SELECT COALESCE(SUM(amount), 0.0) FROM expenses {exp_where}", exp_params)
            total_expenses = cursor.fetchone()[0]
            summary["total_expenses"] = total_expenses
            summary["net_profit"] = summary["gross_profit"] - total_expenses

            return summary

    @staticmethod
    def get_sales_by_date(date_from: str = None, date_to: str = None, group_by: str = "day"):
        format_map = {
            "day": "%Y-%m-%d",
            "week": "%Y-%W",
            "month": "%Y-%m"
        }
        fmt = format_map.get(group_by, "%Y-%m-%d")
        conditions = ["o.status != 'cancelled'"]
        params = []
        if date_from:
            conditions.append("date(o.created_at) >= date(?)")
            params.append(date_from)
        if date_to:
            conditions.append("date(o.created_at) <= date(?)")
            params.append(date_to)

        where = " WHERE " + " AND ".join(conditions)

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT 
                    strftime('{fmt}', o.created_at) as period,
                    COUNT(*) as order_count,
                    SUM(o.total) as total_sales,
                    SUM(o.tax_amount) as total_tax
                FROM orders o
                {where}
                GROUP BY period
                ORDER BY period ASC
            """, params)
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_product_sales(date_from: str = None, date_to: str = None, limit: int = 50):
        conditions = ["o.status != 'cancelled'"]
        params = []
        if date_from:
            conditions.append("date(o.created_at) >= date(?)")
            params.append(date_from)
        if date_to:
            conditions.append("date(o.created_at) <= date(?)")
            params.append(date_to)

        where = " WHERE " + " AND ".join(conditions)

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT 
                    oi.product_name,
                    SUM(oi.quantity) as total_units_sold,
                    SUM(oi.total) as total_revenue,
                    SUM((oi.unit_price - oi.discount) * oi.quantity - (oi.cost_price * oi.quantity)) as total_profit
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                {where}
                GROUP BY oi.product_name
                ORDER BY total_units_sold DESC
                LIMIT ?
            """, params + [limit])
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_category_sales(date_from: str = None, date_to: str = None):
        conditions = ["o.status != 'cancelled'"]
        params = []
        if date_from:
            conditions.append("date(o.created_at) >= date(?)")
            params.append(date_from)
        if date_to:
            conditions.append("date(o.created_at) <= date(?)")
            params.append(date_to)

        where = " WHERE " + " AND ".join(conditions)

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT 
                    COALESCE(c.name, 'Uncategorized') as category_name,
                    SUM(oi.quantity) as total_units_sold,
                    SUM(oi.total) as total_revenue
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                LEFT JOIN products p ON oi.product_id = p.id
                LEFT JOIN categories c ON p.category_id = c.id
                {where}
                GROUP BY category_name
                ORDER BY total_revenue DESC
            """, params)
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_hourly_sales(date_from: str = None, date_to: str = None):
        conditions = ["o.status != 'cancelled'"]
        params = []
        if date_from:
            conditions.append("date(o.created_at) >= date(?)")
            params.append(date_from)
        if date_to:
            conditions.append("date(o.created_at) <= date(?)")
            params.append(date_to)

        where = " WHERE " + " AND ".join(conditions)

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT 
                    strftime('%H', o.created_at) as hour,
                    COUNT(*) as order_count,
                    SUM(o.total) as total_sales
                FROM orders o
                {where}
                GROUP BY hour
                ORDER BY hour ASC
            """, params)
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_payment_method_breakdown(date_from: str = None, date_to: str = None):
        conditions = ["o.status != 'cancelled'"]
        params = []
        if date_from:
            conditions.append("date(o.created_at) >= date(?)")
            params.append(date_from)
        if date_to:
            conditions.append("date(o.created_at) <= date(?)")
            params.append(date_to)

        where = " WHERE " + " AND ".join(conditions)

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT 
                    o.payment_method,
                    COUNT(*) as transaction_count,
                    SUM(o.total) as total_amount
                FROM orders o
                {where}
                GROUP BY o.payment_method
            """, params)
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_top_customers(date_from: str = None, date_to: str = None, limit: int = 20):
        conditions = ["o.status != 'cancelled'", "o.customer_id IS NOT NULL"]
        params = []
        if date_from:
            conditions.append("date(o.created_at) >= date(?)")
            params.append(date_from)
        if date_to:
            conditions.append("date(o.created_at) <= date(?)")
            params.append(date_to)

        where = " WHERE " + " AND ".join(conditions)

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT 
                    c.id, c.name, c.phone,
                    COUNT(o.id) as total_orders,
                    SUM(o.total) as total_spent
                FROM orders o
                JOIN customers c ON o.customer_id = c.id
                {where}
                GROUP BY c.id
                ORDER BY total_spent DESC
                LIMIT ?
            """, params + [limit])
            return [dict(row) for row in cursor.fetchall()]
