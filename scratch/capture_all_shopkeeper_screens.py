import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap

from pos_app.database import init_database
from pos_app.qt_theme import GLOBAL_QSS
from pos_app.views.qt_main_window import QtMainWindow
from pos_app.views.qt_products_view import QtProductEditDialog
from pos_app.views.dialogs.qt_customer_dialog import QtCustomerDialog
from pos_app.views.dialogs.qt_payment_dialog import QtPaymentDialog
from pos_app.controllers.auth_controller import AuthController
from pos_app.models.product_model import ProductModel
from pos_app.models.customer_model import CustomerModel

def capture_all():
    init_database()
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(GLOBAL_QSS)

    out_dir = os.path.abspath("scratch_screenshots")
    os.makedirs(out_dir, exist_ok=True)

    # Login as admin
    admin = AuthController.login("admin", "admin123")
    assert admin, "Admin login failed"

    # Create main window
    win = QtMainWindow()
    win.resize(1280, 800)
    win.show()
    app.processEvents()
    time.sleep(0.3)
    app.processEvents()

    # 1. POS View
    print("[1/9] Capturing POS View...")
    win.navigate_to("pos")
    app.processEvents()
    pos_view = win.screen_instances["pos"]
    # Add a couple items to cart for a realistic demonstration
    prods = ProductModel.list_all(limit=4)
    if prods:
        pos_view._add_product_to_cart(prods[0])
        if len(prods) > 1:
            pos_view._add_product_to_cart(prods[1])
            pos_view._add_product_to_cart(prods[1])
    app.processEvents()
    time.sleep(0.3)
    p_pos = os.path.join(out_dir, "screen_01_pos_checkout.png")
    win.grab().save(p_pos)
    print(f"Saved: {p_pos}")

    # 2. Payment Dialog
    print("[2/9] Capturing Payment Dialog...")
    cart_data = {
        "grand_total": 1500.0,
        "subtotal": 1500.0,
        "discount_amount": 0.0,
        "tax_amount": 0.0,
        "items": [
            {"product_id": 1, "product_name": "Premium Tea Bags", "unit_price": 250.0, "quantity": 2, "total": 500.0}
        ]
    }
    pay_dlg = QtPaymentDialog(parent=win, cart_data=cart_data, customer=None)
    pay_dlg.show()
    app.processEvents()
    time.sleep(0.3)
    p_pay = os.path.join(out_dir, "screen_02_payment_modal.png")
    pay_dlg.card.grab().save(p_pay)
    print(f"Saved: {p_pay}")
    pay_dlg.close()
    app.processEvents()

    # 3. Product Form with Validation Highlights
    print("[3/9] Capturing Product Add/Edit Dialog Validation...")
    prod_dlg = QtProductEditDialog(parent=win)
    prod_dlg.show()
    app.processEvents()
    # Trigger save with missing required fields
    prod_dlg._save()
    app.processEvents()
    time.sleep(0.3)
    p_p_dlg = os.path.join(out_dir, "screen_03_product_validation.png")
    prod_dlg.card.grab().save(p_p_dlg)
    print(f"Saved: {p_p_dlg}")
    prod_dlg.close()
    app.processEvents()

    # 4. Products Catalog View
    print("[4/9] Capturing Products Catalog View...")
    win.navigate_to("products")
    app.processEvents()
    time.sleep(0.3)
    p_prod = os.path.join(out_dir, "screen_04_products_catalog.png")
    win.grab().save(p_prod)
    print(f"Saved: {p_prod}")

    # 5. Inventory & Low Stock View
    print("[5/9] Capturing Inventory & Low Stock View...")
    win.navigate_to("inventory")
    app.processEvents()
    time.sleep(0.3)
    p_inv = os.path.join(out_dir, "screen_05_inventory_low_stock.png")
    win.grab().save(p_inv)
    print(f"Saved: {p_inv}")

    # 6. Customers & Khata Ledger View
    print("[6/9] Capturing Customers & Khata Ledger View...")
    win.navigate_to("customers")
    app.processEvents()
    cust_view = win.screen_instances["customers"]
    if cust_view.table_cust.rowCount() > 0:
        cust_view.table_cust.selectRow(0)
    app.processEvents()
    time.sleep(0.3)
    p_cust = os.path.join(out_dir, "screen_06_customers_khata.png")
    win.grab().save(p_cust)
    print(f"Saved: {p_cust}")

    # 7. Customer Dialog Validation
    print("[7/9] Capturing Customer Dialog Validation...")
    cust_dlg = QtCustomerDialog(parent=win)
    cust_dlg.show()
    app.processEvents()
    cust_dlg._save_customer()
    app.processEvents()
    time.sleep(0.3)
    p_c_dlg = os.path.join(out_dir, "screen_07_customer_validation.png")
    cust_dlg.card.grab().save(p_c_dlg)
    print(f"Saved: {p_c_dlg}")
    cust_dlg.close()
    app.processEvents()

    # 8. Sales History View
    print("[8/9] Capturing Sales History View...")
    win.navigate_to("sales")
    app.processEvents()
    sales_view = win.screen_instances["sales"]
    if sales_view.table_orders.rowCount() > 0:
        sales_view.table_orders.selectRow(0)
    app.processEvents()
    time.sleep(0.3)
    p_sales = os.path.join(out_dir, "screen_08_sales_orders.png")
    win.grab().save(p_sales)
    print(f"Saved: {p_sales}")

    # 9. Expenses View
    print("[9/9] Capturing Expenses View...")
    win.navigate_to("expenses")
    app.processEvents()
    exp_view = win.screen_instances["expenses"]
    # Trigger expense validation
    exp_view._add_expense()
    app.processEvents()
    time.sleep(0.3)
    p_exp = os.path.join(out_dir, "screen_09_expenses_log.png")
    win.grab().save(p_exp)
    print(f"Saved: {p_exp}")

    # 10. Reports & Analytics View
    print("[10/11] Capturing Reports & Analytics View...")
    win.navigate_to("reports")
    app.processEvents()
    time.sleep(0.3)
    p_rep = os.path.join(out_dir, "screen_10_reports_analytics.png")
    win.grab().save(p_rep)
    print(f"Saved: {p_rep}")

    # 11. Settings View
    print("[11/11] Capturing Settings View...")
    win.navigate_to("settings")
    app.processEvents()
    time.sleep(0.3)
    p_set = os.path.join(out_dir, "screen_11_settings_config.png")
    win.grab().save(p_set)
    print(f"Saved: {p_set}")

    win.close()
    print("All screenshots successfully captured!")

if __name__ == "__main__":
    capture_all()
