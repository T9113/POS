"""
PySide6 Dashboard View for OnesDev POS.
Visual KPI cards, store overview, quick action buttons, and recent orders.
"""
from datetime import datetime
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtGui import QColor

from pos_app.qt_theme import COLORS, AnimatedButton, DropShadowCard, order_status_display
from pos_app.models.order_model import OrderModel
from pos_app.models.product_model import ProductModel
from pos_app.models.expense_model import ExpenseModel
from pos_app.models.settings_model import SettingsModel
from pos_app.controllers.auth_controller import AuthController
from pos_app.utils.icon_helper import get_icon


class QtDashboardView(QWidget):
    """Modern Dashboard overview with KPI metric cards and transactions."""
    navigate_to = Signal(str)
    navigate_requested = navigate_to

    def __init__(self, parent=None):
        super().__init__(parent)
        self.currency = SettingsModel.get("currency_symbol", "Rs")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # 1. Greeting Banner
        greeting_card = DropShadowCard(self, corner_radius=12, blur_radius=16, offset_y=3, opacity=20)
        greet_layout = QHBoxLayout(greeting_card)
        greet_layout.setContentsMargins(20, 16, 20, 16)

        left_greet = QVBoxLayout()
        user = AuthController.get_current_user()
        user_name = user["full_name"] if user else "Cashier"
        hour = datetime.now().hour
        greeting = "Good Morning" if hour < 12 else ("Good Afternoon" if hour < 18 else "Good Evening")

        lbl_greeting = QLabel(f"{greeting}, {user_name}", greeting_card)
        lbl_greeting.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLORS['text_primary']};")
        left_greet.addWidget(lbl_greeting)

        today_str = datetime.now().strftime("%A, %d %B %Y")
        lbl_sub = QLabel(f"Today is {today_str}  •  Store Active & Ready", greeting_card)
        lbl_sub.setStyleSheet(f"font-size: 13px; color: {COLORS['text_secondary']};")
        left_greet.addWidget(lbl_sub)
        greet_layout.addLayout(left_greet)

        greet_layout.addStretch()

        # Quick Actions
        btn_new_sale = AnimatedButton(" New Sale (F1)", greeting_card, variant="primary", icon_name="cart", icon_size=15)
        btn_new_sale.setFixedHeight(42)
        btn_new_sale.clicked.connect(lambda: self.navigate_to.emit("pos"))
        greet_layout.addWidget(btn_new_sale)

        if AuthController.is_admin():
            btn_add_prod = AnimatedButton(" Add Product", greeting_card, variant="secondary", icon_name="plus", icon_size=14)
            btn_add_prod.setFixedHeight(42)
            btn_add_prod.setToolTip("Go to Products Catalog")
            btn_add_prod.clicked.connect(lambda: self.navigate_to.emit("products"))
            greet_layout.addWidget(btn_add_prod)

        btn_eod = AnimatedButton(" Close Day", greeting_card, variant="secondary", icon_name="sunset", icon_size=14)
        btn_eod.setFixedHeight(42)
        btn_eod.setToolTip("End of Day Cash Reconciliation")
        btn_eod.clicked.connect(self._open_eod_dialog)
        greet_layout.addWidget(btn_eod)

        layout.addWidget(greeting_card)

        # 2. KPI Metrics Grid (4 Cards)
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(14)

        self.card_sales = self._create_kpi_card("TODAY'S SALES", f"{self.currency} 0.00", "0 completed orders", COLORS["primary"])
        kpi_layout.addWidget(self.card_sales)

        self.card_orders = self._create_kpi_card("TOTAL ORDERS", "0 Orders", "Average order value: Rs 0.00", COLORS["text_primary"])
        kpi_layout.addWidget(self.card_orders)

        self.card_profit = self._create_kpi_card("NET PROFIT", f"{self.currency} 0.00", "Gross profit minus expenses", COLORS["success"])
        kpi_layout.addWidget(self.card_profit)

        self.card_low_stock = self._create_kpi_card("LOW STOCK ALERTS", "0 Items", "Products at or below min stock", COLORS["danger"])
        kpi_layout.addWidget(self.card_low_stock)

        layout.addLayout(kpi_layout)

        # 3. Recent Transactions Section
        lbl_recent = QLabel("Recent Transactions", self)
        lbl_recent.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {COLORS['text_primary']}; margin-top: 6px;")
        layout.addWidget(lbl_recent)

        self.table = QTableWidget(self)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Order #", "Customer", "Time", "Payment Mode", "Status", "Total Amount"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

    def _create_kpi_card(self, title: str, val: str, sub: str, color: str) -> QFrame:
        card = DropShadowCard(self, corner_radius=10, blur_radius=14, offset_y=3, opacity=20)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 14, 18, 14)
        card_layout.setSpacing(4)

        lbl_t = QLabel(title, card)
        lbl_t.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {COLORS['text_secondary']}; letter-spacing: 0.5px;")
        card_layout.addWidget(lbl_t)

        lbl_v = QLabel(val, card)
        lbl_v.setObjectName("val")
        lbl_v.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {color}; font-family: Consolas, monospace;")
        card_layout.addWidget(lbl_v)

        lbl_s = QLabel(sub, card)
        lbl_s.setObjectName("sub")
        lbl_s.setStyleSheet(f"font-size: 11px; color: {COLORS['text_muted']};")
        card_layout.addWidget(lbl_s)

        return card

    def _open_eod_dialog(self):
        from pos_app.views.dialogs.qt_eod_dialog import QtEODDialog
        top_window = self.window()
        self.dlg_eod = QtEODDialog(top_window)
        self.dlg_eod.show_animated()

    def refresh_data(self):
        """Reloads metrics and table from database."""
        self.currency = SettingsModel.get("currency_symbol", "Rs")
        today = datetime.now().strftime("%Y-%m-%d")
        metrics = OrderModel.get_today_metrics()
        total_sales = metrics["total_sales"]
        order_count = metrics["total_orders"]
        avg_order = metrics["avg_order_value"]

        gross_profit = metrics["gross_profit"]
        expenses = ExpenseModel.get_total_for_range(today, today)
        net_profit = gross_profit - expenses

        # Low stock
        low_stock_items = ProductModel.get_low_stock_products()
        low_count = len(low_stock_items)

        # Update KPI Cards
        self.card_sales.findChild(QLabel, "val").setText(f"{self.currency} {total_sales:,.2f}")
        sales_sub = f"{order_count} order{'s' if order_count != 1 else ''} today"
        if metrics["total_refunds"]:
            sales_sub += f" • {self.currency} {metrics['total_refunds']:,.2f} refunded"
        self.card_sales.findChild(QLabel, "sub").setText(sales_sub)

        self.card_orders.findChild(QLabel, "val").setText(f"{order_count} Order{'s' if order_count != 1 else ''}")
        self.card_orders.findChild(QLabel, "sub").setText(f"Average: {self.currency} {avg_order:,.2f}")

        self.card_profit.findChild(QLabel, "val").setText(f"{self.currency} {net_profit:,.2f}")
        self.card_profit.findChild(QLabel, "sub").setText(f"Gross: {self.currency} {gross_profit:,.2f} • Exp: {self.currency} {expenses:,.2f}")

        self.card_low_stock.findChild(QLabel, "val").setText(f"{low_count} Item{'s' if low_count != 1 else ''}")
        self.card_low_stock.findChild(QLabel, "sub").setText("Action required" if low_count > 0 else "All stock healthy")

        # Load Recent Orders (top 20)
        recent = OrderModel.get_recent_orders(limit=20)
        self.table.setRowCount(len(recent))
        for row, o in enumerate(recent):
            item_num = QTableWidgetItem(o.get("order_number", ""))
            item_num.setFlags(item_num.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, item_num)

            cust_name = o.get("customer_name") or "Walk-in Customer"
            item_cust = QTableWidgetItem(cust_name)
            item_cust.setFlags(item_cust.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, item_cust)

            time_str = o.get("created_at", "")[-8:]
            item_time = QTableWidgetItem(time_str)
            item_time.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_time.setFlags(item_time.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, item_time)

            pay_method = (o.get("payment_method") or "cash").upper()
            item_pay = QTableWidgetItem(pay_method)
            item_pay.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_pay.setFlags(item_pay.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 3, item_pay)

            status_label, status_color = order_status_display(o.get("status"))
            item_status = QTableWidgetItem(status_label)
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_status.setForeground(QColor(status_color))
            item_status.setFlags(item_status.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 4, item_status)

            tot = o.get("total", 0.0)
            item_tot = QTableWidgetItem(f"{self.currency} {tot:,.2f}")
            item_tot.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item_tot.setFlags(item_tot.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 5, item_tot)
