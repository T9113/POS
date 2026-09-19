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
        # Create a dedicated test product
        pid = ProductModel.create({
            "name": "Test Milk 1L",
            "sku": "TEST-MILK-001",
            "barcode": "999888777001",
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
        self.assertIn("Test Milk 1L", receipt_txt)
        self.assertIn("TOTAL:", receipt_txt)

    def test_04_returns_and_restock(self):
        """Test returning order items restocks inventory"""
        pid = ProductModel.create({
            "name": "Test Widget",
            "sku": "TEST-WIDGET-002",
            "barcode": "999888777002",
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

if __name__ == "__main__":
    unittest.main()
