from datetime import datetime
from pos_app.database import get_db
from pos_app.models.order_model import OrderModel


class EODModel:
    @staticmethod
    def get_eod_calculation_for_today():
        today_date = datetime.now().strftime("%Y-%m-%d")
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as total_orders, COALESCE(SUM(total), 0.0) as total_sales
                FROM orders
                WHERE date(created_at) = date(?) AND status != 'cancelled'
            """, (today_date,))
            sales_row = cursor.fetchone()

            # Cash taken into the drawer: full cash sales plus the cash part of split sales
            cursor.execute("""
                SELECT COALESCE(SUM(amount_paid - change_due), 0.0) as cash_sales
                FROM orders
                WHERE date(created_at) = date(?)
                  AND status != 'cancelled'
                  AND payment_method IN ('cash', 'split')
            """, (today_date,))
            cash_sales = cursor.fetchone()["cash_sales"]

            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0.0) as collected
                FROM customer_payments
                WHERE date(created_at) = date(?)
            """, (today_date,))
            khata_collections = cursor.fetchone()["collected"]

        refunds = OrderModel.get_refund_totals(today_date, today_date)
        expected_cash = round(cash_sales + khata_collections - refunds["cash_refunds"], 2)

        return {
            "date": today_date,
            "total_orders": sales_row["total_orders"],
            "total_sales": sales_row["total_sales"],
            "cash_sales": cash_sales,
            "khata_collections": khata_collections,
            "cash_refunds": refunds["cash_refunds"],
            "total_refunds": refunds["total_refunds"],
            "expected_cash": expected_cash,
        }

    @staticmethod
    def save_eod_report(user_id: int, total_sales: float, total_orders: int,
                        expected_cash: float, actual_cash: float, difference: float, notes: str = ""):
        today_date = datetime.now().strftime("%Y-%m-%d")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO eod_reports (
                    user_id, date, total_sales, total_orders,
                    expected_cash, actual_cash, difference, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, today_date, total_sales, total_orders, expected_cash, actual_cash, difference, notes.strip(), now))
            return cursor.lastrowid

    @staticmethod
    def list_reports(limit: int = 50):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.*, u.full_name as user_name
                FROM eod_reports r
                LEFT JOIN users u ON r.user_id = u.id
                ORDER BY r.created_at DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_today_report():
        today_date = datetime.now().strftime("%Y-%m-%d")
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM eod_reports WHERE date = ? ORDER BY created_at DESC LIMIT 1", (today_date,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_expected_cash():
        calc = EODModel.get_eod_calculation_for_today()
        return calc["expected_cash"], calc["total_sales"], calc["total_orders"]

    @staticmethod
    def save_report(user_id: int, expected_cash: float, actual_cash: float, notes: str = "", total_sales: float = None, total_orders: int = None):
        if total_sales is None or total_orders is None:
            calc = EODModel.get_eod_calculation_for_today()
            total_sales = calc["total_sales"]
            total_orders = calc["total_orders"]
        diff = round(actual_cash - expected_cash, 2)
        return EODModel.save_eod_report(user_id, total_sales, total_orders, expected_cash, actual_cash, diff, notes)

    @staticmethod
    def get_latest_report():
        reports = EODModel.list_reports(limit=1)
        return reports[0] if reports else None
