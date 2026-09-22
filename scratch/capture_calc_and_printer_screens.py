"""
Visual verification capture script for POS Calculations and Printer Windows.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from pos_app.database import init_database
from pos_app.controllers.auth_controller import AuthController
from pos_app.models.product_model import ProductModel
from pos_app.models.customer_model import CustomerModel
from pos_app.views.qt_main_window import QtMainWindow
from pos_app.views.dialogs.qt_receipt_dialog import QtReceiptPreviewDialog
from pos_app.qt_theme import GLOBAL_QSS

def capture():
    init_database()
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(GLOBAL_QSS)

    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scratch_screenshots")
    os.makedirs(output_dir, exist_ok=True)

    AuthController.login("admin", "admin")

    main_win = QtMainWindow()
    main_win.resize(1280, 800)
    main_win.show()
    app.processEvents()
    time.sleep(0.3)

    # 1. Switch to POS view and add items
    main_win.navigate_to("pos")
    app.processEvents()
    pos_view = main_win.screen_instances["pos"]
    pos_view.cart_controller.clear()

    prods = ProductModel.list_all(limit=3)
    if len(prods) >= 2:
        pos_view._add_product_to_cart(prods[0])
        pos_view._add_product_to_cart(prods[1])
        pos_view._adjust_qty(prods[0]["id"], 2) # +2 qty
        pos_view.txt_discount.setText("25")
        pos_view._apply_discount()
        app.processEvents()
        time.sleep(0.2)

    pos_path = os.path.join(output_dir, "screen_calc_pos_totals.png")
    main_win.grab().save(pos_path)
    print(f"Captured: {pos_path}")

    # 2. Open Receipt Preview Dialog with sample order
    sample_order = {
        "order_number": "ORD-20260922-0088",
        "created_at": "2026-09-22 14:35:00",
        "customer_name": "Tariq Mehmood",
        "cashier_name": "Admin Cashier",
        "items": [
            {"product_name": "Basmati Rice 5kg", "quantity": 1, "unit_price": 1450.0, "total": 1450.0},
            {"product_name": "Sunflower Cooking Oil 3L", "quantity": 2, "unit_price": 980.0, "total": 1960.0},
            {"product_name": "Full Cream Milk 1L", "quantity": 4, "unit_price": 210.0, "total": 840.0}
        ],
        "subtotal": 4250.0,
        "discount_amount": 150.0,
        "tax_amount": 205.0,
        "total": 4305.0,
        "amount_paid": 5000.0,
        "change_due": 695.0,
        "payment_method": "cash"
    }

    rcpt_dlg = QtReceiptPreviewDialog(main_win, sample_order)
    rcpt_dlg.show()
    app.processEvents()
    time.sleep(0.2)
    rcpt_path = os.path.join(output_dir, "screen_receipt_preview_80mm.png")
    rcpt_dlg.grab().save(rcpt_path)
    print(f"Captured: {rcpt_path}")

    # Switch to 58mm
    rcpt_dlg._set_paper_width("58mm")
    app.processEvents()
    time.sleep(0.2)
    rcpt_58_path = os.path.join(output_dir, "screen_receipt_preview_58mm.png")
    rcpt_dlg.grab().save(rcpt_58_path)
    print(f"Captured: {rcpt_58_path}")
    rcpt_dlg.close()

    # 3. Customer Khata with Collect Due button
    main_win.navigate_to("customers")
    app.processEvents()
    time.sleep(0.2)
    cust_view = main_win.screen_instances["customers"]
    if cust_view.customers_cache:
        # Find a customer with balance or give first customer a balance for demonstration
        c0 = cust_view.customers_cache[0]
        CustomerModel.update_balance(c0["id"], 450.0)
        cust_view.refresh_customers()
        app.processEvents()
        cust_view.table_cust.selectRow(0)
        app.processEvents()
        time.sleep(0.2)

    cust_path = os.path.join(output_dir, "screen_customer_khata_due.png")
    main_win.grab().save(cust_path)
    print(f"Captured: {cust_path}")

    main_win.close()
    print("All verification screenshots captured successfully.")

if __name__ == "__main__":
    capture()
