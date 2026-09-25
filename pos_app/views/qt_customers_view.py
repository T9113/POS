"""
PySide6 Customers Directory View for OnesDev POS.
Customer database with credit/Khata balance tracking, search,
purchase history, and Excel export.
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFrame, QSplitter, QInputDialog
)

from pos_app.qt_theme import COLORS, AnimatedButton, DropShadowCard, clear_layout
from pos_app.models.customer_model import CustomerModel
from pos_app.models.order_model import OrderModel
from pos_app.models.settings_model import SettingsModel
from pos_app.controllers.auth_controller import AuthController
from pos_app.views.dialogs.qt_customer_dialog import QtCustomerDialog
from pos_app.utils.exporter import Exporter
from pos_app.utils.icon_helper import get_icon


class QtCustomersView(QWidget):
    """Customer Directory, Profiles, and Khata Management."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.currency = SettingsModel.get("currency_symbol", "Rs")
        self.selected_customer = None
        self.customer_dialog = None
        self._build_ui()
        self.refresh_customers()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Top Control Card
        top_card = DropShadowCard(self, corner_radius=12)
        top_layout = QHBoxLayout(top_card)
        top_layout.setContentsMargins(16, 12, 16, 12)
        top_layout.setSpacing(12)

        lbl_search = QLabel(top_card)
        lbl_search.setPixmap(get_icon("search", COLORS["text_muted"], 18).pixmap(18, 18))
        lbl_search.setFixedWidth(24)
        top_layout.addWidget(lbl_search)

        self.txt_search = QLineEdit(top_card)
        self.txt_search.setPlaceholderText("Search Customers by Name or Phone...")
        self.txt_search.setFixedHeight(36)
        self.txt_search.textChanged.connect(self.refresh_customers)
        top_layout.addWidget(self.txt_search, stretch=1)

        btn_excel = AnimatedButton("Export Excel", top_card, variant="secondary", icon_name="excel")
        btn_excel.setFixedHeight(36)
        btn_excel.clicked.connect(self._export_excel)
        top_layout.addWidget(btn_excel)

        btn_add = AnimatedButton("Add Customer", top_card, variant="primary", icon_name="plus")
        btn_add.setFixedHeight(36)
        btn_add.setToolTip("Register new customer account")
        btn_add.clicked.connect(self._open_add_customer)
        top_layout.addWidget(btn_add)

        main_layout.addWidget(top_card)

        # Splitter: Left = Directory, Right = Selected Profile & Order History
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Left Directory Card
        left_card = DropShadowCard(splitter, corner_radius=12)
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(8)

        lbl_dir = QLabel("CUSTOMER DIRECTORY", left_card)
        lbl_dir.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {COLORS['text_muted']}; letter-spacing: 0.5px;")
        left_layout.addWidget(lbl_dir)

        self.table_cust = QTableWidget(left_card)
        self.table_cust.setColumnCount(4)
        self.table_cust.setHorizontalHeaderLabels(["Name", "Phone", "Khata Balance", "Total Orders"])
        self.table_cust.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in (1, 2, 3):
            self.table_cust.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self.table_cust.verticalHeader().setVisible(False)
        self.table_cust.setAlternatingRowColors(True)
        self.table_cust.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_cust.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table_cust.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['bg_surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
            QHeaderView::section {{
                background-color: {COLORS['bg_hover']};
                color: {COLORS['text_secondary']};
                font-weight: 600;
                font-size: 12px;
                padding: 8px;
                border: none;
                border-bottom: 2px solid {COLORS['border']};
            }}
            QTableWidget::item {{
                padding: 6px 10px;
                font-size: 13px;
            }}
        """)
        self.table_cust.itemSelectionChanged.connect(self._on_customer_selected)
        left_layout.addWidget(self.table_cust)
        splitter.addWidget(left_card)

        # Right Profile Card
        self.right_card = DropShadowCard(splitter, corner_radius=12)
        self.right_layout = QVBoxLayout(self.right_card)
        self.right_layout.setContentsMargins(16, 16, 16, 16)
        self.right_layout.setSpacing(12)
        self._render_empty_profile()
        splitter.addWidget(self.right_card)

        splitter.setSizes([600, 500])
        main_layout.addWidget(splitter, stretch=1)

    def _render_empty_profile(self):
        clear_layout(self.right_layout)

        lbl_empty = QLabel("Select any customer to view account balance, notes, and purchase history.", self.right_card)
        lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_empty.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 14px;")
        self.right_layout.addWidget(lbl_empty)

    def refresh_customers(self):
        self.currency = SettingsModel.get("currency_symbol", "Rs")
        search_query = self.txt_search.text().strip()
        customers = CustomerModel.list_all(search=search_query)
        self.customers_cache = customers
        self.table_cust.setRowCount(len(customers))

        for r, c in enumerate(customers):
            self.table_cust.setItem(r, 0, QTableWidgetItem(c.get("name", "")))
            self.table_cust.setItem(r, 1, QTableWidgetItem(c.get("phone") or "-"))

            bal = c.get("balance", 0.0)
            bal_item = QTableWidgetItem(f"{self.currency} {bal:,.2f}")
            bal_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if bal > 0:
                bal_item.setForeground(QColor(COLORS["danger"]))
            self.table_cust.setItem(r, 2, bal_item)

            ord_cnt = c.get("total_orders", 0)
            ord_item = QTableWidgetItem(f"{ord_cnt}")
            ord_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_cust.setItem(r, 3, ord_item)

    def _on_customer_selected(self):
        selected_rows = self.table_cust.selectedIndexes()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        if row < len(self.customers_cache):
            customer = self.customers_cache[row]
            self._render_customer_profile(customer)

    def _render_customer_profile(self, customer: dict):
        clear_layout(self.right_layout)

        # Customer Header Profile
        lbl_name = QLabel(customer.get("name", ""), self.right_card)
        lbl_name.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLORS['text_primary']};")
        self.right_layout.addWidget(lbl_name)

        info_box = QFrame(self.right_card)
        info_box.setObjectName("CustomerInfoBox")
        info_box.setStyleSheet(f"""
            QFrame#CustomerInfoBox {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 12px;
            }}
            QWidget {{
                background: transparent;
                border: none;
            }}
        """)
        inf_l = QVBoxLayout(info_box)
        inf_l.setSpacing(6)

        def make_row(icon_name, text):
            r_w = QWidget(info_box)
            r_l = QHBoxLayout(r_w)
            r_l.setContentsMargins(0, 0, 0, 0)
            r_l.setSpacing(8)
            i_lbl = QLabel(r_w)
            i_lbl.setPixmap(get_icon(icon_name, COLORS["text_secondary"], 15).pixmap(15, 15))
            i_lbl.setFixedWidth(18)
            t_lbl = QLabel(text, r_w)
            t_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
            r_l.addWidget(i_lbl)
            r_l.addWidget(t_lbl, stretch=1)
            return r_w

        inf_l.addWidget(make_row("phone", f"Phone: {customer.get('phone') or 'Not provided'}"))
        inf_l.addWidget(make_row("mail", f"Email: {customer.get('email') or 'Not provided'}"))
        inf_l.addWidget(make_row("map_pin", f"Address: {customer.get('address') or 'Not provided'}"))

        bal = customer.get("balance", 0.0)
        bal_w = QWidget(info_box)
        bal_l = QHBoxLayout(bal_w)
        bal_l.setContentsMargins(0, 4, 0, 0)
        bal_l.setSpacing(8)
        bal_icon = QLabel(bal_w)
        bal_icon.setPixmap(get_icon("credit_card", COLORS['danger'] if bal > 0 else COLORS['success'], 16).pixmap(16, 16))
        bal_icon.setFixedWidth(18)
        lbl_bal = QLabel(f"Khata / Credit Due: {self.currency} {bal:,.2f}", bal_w)
        lbl_bal.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {COLORS['danger'] if bal > 0 else COLORS['success']};")
        bal_l.addWidget(bal_icon)
        bal_l.addWidget(lbl_bal, stretch=1)

        if bal > 0:
            btn_pay_due = AnimatedButton("Collect Due", bal_w, variant="success", icon_name="check", icon_color="#FFFFFF", icon_size=12)
            btn_pay_due.setFixedHeight(28)
            btn_pay_due.clicked.connect(lambda _, c=customer: self._collect_due(c))
            bal_l.addWidget(btn_pay_due)

        inf_l.addWidget(bal_w)

        self.right_layout.addWidget(info_box)

        # Recent Orders Table
        lbl_h = QLabel("Recent Purchases", self.right_card)
        lbl_h.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {COLORS['text_primary']}; margin-top: 8px;")
        self.right_layout.addWidget(lbl_h)

        history_table = QTableWidget(self.right_card)
        history_table.setColumnCount(3)
        history_table.setHorizontalHeaderLabels(["Order #", "Date", "Amount"])
        history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        history_table.verticalHeader().setVisible(False)

        cust_orders = OrderModel.list_orders(customer_id=customer.get("id"), limit=20)
        history_table.setRowCount(len(cust_orders))
        for i, o in enumerate(cust_orders):
            history_table.setItem(i, 0, QTableWidgetItem(o.get("order_number", "")))
            history_table.setItem(i, 1, QTableWidgetItem(o.get("created_at", "")[:10]))
            tot_item = QTableWidgetItem(f"{self.currency} {o.get('total', 0.0):,.2f}")
            tot_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            history_table.setItem(i, 2, tot_item)

        self.right_layout.addWidget(history_table, stretch=1)

    def _open_add_customer(self):
        top_window = self.window()
        if not self.customer_dialog:
            self.customer_dialog = QtCustomerDialog(top_window, on_complete=self.refresh_customers)
        self.customer_dialog.show_animated()

    def _export_excel(self):
        customers = CustomerModel.list_all()
        headers = ["Customer Name", "Phone", "Email", "Address", "Khata Balance", "Total Orders", "Total Spent"]
        rows = [
            [
                c.get("name", ""),
                c.get("phone", ""),
                c.get("email", ""),
                c.get("address", ""),
                f"{self.currency} {c.get('balance', 0.0):,.2f}",
                c.get("total_orders", 0),
                f"{self.currency} {c.get('total_spent', 0.0):,.2f}"
            ]
            for c in customers
        ]
        from datetime import datetime
        filename = f"customers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        try:
            path = Exporter.export_excel(filename, "Customer Directory", headers, rows)
            QMessageBox.information(self, "Export Complete", f"Customers exported successfully:\n\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "Export Error", str(e))

    def _collect_due(self, customer: dict):
        cur_bal = float(customer.get("balance", 0.0))
        amt, ok = QInputDialog.getDouble(
            self, "Collect Khata Due",
            f"Enter payment amount received from {customer.get('name')}:\n\n(Current Overdue Balance: {self.currency} {cur_bal:,.2f})",
            cur_bal, 0.01, cur_bal, 2
        )
        if ok and amt > 0:
            user = AuthController.get_current_user()
            CustomerModel.pay_due(customer["id"], amt, user_id=user["id"] if user else None, note="Khata collection")
            QMessageBox.information(
                self, "Payment Received",
                f"Successfully recorded payment of {self.currency} {amt:,.2f} for {customer.get('name')}."
            )
            self.refresh_customers()
            updated_c = CustomerModel.get_by_id(customer["id"])
            if updated_c:
                self._render_customer_profile(updated_c)
