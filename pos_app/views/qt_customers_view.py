"""
PySide6 Customers Directory View for OnesDev POS.
Customer database with credit/Khata balance tracking, search,
purchase history, and Excel export.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFrame, QSplitter
)

from pos_app.qt_theme import COLORS, AnimatedButton, DropShadowCard
from pos_app.models.customer_model import CustomerModel
from pos_app.models.order_model import OrderModel
from pos_app.models.settings_model import SettingsModel
from pos_app.views.dialogs.qt_customer_dialog import QtCustomerDialog
from pos_app.utils.exporter import Exporter


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

        lbl_search = QLabel("🔍", top_card)
        lbl_search.setStyleSheet("font-size: 15px;")
        top_layout.addWidget(lbl_search)

        self.txt_search = QLineEdit(top_card)
        self.txt_search.setPlaceholderText("Search Customers by Name or Phone...")
        self.txt_search.setFixedHeight(36)
        self.txt_search.textChanged.connect(self.refresh_customers)
        top_layout.addWidget(self.txt_search, stretch=1)

        btn_excel = AnimatedButton("📊 Export Excel", top_card, variant="secondary")
        btn_excel.setFixedHeight(36)
        btn_excel.clicked.connect(self._export_excel)
        top_layout.addWidget(btn_excel)

        btn_add = AnimatedButton("+ Add Customer", top_card, variant="primary")
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
        while self.right_layout.count():
            item = self.right_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        lbl_empty = QLabel("👈 Select any customer to view account balance, notes, and purchase history.", self.right_card)
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
                bal_item.setForeground(Qt.GlobalColor.darkRed)
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
        while self.right_layout.count():
            item = self.right_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Customer Header Profile
        lbl_name = QLabel(customer.get("name", ""), self.right_card)
        lbl_name.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLORS['text_primary']};")
        self.right_layout.addWidget(lbl_name)

        info_box = QFrame(self.right_card)
        info_box.setStyleSheet(f"background-color: {COLORS['bg_input']}; border: 1px solid {COLORS['border']}; border-radius: 8px; padding: 10px;")
        inf_l = QVBoxLayout(info_box)
        inf_l.setSpacing(4)

        inf_l.addWidget(QLabel(f"📞 Phone: {customer.get('phone') or 'Not provided'}"))
        inf_l.addWidget(QLabel(f"✉️ Email: {customer.get('email') or 'Not provided'}"))
        inf_l.addWidget(QLabel(f"📍 Address: {customer.get('address') or 'Not provided'}"))

        bal = customer.get("balance", 0.0)
        lbl_bal = QLabel(f"💳 Khata / Credit Due: {self.currency} {bal:,.2f}")
        lbl_bal.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {'#DC2626' if bal > 0 else '#059669'};")
        inf_l.addWidget(lbl_bal)

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
