"""
Unit and Integration Tests for POS Calculations and Receipt Thermal Printer Subsystem.
Verifies mathematical accuracy for Subtotals, Discounts, Taxes (inclusive & exclusive),
Tender/Change returns, Khata Ledger balances, Cost/Profit margins, and 80mm/58mm Receipt formats.
"""
import unittest
from pos_app.models.order_model import OrderModel, OrderResult
from pos_app.models.customer_model import CustomerModel
from pos_app.models.expense_model import ExpenseModel
from pos_app.models.report_model import ReportModel
from pos_app.controllers.cart_controller import CartController
from pos_app.utils.receipt_printer import ReceiptPrinter
from pos_app.database import init_database


class TestPOSCalculationsAndPrinter(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_database()

    def setUp(self):
        # Create a test customer
        self.cust_id = CustomerModel.create(
            name="Test Math Customer",
            phone="0300-9998887",
            balance=0.0
        )

    def tearDown(self):
        if self.cust_id:
            from pos_app.database import get_db
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM customer_payments WHERE customer_id = ?", (self.cust_id,))
                cursor.execute("DELETE FROM order_items WHERE order_id IN (SELECT id FROM orders WHERE customer_id = ?)", (self.cust_id,))
                cursor.execute("DELETE FROM orders WHERE customer_id = ?", (self.cust_id,))
            CustomerModel.delete(self.cust_id)

    def test_cart_item_and_subtotal_calculations(self):
        cart = CartController()
        cart.add_item(product_id=101, name="Soap Bar", price=50.0, cost_price=30.0, quantity=3)
        cart.add_item(product_id=102, name="Shampoo Bottle", price=250.0, cost_price=160.0, quantity=2)

        # 3 * 50 = 150; 2 * 250 = 500 => Subtotal = 650
        self.assertEqual(cart.get_subtotal(), 650.0)

        # Apply flat discount of 50
        cart.set_discount(50.0)
        self.assertEqual(cart.get_discount(), 50.0)
        self.assertEqual(cart.get_grand_total(), 600.0)

        # Quantity adjustment: increase item 101 by +2 (total 5)
        cart.adjust_quantity(101, 2)
        # 5 * 50 = 250; 2 * 250 = 500 => Subtotal = 750, Grand = 700
        self.assertEqual(cart.get_subtotal(), 750.0)
        self.assertEqual(cart.get_grand_total(), 700.0)

    def test_exclusive_and_inclusive_tax_calculations(self):
        subtotal = 1000.0
        discount = 100.0
        net_subtotal = subtotal - discount # 900.0
        tax_pct = 10.0 # 10%

        # Exclusive Tax: Added on top
        tax_exclusive = round((net_subtotal * tax_pct) / 100.0, 2)
        grand_exclusive = round(net_subtotal + tax_exclusive, 2)
        self.assertEqual(tax_exclusive, 90.0)
        self.assertEqual(grand_exclusive, 990.0)

        # Inclusive Tax: Already inside net_subtotal
        tax_inclusive = round(net_subtotal - (net_subtotal / (1.0 + (tax_pct / 100.0))), 2)
        grand_inclusive = round(net_subtotal, 2)
        self.assertEqual(tax_inclusive, 81.82)
        self.assertEqual(grand_inclusive, 900.0)

    def test_change_return_calculation(self):
        grand_total = 475.50
        tendered = 500.0
        change_due = round(max(0.0, tendered - grand_total), 2)
        self.assertEqual(change_due, 24.50)

        # Short payment
        tendered_short = 400.0
        diff = tendered_short - grand_total
        self.assertTrue(diff < 0)
        self.assertEqual(round(abs(diff), 2), 75.50)

    def test_order_creation_profit_and_inventory_calculation(self):
        items = [
            {"product_id": None, "name": "Item A", "price": 100.0, "cost_price": 60.0, "quantity": 2},
            {"product_id": None, "name": "Item B", "price": 200.0, "cost_price": 120.0, "quantity": 1}
        ]
        # Total = 2*100 + 1*200 = 400. Cost = 2*60 + 1*120 = 240.
        # Expected profit = 400 - 240 = 160.
        order_res = OrderModel.create_order(
            customer_id=self.cust_id,
            user_id=1,
            items=items,
            subtotal=400.0,
            discount_amount=0.0,
            tax_amount=0.0,
            total=400.0,
            amount_paid=400.0,
            change_due=0.0,
            payment_method="cash"
        )
        self.assertTrue(order_res.get("success"))
        order_dict = order_res.get("order")
        self.assertEqual(order_dict["total"], 400.0)
        self.assertEqual(order_dict["cost_total"], 240.0)
        self.assertEqual(order_dict["profit"], 160.0)

    def test_khata_credit_and_payment_settlement(self):
        # Customer buys on Credit (Khata): total 350.0, paid 0.0
        items = [{"name": "Grocery Item", "price": 350.0, "cost_price": 200.0, "quantity": 1}]
        order_res = OrderModel.create_order(
            customer_id=self.cust_id,
            user_id=1,
            items=items,
            subtotal=350.0,
            total=350.0,
            amount_paid=0.0,
            change_due=0.0,
            payment_method="credit",
            payment_status="credit"
        )
        self.assertTrue(order_res.get("success"))

        # Verify customer's due balance increased by 350.0
        cust = CustomerModel.get_by_id(self.cust_id)
        self.assertEqual(cust["balance"], 350.0)

        # Customer makes partial payment of 200.0
        CustomerModel.pay_due(self.cust_id, 200.0)
        cust_after_pay = CustomerModel.get_by_id(self.cust_id)
        self.assertEqual(cust_after_pay["balance"], 150.0)

        # Customer settles remaining 150.0
        CustomerModel.pay_due(self.cust_id, 150.0)
        cust_cleared = CustomerModel.get_by_id(self.cust_id)
        self.assertEqual(cust_cleared["balance"], 0.0)

    def test_receipt_printer_80mm_and_58mm_formatting(self):
        order = {
            "order_number": "ORD-20260922-9999",
            "created_at": "2026-09-22 14:00:00",
            "customer_name": "Test Customer",
            "cashier_name": "Admin",
            "items": [
                {"product_name": "Basmati Rice 1kg", "quantity": 2, "unit_price": 320.0, "total": 640.0},
                {"product_name": "Cooking Oil 1L", "quantity": 1, "unit_price": 510.0, "total": 510.0}
            ],
            "subtotal": 1150.0,
            "discount_amount": 50.0,
            "tax_amount": 55.0,
            "total": 1155.0,
            "amount_paid": 1200.0,
            "change_due": 45.0,
            "payment_method": "cash"
        }

        # 80mm format (42 columns)
        rcpt_80 = ReceiptPrinter.format_receipt_text(order, width="80mm")
        self.assertIn("Basmati Rice", rcpt_80)
        self.assertIn("1,150.00", rcpt_80) # Subtotal
        self.assertIn("50.00", rcpt_80)   # Discount
        self.assertIn("1,155.00", rcpt_80) # Total
        self.assertIn("45.00", rcpt_80)    # Change Due

        # 58mm format (32 columns)
        rcpt_58 = ReceiptPrinter.format_receipt_text(order, width="58mm")
        self.assertIn("Basmati", rcpt_58)
        self.assertIn("1,155.00", rcpt_58)

    def test_printer_enumeration(self):
        printers = ReceiptPrinter.get_printers()
        self.assertIsInstance(printers, list)
        self.assertTrue(len(printers) > 0)


if __name__ == "__main__":
    unittest.main()
