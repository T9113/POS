import json
from pos_app.database import get_db
from pos_app.models.order_model import OrderModel

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
                SELECT COALESCE(SUM(o.profit), 0.0) as gross_profit
                FROM orders o
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
        refunds = OrderModel.get_refund_totals(date_from, date_to)
        summary["gross_sales"] = summary["total_sales"]
        summary["total_refunds"] = refunds["total_refunds"]
        summary["return_count"] = refunds["return_count"]
        summary["total_sales"] = round(summary["gross_sales"] - refunds["total_refunds"], 2)
        summary["gross_profit"] = round(summary["gross_profit"] - (refunds["total_refunds"] - refunds["refund_cost"]), 2)
        summary["total_expenses"] = total_expenses
        summary["net_profit"] = round(summary["gross_profit"] - total_expenses, 2)
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
    def _returns_by_product(date_from: str = None, date_to: str = None) -> dict:
        """{product_name: {"qty", "refund", "cost", "category_name"}} for returns made in the range."""
        conditions, params = [], []
        if date_from:
            conditions.append("date(r.created_at) >= date(?)")
            params.append(date_from)
        if date_to:
            conditions.append("date(r.created_at) <= date(?)")
            params.append(date_to)
        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        out = {}
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT r.items_json FROM returns r {where}", params)
            rows = cursor.fetchall()
            for row in rows:
                for it in json.loads(row["items_json"] or "[]"):
                    name = it.get("product_name") or "Item"
                    rec = out.setdefault(name, {"qty": 0.0, "refund": 0.0, "cost": 0.0, "category_name": None})
                    qty = float(it.get("quantity", 0))
                    rec["qty"] += qty
                    rec["refund"] += float(it.get("refund_amount", float(it.get("unit_price", 0)) * qty))
                    rec["cost"] += float(it.get("cost_price") or 0.0) * qty
                    if rec["category_name"] is None and it.get("product_id"):
                        cursor.execute("""
                            SELECT COALESCE(c.name, 'Uncategorized') AS cname
                            FROM products p LEFT JOIN categories c ON p.category_id = c.id
                            WHERE p.id = ?
                        """, (it["product_id"],))
                        c_row = cursor.fetchone()
                        rec["category_name"] = c_row["cname"] if c_row else "Uncategorized"
        return out

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
                    SUM(oi.total * (CASE WHEN o.subtotal > 0 THEN (o.subtotal - o.discount_amount) / o.subtotal ELSE 1.0 END)) as total_revenue,
                    SUM(oi.total * (CASE WHEN o.subtotal > 0 THEN (o.subtotal - o.discount_amount) / o.subtotal ELSE 1.0 END) - oi.cost_price * oi.quantity) as total_profit
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                {where}
                GROUP BY oi.product_name
            """, params)
            rows = [dict(row) for row in cursor.fetchall()]

        returns = ReportModel._returns_by_product(date_from, date_to)
        for r in rows:
            ret = returns.get(r["product_name"])
            if ret:
                r["total_units_sold"] = round(r["total_units_sold"] - ret["qty"], 3)
                r["total_revenue"] = round(r["total_revenue"] - ret["refund"], 2)
                r["total_profit"] = round(r["total_profit"] - (ret["refund"] - ret["cost"]), 2)
        rows = [r for r in rows if r["total_units_sold"] > 1e-9]
        rows.sort(key=lambda r: r["total_units_sold"], reverse=True)
        return rows[:limit]

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
                    SUM(oi.total * (CASE WHEN o.subtotal > 0 THEN (o.subtotal - o.discount_amount) / o.subtotal ELSE 1.0 END)) as total_revenue
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                LEFT JOIN products p ON oi.product_id = p.id
                LEFT JOIN categories c ON p.category_id = c.id
                {where}
                GROUP BY category_name
            """, params)
            rows = {row["category_name"]: dict(row) for row in cursor.fetchall()}

        for ret in ReportModel._returns_by_product(date_from, date_to).values():
            cat = rows.get(ret["category_name"] or "Uncategorized")
            if cat:
                cat["total_units_sold"] = round(cat["total_units_sold"] - ret["qty"], 3)
                cat["total_revenue"] = round(cat["total_revenue"] - ret["refund"], 2)
        result = [r for r in rows.values() if r["total_units_sold"] > 1e-9]
        result.sort(key=lambda r: r["total_revenue"], reverse=True)
        return result

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
