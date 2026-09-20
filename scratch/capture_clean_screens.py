import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from pos_app.database import init_database
from pos_app.qt_theme import GLOBAL_QSS
from pos_app.views.qt_main_window import QtMainWindow
from pos_app.views.qt_products_view import QtProductEditDialog
from pos_app.views.dialogs.qt_customer_dialog import QtCustomerDialog
from pos_app.views.dialogs.qt_payment_dialog import QtPaymentDialog
from pos_app.views.qt_expenses_view import QtExpensesView
from pos_app.controllers.auth_controller import AuthController
from pos_app.models.product_model import ProductModel
from pos_app.models.customer_model import CustomerModel

def main():
    init_database()
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(GLOBAL_QSS)

    out_dir = os.path.abspath("scratch_screenshots")
    os.makedirs(out_dir, exist_ok=True)

    # 1. Login as admin
    ok, msg = AuthController.login("admin", "admin")
    admin = AuthController.get_current_user()
    print(f"Logged in: {admin['full_name']} ({admin['role']})", flush=True)

    # 2. Main Window and Views
    win = QtMainWindow()
    win.resize(1280, 800)
    win.show()
    app.processEvents()
    time.sleep(0.3)
    app.processEvents()

    # POS
    print("Capturing 01_pos...", flush=True)
    win.navigate_to("pos")
    app.processEvents()
    pos_view = win.screen_instances["pos"]
    prods = ProductModel.list_all(limit=3)
    if prods:
        pos_view._add_product_to_cart(prods[0])
        if len(prods) > 1:
            pos_view._add_product_to_cart(prods[1])
            pos_view._add_product_to_cart(prods[1])
    app.processEvents()
    time.sleep(0.3)
    win.grab().save(os.path.join(out_dir, "01_pos_checkout.png"))

    # Products
    print("Capturing 02_products...", flush=True)
    win.navigate_to("products")
    prod_view = win.screen_instances["products"]
    prod_view.load_products()
    app.processEvents()
    time.sleep(0.3)
    win.grab().save(os.path.join(out_dir, "02_products_catalog.png"))

    # Inventory
    print("Capturing 03_inventory...", flush=True)
    win.navigate_to("inventory")
    app.processEvents()
    time.sleep(0.3)
    win.grab().save(os.path.join(out_dir, "03_inventory_stock.png"))

    # Customers
    print("Capturing 04_customers...", flush=True)
    win.navigate_to("customers")
    app.processEvents()
    cust_view = win.screen_instances["customers"]
    if cust_view.table_cust.rowCount() > 0:
        cust_view.table_cust.selectRow(0)
    app.processEvents()
    time.sleep(0.3)
    win.grab().save(os.path.join(out_dir, "04_customers_khata.png"))

    # Sales
    print("Capturing 05_sales...", flush=True)
    win.navigate_to("sales")
    app.processEvents()
    sales_view = win.screen_instances["sales"]
    if sales_view.table_orders.rowCount() > 0:
        sales_view.table_orders.selectRow(0)
    app.processEvents()
    time.sleep(0.3)
    win.grab().save(os.path.join(out_dir, "05_sales_history.png"))

    # Expenses
    print("Capturing 06_expenses...", flush=True)
    win.navigate_to("expenses")
    app.processEvents()
    time.sleep(0.3)
    win.grab().save(os.path.join(out_dir, "06_expenses_store.png"))

    # Reports
    print("Capturing 07_reports...", flush=True)
    win.navigate_to("reports")
    app.processEvents()
    time.sleep(0.3)
    win.grab().save(os.path.join(out_dir, "07_reports_analytics.png"))

    # Settings
    print("Capturing 08_settings...", flush=True)
    win.navigate_to("settings")
    app.processEvents()
    time.sleep(0.3)
    win.grab().save(os.path.join(out_dir, "08_settings_profile.png"))

    win.hide()
    win.close()
    app.processEvents()

    # 3. Modals and Forms with Validation
    dlg_host = QWidget()
    dlg_host.resize(1200, 800)
    dlg_host.show()
    app.processEvents()

    # Payment Modal
    print("Capturing 09_payment_dialog...", flush=True)
    cart_data = {
        "grand_total": 1250.0,
        "subtotal": 1250.0,
        "discount_amount": 0.0,
        "tax_amount": 0.0,
        "items": [
            {"product_id": 1, "product_name": "Premium Tea Bags", "unit_price": 250.0, "quantity": 5, "total": 1250.0}
        ]
    }
    pay_dlg = QtPaymentDialog(dlg_host, cart_data=cart_data)
    pay_dlg.show()
    app.processEvents()
    time.sleep(0.2)
    pay_dlg.card.grab().save(os.path.join(out_dir, "09_payment_modal.png"))
    pay_dlg.hide()
    pay_dlg.close()

    # Product Form Validation
    print("Capturing 10_product_form_validation...", flush=True)
    prod_dlg = QtProductEditDialog(dlg_host)
    prod_dlg.show()
    app.processEvents()
    prod_dlg._save()
    app.processEvents()
    time.sleep(0.2)
    prod_dlg.card.grab().save(os.path.join(out_dir, "10_product_form_validation.png"))
    prod_dlg.hide()
    prod_dlg.close()

    # Customer Form Validation
    print("Capturing 11_customer_form_validation...", flush=True)
    cust_dlg = QtCustomerDialog(dlg_host)
    cust_dlg.show()
    app.processEvents()
    cust_dlg._save_customer()
    app.processEvents()
    time.sleep(0.2)
    cust_dlg.card.grab().save(os.path.join(out_dir, "11_customer_form_validation.png"))
    cust_dlg.hide()
    cust_dlg.close()

    # Expenses Inline Form Validation
    print("Capturing 12_expense_form_validation...", flush=True)
    exp_host = QWidget()
    exp_host.resize(900, 500)
    exp_view = QtExpensesView(exp_host)
    exp_host.show()
    app.processEvents()
    exp_view._add_expense()
    app.processEvents()
    time.sleep(0.2)
    exp_host.grab().save(os.path.join(out_dir, "12_expense_validation.png"))
    exp_host.hide()
    exp_host.close()

    dlg_host.hide()
    dlg_host.close()
    app.processEvents()

    print("ALL 12 SHOPKEEPER SCREENS CAPTURED SUCCESSFULLY!", flush=True)
    os._exit(0)

if __name__ == "__main__":
    main()
