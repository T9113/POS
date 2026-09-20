import sys
import os
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap

from pos_app.database import init_database
from pos_app.qt_theme import GLOBAL_QSS
from pos_app.views.qt_products_view import QtProductEditDialog, QtProductsView
from pos_app.views.dialogs.qt_customer_dialog import QtCustomerDialog
from pos_app.views.qt_main_window import QtMainWindow
from pos_app.views.qt_login_view import QtLoginWindow
from pos_app.controllers.auth_controller import AuthController

def run_verification():
    init_database()
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(GLOBAL_QSS)

    out_dir = os.path.abspath("scratch_screenshots")
    os.makedirs(out_dir, exist_ok=True)

    parent = QWidget()
    parent.resize(1200, 800)
    parent.show()
    app.processEvents()

    # 1. Test Product Edit Dialog (Error state)
    print("[1/5] Testing QtProductEditDialog validation & highlight...")
    dlg = QtProductEditDialog(parent)
    dlg.show()
    app.processEvents()

    # Click save without filling required fields
    dlg._save()
    app.processEvents()
    time.sleep(0.2)
    app.processEvents()

    p1 = os.path.join(out_dir, "product_form_error_highlight.png")
    dlg.card.grab().save(p1)
    print(f"Saved: {p1}")

    # Check that error label is visible and field has error styling
    assert dlg.lbl_name_err.isVisible(), "Name error label should be visible!"
    assert dlg.lbl_sell_err.isVisible(), "Selling price error label should be visible!"

    # Now fill the fields and verify errors clear dynamically
    dlg.txt_name.setText("Wireless Barcode Scanner")
    app.processEvents()
    assert not dlg.lbl_name_err.isVisible(), "Name error should clear upon typing!"

    dlg.spn_sell.setValue(4500.0)
    app.processEvents()
    assert not dlg.lbl_sell_err.isVisible(), "Selling price error should clear upon value change!"

    dlg.txt_barcode.setText("8901234567890")
    dlg.spn_cost.setValue(3200.0)
    dlg.spn_stock.setValue(25.0)
    app.processEvents()

    p2 = os.path.join(out_dir, "product_form_filled_clean.png")
    dlg.card.grab().save(p2)
    print(f"Saved: {p2}")
    dlg.close()

    # 2. Test Customer Dialog validation & highlight
    print("[2/5] Testing QtCustomerDialog validation & highlight...")
    cdlg = QtCustomerDialog(parent)
    cdlg.show()
    app.processEvents()

    # Click save without filling customer name
    cdlg._save_customer()
    app.processEvents()
    time.sleep(0.1)
    app.processEvents()

    p3 = os.path.join(out_dir, "customer_dialog_error_highlight.png")
    cdlg.card.grab().save(p3)
    print(f"Saved: {p3}")
    assert cdlg.lbl_name_err.isVisible(), "Customer name error label should be visible!"

    cdlg.txt_name.setText("Ali Khan Traders")
    app.processEvents()
    assert not cdlg.lbl_name_err.isVisible(), "Customer name error should clear upon typing!"
    cdlg.close()

    # 3. Test Products Catalog View with SVG table action buttons
    print("[3/5] Testing QtProductsView table rendering...")
    pview = QtProductsView()
    pview.resize(1100, 600)
    pview.show()
    app.processEvents()
    time.sleep(0.2)
    app.processEvents()

    p4 = os.path.join(out_dir, "products_catalog_table_svg.png")
    pview.grab().save(p4)
    print(f"Saved: {p4}")
    pview.close()

    # 4. Test QtMainWindow with SVG sidebar icons and zero glitch frame
    print("[4/5] Testing QtMainWindow sidebar & navigation...")
    AuthController.login("admin", "admin")
    main_win = QtMainWindow()
    main_win.show()
    app.processEvents()
    time.sleep(0.3)
    app.processEvents()

    p5 = os.path.join(out_dir, "main_window_sidebar_svg.png")
    main_win.grab().save(p5)
    print(f"Saved: {p5}")
    main_win.close()

    # 5. Test QtLoginWindow with SVG brand icon
    print("[5/5] Testing QtLoginWindow card & SVG icon...")
    login_win = QtLoginWindow()
    login_win.show()
    app.processEvents()
    time.sleep(0.2)
    app.processEvents()

    p6 = os.path.join(out_dir, "login_window_svg.png")
    login_win.grab().save(p6)
    print(f"Saved: {p6}")
    login_win.close()

    print("\n All UI verification tests passed successfully!")

if __name__ == "__main__":
    run_verification()
