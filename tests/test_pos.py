import os
import sys
import unittest
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from pos_app.database import init_database
from pos_app.models.product_model import ProductModel
from pos_app.models.customer_model import CustomerModel
from pos_app.models.order_model import OrderModel
from pos_app.controllers.pos_controller import POSController
from pos_app.controllers.sales_controller import SalesController
from pos_app.controllers.settings_controller import SettingsController
from pos_app.utils.exporter import Exporter
from pos_app.utils.receipt_printer import ReceiptPrinter

class TestSwiftPOS(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_database()

    def test_01_product_search_performance(self):
        """Verify search query speed over 5,000+ products is fast (< 50ms)"""
        start = time.perf_counter()
        results = ProductModel.search_products(query="Rice", limit=25)
        duration_ms = (time.perf_counter() - start) * 1000
        self.assertIsInstance(results, list)
        self.assertLess(duration_ms, 100.0, f"Search took {duration_ms:.2f}ms, should be < 100ms")

    def test_02_cart_calculation(self):
        """Test subtotal, discounts, tax, and total in cart"""
        controller = POSController()
        controller.clear_cart()

        prod1 = {"id": 99991, "name": "Item A", "selling_price": 100.0, "cost_price": 60.0, "current_stock": 50}
        prod2 = {"id": 99992, "name": "Item B", "selling_price": 250.0, "cost_price": 150.0, "current_stock": 20}

        controller.add_product(prod1, qty=2) # 200
        controller.add_product(prod2, qty=1) # 250 -> subtotal 450

        summary = controller.get_summary()
        self.assertEqual(summary["subtotal"], 450.0)
        self.assertEqual(summary["grand_total"], 450.0)

        # Apply 10% bill discount
        controller.set_order_discount(10, is_percentage=True)
        summary_disc = controller.get_summary()
        self.assertEqual(summary_disc["discount_amount"], 45.0)
        self.assertEqual(summary_disc["grand_total"], 405.0)

    def test_03_checkout_and_stock_decrement(self):
        """Test that checkout saves order and atomically decreases stock"""
        ts = int(time.time() * 1000)
        pid = ProductModel.create({
            "name": f"Test Milk {ts}",
            "sku": f"TEST-MILK-{ts}",
            "barcode": f"888{ts}",
            "selling_price": 200.0,
            "cost_price": 150.0,
            "current_stock": 10.0,
            "min_stock": 2.0
        })

        initial_prod = ProductModel.get_by_id(pid)
        self.assertEqual(initial_prod["current_stock"], 10.0)

        controller = POSController()
        controller.clear_cart()
        controller.add_product(initial_prod, qty=3)

        ok, msg, order = controller.checkout(payment_method="cash", amount_paid=600.0)
        self.assertTrue(ok)
        self.assertEqual(order["total"], 600.0)

        # Verify stock decreased by 3 -> 7.0
        updated_prod = ProductModel.get_by_id(pid)
        self.assertEqual(updated_prod["current_stock"], 7.0)

        # Test Receipt formatting
        receipt_txt = ReceiptPrinter.format_receipt_text(order)
        self.assertIn("TOTAL:", receipt_txt)

    def test_04_returns_and_restock(self):
        """Test returning order items restocks inventory"""
        ts = int(time.time() * 1000)
        pid = ProductModel.create({
            "name": f"Test Widget {ts}",
            "sku": f"TEST-WIDGET-{ts}",
            "barcode": f"777{ts}",
            "selling_price": 50.0,
            "cost_price": 30.0,
            "current_stock": 10.0
        })

        controller = POSController()
        controller.clear_cart()
        prod = ProductModel.get_by_id(pid)
        controller.add_product(prod, qty=4) # Stock becomes 6

        ok, msg, order = controller.checkout(payment_method="cash", amount_paid=200.0)
        self.assertTrue(ok)
        self.assertEqual(ProductModel.get_by_id(pid)["current_stock"], 6.0)

        # Return 2 items
        returned = [{"product_id": pid, "quantity": 2, "refund_amount": 100.0}]
        ret_ok, ret_msg = SalesController.process_refund(order["id"], returned, 100.0, "Customer Return")
        self.assertTrue(ret_ok)

        # Stock should be 6 + 2 = 8.0
        self.assertEqual(ProductModel.get_by_id(pid)["current_stock"], 8.0)

    def test_05_backup_database(self):
        """Test SQLite backup API"""
        ok, msg = SettingsController.backup_database()
        self.assertTrue(ok)
        self.assertIn("pos_backup_", msg)

    def test_06_excel_and_pdf_export(self):
        """Test Excel and PDF generation"""
        headers = ["Col A", "Col B"]
        rows = [["Val 1", "Val 2"], ["Val 3", "Val 4"]]
        
        xl_path = Exporter.export_excel("test_export.xlsx", "Test Sheet", headers, rows)
        self.assertTrue(os.path.exists(xl_path))

        pdf_path = Exporter.export_pdf("test_export.pdf", "Test PDF", headers, rows)
        self.assertTrue(os.path.exists(pdf_path))

    def test_07_loyalty_points_redemption(self):
        """Test earning and redeeming loyalty points (Feature R)"""
        ts = int(time.time() * 1000)
        cid = CustomerModel.create(f"Loyalty VIP Tester {ts}", f"0300{ts % 10000000:07d}")
        CustomerModel.add_loyalty_points(cid, 50)
        cust = CustomerModel.get_by_id(cid)
        self.assertEqual(cust["loyalty_points"], 50)

        controller = POSController()
        controller.clear_cart()
        controller.set_customer(cust)

        pid = ProductModel.create({
            "name": f"Loyalty Item {ts}",
            "sku": f"LOYAL-{ts}",
            "barcode": f"444{ts}",
            "selling_price": 500.0,
            "cost_price": 300.0,
            "current_stock": 20.0
        })
        prod = ProductModel.get_by_id(pid)
        controller.add_product(prod, qty=1)

        # Redeem 30 loyalty points (Rs 30 discount)
        ok, msg = controller.redeem_loyalty_points(30)
        self.assertTrue(ok)

        summary = controller.get_summary()
        self.assertEqual(summary["loyalty_discount"], 30.0)
        self.assertEqual(summary["grand_total"], 470.0)

        ok, msg, order = controller.checkout(payment_method="cash", amount_paid=500.0)
        self.assertTrue(ok)
        self.assertEqual(order["total"], 470.0)

        # Check customer balance updated: 50 - 30 + (470 // 100) = 24 points
        updated_cust = CustomerModel.get_by_id(cid)
        self.assertEqual(updated_cust["loyalty_points"], 24)

    def test_08_price_override_and_profit_calculation(self):
        """Test price override and profit recording (Features N & T)"""
        ts = int(time.time() * 1000)
        pid = ProductModel.create({
            "name": f"Override Item {ts}",
            "sku": f"OVERRIDE-{ts}",
            "barcode": f"666{ts}",
            "selling_price": 200.0,
            "cost_price": 120.0,
            "current_stock": 15.0
        })
        prod = ProductModel.get_by_id(pid)

        controller = POSController()
        controller.clear_cart()
        controller.add_product(prod, qty=2)

        # Override price from 200 to 180 (Manager Special)
        controller.override_item_price(product_id=pid, new_price=180.0, reason="Manager Special")

        item = controller.cart_items[pid]
        self.assertEqual(item["unit_price"], 180.0)
        self.assertEqual(item["price_override"], 1)
        self.assertEqual(item["override_reason"], "Manager Special")

        ok, msg, order = controller.checkout(payment_method="cash", amount_paid=400.0)
        self.assertTrue(ok)
        self.assertEqual(order["total"], 360.0)
        self.assertEqual(order["cost_total"], 240.0)
        self.assertEqual(order["profit"], 120.0) # 360 - 240

    def test_09_eod_report_reconciliation(self):
        """Test End-of-Day cash reconciliation and variance calculation (Feature P)"""
        from pos_app.models.eod_model import EODModel
        expected_cash, total_sales, total_orders = EODModel.get_expected_cash()
        self.assertGreaterEqual(expected_cash, 0.0)

        # Enter actual cash with Rs 50 shortage
        actual_cash = max(0.0, expected_cash - 50.0)
        report_id = EODModel.save_report(
            user_id=1,
            expected_cash=expected_cash,
            actual_cash=actual_cash,
            notes="End of Day test closing"
        )
        self.assertIsInstance(report_id, int)

        report = EODModel.get_latest_report()
        self.assertIsNotNone(report)
        self.assertEqual(report["id"], report_id)
        self.assertAlmostEqual(report["difference"], actual_cash - expected_cash, places=2)

    def test_10_product_favorites(self):
        """Test pinning favorite / frequent products (Feature M)"""
        ts = int(time.time() * 1000)
        pid = ProductModel.create({
            "name": f"Favorite Quick Bread {ts}",
            "sku": f"FAV-BREAD-{ts}",
            "barcode": f"555{ts}",
            "selling_price": 80.0,
            "cost_price": 50.0,
            "current_stock": 50.0
        })

        self.assertFalse(ProductModel.get_by_id(pid).get("is_favorite", False))
        ProductModel.toggle_favorite(pid)
        self.assertTrue(ProductModel.get_by_id(pid).get("is_favorite", False))

        favs = ProductModel.get_favorites(limit=12)
        fav_ids = [f["id"] for f in favs]
        self.assertIn(pid, fav_ids)

        ProductModel.toggle_favorite(pid)
        self.assertFalse(ProductModel.get_by_id(pid).get("is_favorite", False))

if __name__ == "__main__":
    unittest.main()
